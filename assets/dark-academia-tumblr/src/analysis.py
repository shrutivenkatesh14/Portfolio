"""
Step 4 (optional): look at the data and save some charts.

Run it from the project root:

    python -m src.analysis

Every table shows how many posts are behind each number ("posts"), and how many
different blogs they come from ("blogs"). A median that comes from 6 posts
from one blog should not be trusted as much as one from 200 posts from 100 blogs.
We also repeat each table for the biggest single source (one tag search). If a
pattern shows up in every source it is more believable than one that only shows
up when they are mixed together.
"""
import matplotlib

matplotlib.use("Agg")  # draw straight to image files, so no window is needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import config

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ---- Small helpers that put each post into a group ---------------------------

def tag_group(count):
    """Put a post into a group by how many tags it has."""
    if count == 0:
        return "0 tags"
    if count <= 3:
        return "1-3 tags"
    if count <= 7:
        return "4-7 tags"
    if count <= 12:
        return "8-12 tags"
    return "13+ tags"


def time_of_day(hour):
    """Put a post into a part of the day (UTC) by the hour it was posted."""
    if 5 <= hour < 12:
        return "Morning (5-11)"
    if 12 <= hour < 17:
        return "Afternoon (12-16)"
    if 17 <= hour < 21:
        return "Evening (17-20)"
    return "Night (21-4)"


def length_group(words):
    """Put a post into a group by how many words it has."""
    if words == 0:
        return "No text"
    if words < 50:
        return "1-49 words"
    if words < 150:
        return "50-149 words"
    return "150+ words"


def load_posts():
    """Read the features file and add the group columns used in the tables."""
    df = pd.read_csv(config.FEATURES_FILE)
    when = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df["year"] = when.dt.year
    df["weekday"] = when.dt.day_name()
    df["tag_group"] = df["tag_count"].apply(tag_group)
    df["time_of_day"] = df["hour"].apply(time_of_day)
    df["length_group"] = df["word_count"].apply(length_group)
    df["asks_question"] = np.where(df["has_question"] == 1, "Has a question", "No question")
    return df


def summarise(df, column, order=None):
    """Posts, number of blogs and median notes for each value of one column."""
    table = df.groupby(column).agg(
        posts=("note_count", "size"),
        blogs=("blog", "nunique"),
        median_notes=("note_count", "median"),
    )
    if order:
        table = table.reindex([name for name in order if name in table.index])
    return table


# ---- Charts ------------------------------------------------------------------

def label_bars(ax, bars, counts):
    """Write the number of posts above each bar."""
    ax.bar_label(bars, labels=[f"n={n}" for n in counts], fontsize=8, padding=2)


def plot_distribution(df):
    """Chart 1: how lopsided the note counts are."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4))

    # For the left chart we cut the axis at the 99th percentile, otherwise one
    # post with a million notes squashes everything else into a single bar.
    cutoff = df["note_count"].quantile(0.99)
    left.hist(df["note_count"].clip(upper=cutoff), bins=40, color="#6b4f3a", edgecolor="white")
    left.set_title("Notes per post (cut at the 99th percentile)")
    left.set_xlabel("Notes")
    left.set_ylabel("Posts")

    right.hist(df["log_notes"], bins=40, color="#8a6d3b", edgecolor="white")
    right.set_title("Same data after log(notes + 1)")
    right.set_xlabel("log(notes + 1)")

    fig.tight_layout()
    fig.savefig(config.FIGURE_DIR / "01_note_distribution.png", dpi=150)
    plt.close(fig)


def plot_source_and_year(df):
    """
    Chart 2: notes by source and by the year the post was made.

    This is the most important chart in the project. Old posts have had years to
    pick up notes, and different sources cover different years. So "which source"
    and "which year" are tangled up with "which post did well".
    """
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.5))

    by_source = summarise(df, "source").sort_values("median_notes", ascending=False)
    bars = left.bar(by_source.index, by_source["median_notes"], color="#6b4f3a")
    label_bars(left, bars, by_source["posts"])
    left.set_title("Median notes by source")
    left.set_ylabel("Median notes")
    left.tick_params(axis="x", rotation=20)

    by_year = summarise(df, "year")
    bars = right.bar(by_year.index.astype(str), by_year["median_notes"], color="#8a6d3b")
    label_bars(right, bars, by_year["posts"])
    right.set_title("Median notes by year the post was made")

    fig.tight_layout()
    fig.savefig(config.FIGURE_DIR / "02_source_and_year.png", dpi=150)
    plt.close(fig)


def plot_group_medians(tables):
    """Chart 3: median notes for each of the things a creator can choose."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, (title, table) in zip(axes.flatten(), tables.items()):
        bars = ax.bar(table.index, table["median_notes"], color="#6b4f3a")
        label_bars(ax, bars, table["posts"])
        ax.set_title(title)
        ax.set_ylabel("Median notes")
        ax.tick_params(axis="x", rotation=30)
    fig.suptitle("Median notes by post choices (all tag searches together)")
    fig.tight_layout()
    fig.savefig(config.FIGURE_DIR / "03_group_medians.png", dpi=150)
    plt.close(fig)


def main():
    """Run the whole exploration:
    1. Load the posts and print how uneven the note counts are.
    2. Print a table for each thing a creator can choose (tags, day, time, type, question, length).
    3. Print the same tables again for the biggest source, to see if the pattern still holds.
    4. Save the tag table for the app, and save the charts.
    """
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    df = load_posts()

    print(f"{len(df)} posts. Note counts: median {df['note_count'].median():.0f}, "
          f"mean {df['note_count'].mean():.0f}, max {df['note_count'].max():.0f}\n")

    def build_tables(data):
        """Make one table for each choice a creator can make, from the posts we are given."""
        return {
            "Tags used": summarise(data, "tag_group",
                                   ["0 tags", "1-3 tags", "4-7 tags", "8-12 tags", "13+ tags"]),
            "Day of the week": summarise(data, "weekday", WEEKDAYS),
            "Time of day (UTC)": summarise(data, "time_of_day",
                                           ["Morning (5-11)", "Afternoon (12-16)",
                                            "Evening (17-20)", "Night (21-4)"]),
            "Post type": summarise(data, "post_type"),
            "Question in the text": summarise(data, "asks_question"),
            "Length of the text": summarise(data, "length_group",
                                            ["No text", "1-49 words", "50-149 words", "150+ words"]),
        }

    all_tables = build_tables(df)
    for title, table in all_tables.items():
        print(f"--- {title} (all posts) ---")
        print(table.to_string(), "\n")

    # Same tables again, but only for the biggest source.
    biggest = df["source"].value_counts().idxmax()
    print(f"=== Same tables, only posts from '{biggest}' ===\n")
    for title, table in build_tables(df[df["source"] == biggest]).items():
        print(f"--- {title} ({biggest} only) ---")
        print(table.to_string(), "\n")

    # The app shows this table on its "What the data shows" tab.
    tag_table = all_tables["Tags used"].reset_index()
    tag_table.columns = ["Tags on the post", "Posts", "Blogs", "Median notes"]
    tag_table.to_csv(config.TAG_GROUPS_FILE, index=False)

    plot_distribution(df)
    plot_source_and_year(df)
    plot_group_medians(all_tables)
    print(f"Charts saved in {config.FIGURE_DIR}")


if __name__ == "__main__":
    main()
