"""
Step 1: download posts from Tumblr.

Run it from the project root:

    python -m src.collect

You need a free Tumblr API key (register an app at tumblr.com/oauth/apps).
Put the key in a file called .env, like this:

    TUMBLR_API_KEY=your_key_here

Do not paste the key into the code. Anyone who can see the code could use it.
"""
import html
import json
import os
import re
import time

import pandas as pd

from src import config


def make_client():
    """Create the Tumblr client using the key from the .env file."""
    # These imports live here so the rest of the file can be tested
    # without having pytumblr installed.
    import pytumblr
    from dotenv import load_dotenv

    load_dotenv()
    key = os.environ.get("TUMBLR_API_KEY")
    if not key:
        raise SystemExit(
            "No TUMBLR_API_KEY found. Copy .env.example to .env and add your key."
        )
    return pytumblr.TumblrRestClient(key)


def strip_html(raw):
    """Turn the HTML that Tumblr sends into plain text."""
    without_tags = re.sub(r"<[^>]+>", " ", raw or "")
    # Tumblr sends things like &hellip; and &rsquo;. unescape turns them back into real characters.
    plain = html.unescape(without_tags)
    return re.sub(r"\s+", " ", plain).strip()


def get_text(post):
    """Pick the right field for the text, because each post type stores it somewhere different."""
    kind = post.get("type", "")
    if kind == "text":
        raw = (post.get("title") or "") + " " + (post.get("body") or "")
    elif kind == "quote":
        raw = post.get("text", "")
    elif kind == "chat":
        raw = post.get("body", "")
    else:
        # photos, videos and answers keep their words in the caption (or the answer)
        raw = post.get("caption") or post.get("answer") or ""
    return strip_html(raw)


def looks_like_reblog(post):
    """
    Return 1 if the post is a reblog of someone else's post, otherwise 0.

    Tumblr now sends a "trail": the chain of posts this post is built on.
    An original post has a trail with one item, and that item is the post itself.
    A reblog has an item that is the root of the chain but is not this post.
    We also check the older reblog fields as a backup.
    """
    trail = post.get("trail") or []
    for item in trail:
        # Some trail items are not dictionaries. We skip those instead of crashing.
        if isinstance(item, dict) and item.get("is_root_item") and not item.get("is_current_item"):
            return 1
    if len(trail) > 1:
        return 1
    old_fields = ("reblogged_from_id", "reblogged_from_name", "reblogged_root_id", "reblogged_root_name")
    return int(any(post.get(field) for field in old_fields))


def get_comment_text(post):
    """What the poster added themselves, without the posts underneath it."""
    reblog = post.get("reblog")
    comment = reblog.get("comment") if isinstance(reblog, dict) else ""
    return strip_html(comment or "")


def has_image(post):
    """1 if the post shows a picture. New-style posts keep pictures in the body, so type alone is not enough."""
    if post.get("type") == "photo":
        return 1
    html_text = (post.get("body") or "") + (post.get("caption") or "")
    return int("<img" in html_text or "<figure" in html_text)


def to_row(post, source):
    """Keep only the fields we need from one post."""
    return {
        "source": source,                       # which blog or tag search it came from
        "post_id": post.get("id"),
        "blog_name": post.get("blog_name"),     # the blog that actually owns the post
        "text": get_text(post),
        "comment_text": get_comment_text(post),
        "note_count": post.get("note_count", 0),
        "timestamp": post.get("timestamp"),     # seconds since 1970, in UTC
        "tags": json.dumps(post.get("tags", [])),
        "post_type": post.get("type", ""),
        "has_image": has_image(post),
        "is_reblog": looks_like_reblog(post),
    }


def rows_from(posts, source):
    """
    Turn a page of posts into rows.

    If one post has an odd shape we skip it and say so. Before, a single odd
    post stopped the download for the whole tag, and we lost most of its posts.
    """
    rows, skipped, first_error = [], 0, None
    for post in posts:
        try:
            rows.append(to_row(post, source))
        except Exception as error:
            skipped += 1
            first_error = first_error or error
    if skipped:
        print(f"  {source}: skipped {skipped} posts that could not be read ({first_error!r})")
    return rows


