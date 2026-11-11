"""
Scoring a draft post with the saved model.

The app (app.py) only handles the screen. Everything that decides what the
numbers are lives here, so it can be tested without opening the app.
"""
from dataclasses import dataclass, field, replace

import joblib
import numpy as np
import pandas as pd

from src import config
from src.features import build_feature_row, tag_column_name, text_features

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# We only mention a change if the model expects at least 15 percent more notes.
# Smaller differences are well inside the noise of this model.
MIN_GAIN = 0.15

# Used only if the saved model does not say which tag counts are safe to suggest.
DEFAULT_TAG_COUNT_RANGE = (1, 15)


@dataclass
class Draft:
    """Everything we know about a post that has not been published yet."""
    text: str
    tags: list = field(default_factory=list)
    post_type: str = "text"
    hour: int = 20            # hour of the day in UTC
    day_of_week: int = 4      # 0 is Monday
    has_image: bool = False
    # How many notes the creator's posts usually get. None means "not given".
    typical_notes: float = None


def load_bundle(path=config.MODEL_FILE):
    """Load the saved model and the details that go with it."""
    return joblib.load(path)


def predict_notes(bundle, draft, tag_count=None):
    """
    Predict the number of notes for one draft.

    The model works on log(notes + 1), so we turn the answer back into notes.
    This gives a "typical" result for a post like this. It is closer to the
    median than to the average, because a few viral posts do not pull it up.

    tag_count lets us ask "what if this post had a different number of tags?"
    without changing which tags it has.
    """
    if tag_count is None:
        tag_count = len(draft.tags)
    # The model works on the log scale. If we were not told the usual notes, we use
    # the middle value of the posts the model learned from.
    if draft.typical_notes is None:
        typical_log = bundle.get("default_typical_log", 0.0)
    else:
        typical_log = float(np.log1p(max(draft.typical_notes, 0)))
    row = build_feature_row(
        draft.text, tag_count, draft.post_type, draft.hour, draft.day_of_week,
        tags=draft.tags, tag_vocab=bundle.get("tag_vocab", []),
        has_image=draft.has_image,
        blog_typical_log_notes=typical_log,
    )
    frame = pd.DataFrame([row])[bundle["feature_columns"]]
    log_prediction = float(bundle["model"].predict(frame)[0])
    # The range comes from how wrong the model was on blogs it had not seen (see train.py).
    error_low, error_high = bundle.get("error_range", (0.0, 0.0))
    return {
        "log_prediction": log_prediction,
        "notes": float(np.expm1(log_prediction)),
        "low": float(np.expm1(max(log_prediction + error_low, 0.0))),
        "high": float(np.expm1(max(log_prediction + error_high, 0.0))),
        # Share of the posts we trained on that got fewer notes than this prediction.
        "percentile": float((bundle["train_log_notes"] < log_prediction).mean() * 100),
    }


def draft_check(bundle, draft):
    """
    Plain facts about the draft, next to the middle value for the niche.

    This only describes the draft. It does not say what is better.
    """
    medians = bundle.get("niche_medians", {})
    readability = text_features(draft.text)["readability"]
    return [
        ("Words", len(draft.text.split()), medians.get("word_count")),
        ("Tags", len(draft.tags), medians.get("tag_count")),
        ("Reading ease (0 to 100, higher is easier)", readability, medians.get("readability")),
    ]


def suggest_changes(bundle, draft):
    """
    Try one change at a time and report the ones the model likes.

    We change only the things a creator can pick freely: the hour, the day, the
    number of tags and which popular tags are used. We do not rewrite the text,
    because the model cannot tell us what a better sentence would be.

    We also skip any column that the model hardly uses (see "trusted_features"
    in train.py). Advice about a column the model ignores would just be noise.
    """
    trusted = bundle.get("trusted_features", [])
    current = predict_notes(bundle, draft)["notes"]
    options = []

    def try_values(values, make_prediction, describe):
        """Predict every value, keep the best one, and mention it if it clears MIN_GAIN."""
        # Predict every value, keep the best one, and mention it if it clears MIN_GAIN.
        best_value = max(values, key=make_prediction)
        best_notes = make_prediction(best_value)
        gain = best_notes / max(current, 1) - 1
        if gain >= MIN_GAIN:
            options.append((gain, describe(best_value, best_notes)))

    if "hour" in trusted:
        try_values(
            range(24),
            lambda h: predict_notes(bundle, replace(draft, hour=h))["notes"],
            lambda h, n: f"Post around {h}:00 UTC instead of {draft.hour}:00 UTC. "
                         f"The model expects about {n:.0f} notes instead of {current:.0f}.",
        )
    if "day_of_week" in trusted:
        try_values(
            range(7),
            lambda d: predict_notes(bundle, replace(draft, day_of_week=d))["notes"],
            lambda d, n: f"Post on {DAY_NAMES[d]} instead of {DAY_NAMES[draft.day_of_week]}. "
                         f"The model expects about {n:.0f} notes instead of {current:.0f}.",
        )
    if "tag_count" in trusted:
        low, high = bundle.get("tag_count_range", DEFAULT_TAG_COUNT_RANGE)
        try_values(
            range(max(low, 1), high + 1),
            lambda t: predict_notes(bundle, draft, tag_count=t)["notes"],
            lambda t, n: f"Use {t} tags instead of {len(draft.tags)}. "
                         f"The model expects about {n:.0f} notes instead of {current:.0f}.",
        )

    # Popular tags we could add. Only tags whose own column the model clearly relies on.
    addable = [tag for tag in bundle.get("tag_vocab", [])
               if tag_column_name(tag) in trusted and tag not in draft.tags]
    if addable:
        try_values(
            addable,
            lambda tag: predict_notes(bundle, replace(draft, tags=draft.tags + [tag]))["notes"],
            lambda tag, n: f"Add the tag #{tag}. "
                           f"The model expects about {n:.0f} notes instead of {current:.0f}.",
        )

    options.sort(reverse=True)  # biggest expected gain first
    return [message for _, message in options]


def popular_tags(used_tags, how_many=5, path=config.TAG_STATS_FILE):
    """
    Tags that many different blogs in the niche use, leaving out the ones already on the draft.

    This says what is common, not what works. Once each blog's usual notes were
    taken into account, no tag showed a clear difference in notes.
    """
    stats = pd.read_csv(path)
    used = {tag.lower().strip() for tag in used_tags}
    stats = stats[~stats["tag"].isin(used)]
    top = stats.head(how_many)
    return list(zip(top["tag"], top["blogs"], top["posts"]))
