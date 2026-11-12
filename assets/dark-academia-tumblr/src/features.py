"""
Step 2: clean the raw posts and turn each one into a row of numbers.

Run it from the project root:

    python -m src.features

The same build_feature_row() function is used when you score a draft in the
app. That is on purpose. If training and the app built their numbers in
different ways, the model would be fed something it never learned from.
"""
import ast
import json
from collections import Counter

import numpy as np
import pandas as pd
import textstat
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src import config

# VADER is a ready-made tool that scores how positive or negative a text is.
_sentiment = SentimentIntensityAnalyzer()

# These are the columns the model sees, in a fixed order.
# Post type is stored as two yes/no columns. "text" is the default, so it needs no column.
FEATURE_COLUMNS = [
    "word_count",
    "avg_word_len",
    "unique_word_ratio",     # share of words that are different (low means a lot of repeating)
    "readability",           # Flesch score: higher means easier to read
    "sentiment_compound",    # -1 is very negative, +1 is very positive
    "sentiment_pos",
    "sentiment_neg",
    "has_question",
    "has_exclamation",
    "has_caption",           # 0 when the post has no words at all (many image posts)
    "has_image",             # 1 if the post shows a picture
    "blog_typical_log_notes",  # how many notes this blog's other posts usually get (log scale)
    "tag_count",
    "hour",                  # hour of the day in UTC, 0 to 23
    "day_of_week",           # 0 is Monday, 6 is Sunday
    "type_photo",
    "type_other",            # quote, answer, chat and anything that is not text or photo
]


# Each popular tag can get its own column, named has_tag_ plus the tag.
TAG_COLUMN_PREFIX = "has_tag_"


def tag_column_name(tag):
    """The name of the yes/no column for one tag, like has_tag_vintage."""
    return TAG_COLUMN_PREFIX + tag


def tag_vocab_from_columns(columns):
    """Read the list of tags back out of a list of column names."""
    return [name[len(TAG_COLUMN_PREFIX):] for name in columns if name.startswith(TAG_COLUMN_PREFIX)]


def pick_tag_vocab(tag_lists):
    """
    The most common tags, which will get their own column.

    We pick by how often a tag is used, never by how many notes it got, so that
    the choice does not peek at the answer. The tags we searched for are left out,
    since every post found through that search carries the tag by design.
    """
    counts = Counter(tag for tags in tag_lists for tag in set(tags) if tag not in config.TAGS)
    return [tag for tag, _ in counts.most_common(config.TAG_FEATURE_COUNT)]


def parse_tags(value):
    """
    Turn the tags column into a clean list of lowercase tags.

    The tags can be stored as JSON (what collect.py writes) or as a Python list
    written out as text, like "['a', 'b']". We accept both.
    """
    if isinstance(value, list):
        tags = value
    elif isinstance(value, str) and value.strip():
        try:
            tags = json.loads(value)
        except ValueError:
            try:
                tags = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                tags = []
    else:
        tags = []  # empty cell or NaN
    return [str(tag).lower().strip() for tag in tags if str(tag).strip()]


def text_features(text):
    """Numbers that describe the words of a post."""
    text = text if isinstance(text, str) else ""
    words = text.split()

    # Many photo posts have no caption. We cannot score words that are not there,
    # so we use zeros and let has_caption say "there was nothing to read".
    if not words:
        return {
            "word_count": 0, "avg_word_len": 0.0, "unique_word_ratio": 0.0,
            "readability": 0.0, "sentiment_compound": 0.0, "sentiment_pos": 0.0,
            "sentiment_neg": 0.0, "has_question": 0, "has_exclamation": 0,
            "has_caption": 0,
        }

    scores = _sentiment.polarity_scores(text)
    # Flesch scores are meant to sit between 0 and 100. Very short or odd text can land far outside,
    # so we clip the value to keep a few strange posts from pulling the model around.
    readability = float(np.clip(textstat.flesch_reading_ease(text), 0, 100))

    return {
        "word_count": len(words),
        "avg_word_len": float(np.mean([len(word) for word in words])),
        "unique_word_ratio": len({word.lower() for word in words}) / len(words),
        "readability": readability,
        "sentiment_compound": scores["compound"],
        "sentiment_pos": scores["pos"],
        "sentiment_neg": scores["neg"],
        "has_question": int("?" in text),
        "has_exclamation": int("!" in text),
        "has_caption": 1,
    }


def build_feature_row(text, tag_count, post_type, hour, day_of_week, tags=(), tag_vocab=(),
                      has_image=0, blog_typical_log_notes=0.0):
    """
    All the numbers for one post. Used for training and for the app.

    tags and tag_vocab are only needed for the has_tag_ columns. tag_count is its
    own argument so the app can ask "what if this post had 6 tags?".
    """
    row = text_features(text)
    row["tag_count"] = tag_count
    row["hour"] = hour
    row["day_of_week"] = day_of_week
    row["type_photo"] = int(post_type == "photo")
    row["type_other"] = int(post_type not in ("text", "photo"))
    row["has_image"] = int(bool(has_image))
    row["blog_typical_log_notes"] = float(blog_typical_log_notes)
    for tag in tag_vocab:
        row[tag_column_name(tag)] = int(tag in tags)
    return row


