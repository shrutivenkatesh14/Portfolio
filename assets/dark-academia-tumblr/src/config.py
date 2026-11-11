"""
Settings used by every script in this project.

If you want to change which blogs get scraped, how old a post has to be,
or where files are saved, change it here and nowhere else.
"""
from pathlib import Path

# ROOT is the top folder of the project (the one that holds README.md).
ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
FIGURE_DIR = REPORT_DIR / "figures"

RAW_FILE = DATA_DIR / "tumblr_posts_raw.csv"      # straight from the Tumblr API
FEATURES_FILE = DATA_DIR / "features.csv"         # numbers only, no post text
MODEL_FILE = MODEL_DIR / "engagement_model.joblib"
TAG_STATS_FILE = MODEL_DIR / "tag_stats.csv"
METRICS_FILE = REPORT_DIR / "metrics.json"
TAG_GROUPS_FILE = REPORT_DIR / "tag_groups.csv"   # median notes by number of tags, used by the app

# ---------------------------------------------------------------------------
# What to download
# ---------------------------------------------------------------------------
# These three blogs worked. Three others from our first list (the-dark-academia-aesthetic,
# classical-literature, the-scholars-library) came back "404 Not Found" and were removed.
BLOGS = ["academia-aesthetics", "darkcabin", "scholars-ink"]

# Most of the data comes from tag searches. Every post in a tag search comes from
# a different blog, which lets us test the model on blogs it has never seen.
TAGS = [
    "dark academia",
    "aesthetic academia",
    "classic literature",
    "dark academia aesthetic",
    "dark academia quotes",
]

POSTS_PER_BLOG = 250     # how many posts to try to get from each blog
POSTS_PER_TAG = 600      # how many posts to try to get from each tag search
PAGE_SIZE = 20           # Tumblr gives at most 20 posts per request
PAUSE_SECONDS = 0.5      # small wait between requests so we are polite to the API

# ---------------------------------------------------------------------------
# Cleaning rules
# ---------------------------------------------------------------------------
# A new post has not had time to collect notes yet, so its note count is low
# for the wrong reason. We only keep posts that are at least this many days old.
MIN_POST_AGE_DAYS = 30

# Which column holds the words of the post. "text" is the whole post as Tumblr sends it.
# "comment_text" is only what the poster added themselves. Switch to "comment_text"
# if reblogs carry a long chain of other people's comments in "text".
TEXT_COLUMN = "text"

# The three named blogs (BLOGS above) are very old, big accounts, and each one is a single
# blog. Their posts have had years to collect notes, so they are a different kind of post
# from the recent tag-search posts, and they cannot be used to test "blogs the model has
# not seen" because each one is only one blog. By default they are left out of the model.
# Set this to True to include them.
INCLUDE_NAMED_BLOGS = False

# Keep only posts with at least this many tags. 0 keeps everything.
# Be careful: in our data almost every untagged post came from two blogs, so "no tags"
# mostly told the model which blog a post came from.
MIN_TAGS = 0

# ---------------------------------------------------------------------------
# Modelling
# ---------------------------------------------------------------------------
RANDOM_SEED = 42                  # same seed every run, so results can be repeated
TEST_SIZE = 0.2                   # 20 percent of posts are kept aside for testing
CV_FOLDS = 5                      # how many parts to split the data into for cross-validation
BLOG_FOLDS = 5                    # parts for the "unseen blogs" test (each blog is in one part only)
MIN_TAG_POSTS = 10                # a tag needs this many posts before we rank it
MIN_TAG_BLOGS = 5                 # ...and this many different blogs using it

# How many of the most common tags get their own yes/no column ("does this post use #vintage?").
# The tags we searched for (TAGS above) are never used, because every post from that
# search has the tag. 0 turns this off. train.py only keeps these columns if they
# help on sources the model has not seen.
TAG_FEATURE_COUNT = 10