def collect_blog(client, blog):
    """Download the newest posts from one blog, 20 at a time."""
    rows = []
    try:
        for offset in range(0, config.POSTS_PER_BLOG, config.PAGE_SIZE):
            response = client.posts(blog, limit=config.PAGE_SIZE, offset=offset)
            posts = response.get("posts") if isinstance(response, dict) else None
            if not posts:
                # When Tumblr refuses, the reason is in "meta". Show it so we are not guessing.
                reason = response.get("meta") if isinstance(response, dict) else response
                print(f"  {blog}: no posts at offset {offset}. Tumblr said: {reason}")
                break
            rows += rows_from(posts, blog)
            time.sleep(config.PAUSE_SECONDS)
    except Exception as error:  # a network problem should not throw away the other blogs
        print(f"  {blog}: stopped early because of an error: {error}")
    return rows


def collect_tag(client, tag):
    """
    Download posts that use one tag.

    The tag search walks backwards in time. We start MIN_POST_AGE_DAYS ago so
    that we never pick up posts that are too new to have collected notes.
    """
    rows = []
    before = int(time.time()) - config.MIN_POST_AGE_DAYS * 86400
    try:
        while len(rows) < config.POSTS_PER_TAG:
            posts = client.tagged(tag, before=before, limit=config.PAGE_SIZE)
            if isinstance(posts, dict):
                # When something goes wrong Tumblr sends a message (a dictionary) instead of a list of posts.
                print(f"  #{tag}: Tumblr sent a message instead of posts: {posts.get('meta', posts)}")
                break
            if not posts:
                break
            rows += rows_from(posts, f"tag:{tag}")
            last_time = posts[-1].get("timestamp") if isinstance(posts[-1], dict) else None
            # If the time did not move back, stop. Otherwise we would ask for the same page forever.
            if last_time is None or last_time >= before:
                break
            before = last_time
            time.sleep(config.PAUSE_SECONDS)
    except Exception as error:
        print(f"  #{tag}: stopped early because of an error: {error}")
    return rows


def main():
    """Download everything and save it.
    1. Connect to Tumblr with the key from the .env file.
    2. Download posts from each blog, then from each tag search.
    3. Remove duplicates and mark when we downloaded them.
    4. Print how many posts came from each source, and warn if something looks wrong.
    5. Save the posts to the raw CSV file.
    """
    client = make_client()
    rows = []

    for blog in config.BLOGS:
        print(f"Blog: {blog}")
        rows += collect_blog(client, blog)

    for tag in config.TAGS:
        print(f"Tag: #{tag}")
        rows += collect_tag(client, tag)

    if not rows:
        raise SystemExit("Nothing was downloaded. Check your API key and internet connection.")

    posts = pd.DataFrame(rows).drop_duplicates(subset="post_id")
    # We remember when we scraped, so "how old is this post" is always measured from the same day.
    posts["scraped_at"] = int(time.time())

    print("\nPosts per source:")
    counts = posts["source"].value_counts()
    print(counts.to_string())
    for name in config.BLOGS:
        if name not in counts.index:
            print(f"WARNING: {name} gave no posts. Check the blog name in a browser.")
    if posts["is_reblog"].nunique() == 1:
        print("WARNING: is_reblog is the same for every post, so it will not help the model.")
    print(f"\nDifferent blogs in the data: {posts['blog_name'].nunique()}")
    print(f"Share of posts that are reblogs: {posts['is_reblog'].mean():.0%}")
    print(f"Share of posts with an image:    {posts['has_image'].mean():.0%}")

    config.DATA_DIR.mkdir(exist_ok=True)
    posts.to_csv(config.RAW_FILE, index=False)
    print(f"\nSaved {len(posts)} posts to {config.RAW_FILE}")


if __name__ == "__main__":
    main()