def blog_history(blogs, log_notes):
    """
    For each post: the average log(notes + 1) of the OTHER posts from the same blog.

    How a blog usually does is the biggest thing that decides a post's notes
    (a big blog gets more notes whatever it posts). A creator knows how their own
    posts usually do, so the app asks for it. The post itself is never counted,
    so it cannot give away its own answer. A blog with only one post in our data
    gets the average of all other posts instead. The second thing we return is how
    many other posts from the blog the average is based on.
    """
    total = log_notes.groupby(blogs).transform("sum")
    count = log_notes.groupby(blogs).transform("count")
    peers = count - 1
    others_average = (total - log_notes) / peers.where(peers > 0)
    everyone_else = (log_notes.sum() - log_notes) / (len(log_notes) - 1)
    return others_average.fillna(everyone_else), peers


def clean_raw(raw):
    """
    Remove posts we should not train on.

    It prints how many posts are left after each step, so you can see
    what the rules cost you.
    """
    df = raw.copy()

    # Some older files call this column "blog" instead of "source".
    if "source" not in df.columns and "blog" in df.columns:
        df = df.rename(columns={"blog": "source"})

    # Older files have no blog_name, image or reblog columns. Fill them in the best way we can.
    if "blog_name" not in df.columns:
        df["blog_name"] = df["source"]
    df["blog_name"] = df["blog_name"].fillna(df["source"])
    if "has_image" not in df.columns:
        df["has_image"] = (df["post_type"] == "photo").astype(int)
    if "is_reblog" not in df.columns:
        df["is_reblog"] = 0
    text_column = config.TEXT_COLUMN if config.TEXT_COLUMN in df.columns else "text"
    df["text"] = df[text_column]

    print(f"Posts in the raw file:          {len(df)}")

    df = df.drop_duplicates(subset="post_id")
    df = df.dropna(subset=["note_count", "timestamp"])
    print(f"After removing duplicates:      {len(df)}")

    if not config.INCLUDE_NAMED_BLOGS:
        df = df[df["source"].str.startswith("tag:")]
        print(f"After keeping tag searches only: {len(df)}")

    # Work out how old each post was on the day we scraped.
    # If the file has no scrape date, the newest post is the best guess.
    if "scraped_at" in df.columns and df["scraped_at"].notna().any():
        reference_time = df["scraped_at"].max()
    else:
        reference_time = df["timestamp"].max()
    df["age_days"] = (reference_time - df["timestamp"]) / 86400

    df = df[df["age_days"] >= config.MIN_POST_AGE_DAYS]
    print(f"After dropping posts under {config.MIN_POST_AGE_DAYS} days old: {len(df)}")

    df["tags"] = df["tags"].apply(parse_tags)
    df = df[df["tags"].apply(len) >= config.MIN_TAGS]
    print(f"After requiring {config.MIN_TAGS}+ tags:          {len(df)}")

    # We do NOT remove posts with a huge number of notes. Those viral posts are
    # exactly what this project is about. The log step below handles them instead.
    return df.reset_index(drop=True)


def build_features(clean):
    """Make one row of numbers per post, plus the columns we need later."""
    timestamps = pd.to_datetime(clean["timestamp"], unit="s", utc=True)

    # We save a blog number instead of the blog name. The model only needs to know
    # which posts share a blog, and this keeps other people's usernames out of the file.
    blog_ids = pd.factorize(clean["blog_name"])[0]
    blog_labels = pd.Series(["blog_" + str(number).zfill(4) for number in blog_ids], index=clean.index)
    log_notes = np.log1p(clean["note_count"])
    typical, peers = blog_history(blog_labels, log_notes)

    tag_vocab = pick_tag_vocab(clean["tags"])

    rows = []
    for text, tags, post_type, when, image, typical_log in zip(
        clean["text"], clean["tags"], clean["post_type"], timestamps,
        clean["has_image"], typical,
    ):
        rows.append(build_feature_row(text, len(tags), post_type, when.hour, when.dayofweek,
                                      tags=tags, tag_vocab=tag_vocab,
                                      has_image=image,
                                      blog_typical_log_notes=typical_log))
    numbers = pd.DataFrame(rows)[FEATURE_COLUMNS + [tag_column_name(t) for t in tag_vocab]]

    keep = pd.DataFrame({
        "post_id": clean["post_id"],
        "source": clean["source"],
        "blog": blog_labels,
        "blog_peers": peers,        # how many other posts from this blog are in the data
        "timestamp": clean["timestamp"],
        "post_type": clean["post_type"],
        "tags": clean["tags"].apply(json.dumps),
        "age_days": clean["age_days"].round(1),
        "note_count": clean["note_count"],
        # note counts are very lopsided (most posts get a few, a few get thousands).
        # log1p squashes that, so a handful of viral posts do not dominate the model.
        "log_notes": log_notes,
    })
    return pd.concat([keep, numbers], axis=1)


def main():
    """Read the raw posts, clean them, build the numbers and save them.
    The later steps (train, analysis) only read the file this step writes.
    """
    raw = pd.read_csv(config.RAW_FILE)
    clean = clean_raw(raw)
    features = build_features(clean)
    features.to_csv(config.FEATURES_FILE, index=False)
    print(f"\nSaved {len(features)} rows to {config.FEATURES_FILE}")


if __name__ == "__main__":
    main()
