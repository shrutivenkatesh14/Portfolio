"""
Tests for the parts of the project that are easy to get wrong.

Run them from the project root with:

    python -m pytest

None of these tests need internet or a Tumblr key. For the downloading code we
use a fake client that hands back made-up posts.
"""
import numpy as np
import pandas as pd

from src import collect, config
from src.features import (FEATURE_COLUMNS, blog_history, build_feature_row, clean_raw, parse_tags,
                          pick_tag_vocab, tag_column_name, text_features)
from src.predict import Draft, draft_check, predict_notes, suggest_changes
from src.train import average_gap
from src.usual_model import UsualNotesModel


# ---- features.py ------------------------------------------------------------

def test_parse_tags_reads_json_and_python_style_lists():
    assert parse_tags('["Dark Academia", "books"]') == ["dark academia", "books"]
    assert parse_tags("['Dark Academia', 'books']") == ["dark academia", "books"]


def test_parse_tags_handles_empty_and_missing_values():
    assert parse_tags("[]") == []
    assert parse_tags(float("nan")) == []
    assert parse_tags("not a list at all") == []


def test_empty_text_gives_zeros_and_no_caption_flag():
    for empty in ["", None, float("nan")]:
        row = text_features(empty)
        assert row["has_caption"] == 0
        assert row["word_count"] == 0
        assert row["sentiment_compound"] == 0.0


def test_text_features_spot_questions_and_repeats():
    row = text_features("Is this the real life? Is this just fantasy?")
    assert row["has_question"] == 1
    assert row["has_exclamation"] == 0
    assert row["word_count"] == 9
    # "is" and "this" appear twice, so there are fewer different words than words
    assert row["unique_word_ratio"] < 1.0


def test_feature_row_has_every_column_the_model_needs():
    row = build_feature_row("a short post", tag_count=3, post_type="photo", hour=20, day_of_week=4)
    assert set(FEATURE_COLUMNS) <= set(row)
    assert row["type_photo"] == 1 and row["type_other"] == 0
    assert row["has_image"] == 0
    with_image = build_feature_row("a post", 2, "text", 1, 1, has_image=True)
    assert with_image["has_image"] == 1
    other = build_feature_row("a quote", tag_count=0, post_type="quote", hour=1, day_of_week=0)
    assert other["type_photo"] == 0 and other["type_other"] == 1


def test_clean_raw_drops_young_posts_and_duplicates():
    day = 86400
    newest = 1_700_000_000
    raw = pd.DataFrame({
        "blog": ["tag:a", "tag:a", "tag:a", "tag:b"],
        "post_id": [1, 1, 2, 3],                      # post 1 is listed twice
        "text": ["x", "x", "y", "z"],
        "note_count": [10, 10, 5, 7],
        "timestamp": [newest - 100 * day, newest - 100 * day, newest - 5 * day, newest],
        "tags": ["['a']", "['a']", "['a']", "['a']"],
        "post_type": ["text"] * 4,
    })
    clean = clean_raw(raw)
    # post 1 stays once, post 2 is 5 days old and post 3 is 0 days old, so both go
    assert clean["post_id"].tolist() == [1]
    assert "source" in clean.columns   # "blog" was renamed


def test_clean_raw_leaves_out_the_named_blogs_by_default():
    day = 86400
    raw = pd.DataFrame({
        "source": ["darkcabin", "tag:dark academia"],
        "post_id": [1, 2],
        "text": ["x", "y"],
        "note_count": [500, 3],
        "timestamp": [1_600_000_000 - 100 * day, 1_600_000_000 - 100 * day],
        "scraped_at": [1_600_000_000, 1_600_000_000],   # both posts are 100 days old
        "tags": ["['a']", "['a']"],
        "post_type": ["text", "text"],
    })
    assert clean_raw(raw)["post_id"].tolist() == [2]


def test_tag_vocab_uses_the_most_common_tags_and_skips_searched_tags():
    tag_lists = [["vintage", "dark academia"], ["vintage", "books"], ["vintage"], ["books"], ["rare"]]
    vocab = pick_tag_vocab(tag_lists)
    assert vocab[:2] == ["vintage", "books"]       # most common first
    assert "dark academia" not in vocab            # we searched for it, so every post has it


def test_feature_row_marks_which_popular_tags_a_post_uses():
    row = build_feature_row("hi", 2, "text", 5, 1, tags=["vintage", "x"], tag_vocab=["vintage", "books"])
    assert row[tag_column_name("vintage")] == 1
    assert row[tag_column_name("books")] == 0


def test_blog_history_uses_only_the_other_posts_of_the_blog():
    blogs = pd.Series(["a", "a", "a", "b"])
    log_notes = pd.Series([1.0, 2.0, 3.0, 10.0])
    typical, peers = blog_history(blogs, log_notes)
    assert typical[0] == 2.5            # average of 2.0 and 3.0, never its own 1.0
    assert typical[2] == 1.5
    assert peers.tolist() == [2, 2, 2, 0]
    # blog "b" has one post, so it gets the average of everyone else: (1 + 2 + 3) / 3
    assert typical[3] == 2.0


# ---- collect.py -------------------------------------------------------------

def test_strip_html_removes_tags_and_decodes_symbols():
    assert collect.strip_html("<p>Hello&hellip;  <b>world</b></p>") == "Hello… world"


def test_get_text_uses_the_right_field_for_each_post_type():
    assert collect.get_text({"type": "quote", "text": "<p>quoted</p>"}) == "quoted"
    assert collect.get_text({"type": "photo", "caption": "<p>a caption</p>"}) == "a caption"
    assert collect.get_text({"type": "text", "title": "Hi", "body": "<p>there</p>"}) == "Hi there"


def test_reblog_check_reads_the_trail():
    # An original post: the trail has one item and it is the post itself.
    original = {"trail": [{"is_root_item": True, "is_current_item": True}]}
    assert collect.looks_like_reblog(original) == 0
    # A reblog: the root of the chain is somebody else's post.
    reblog = {"trail": [{"is_root_item": True, "is_current_item": False},
                        {"is_root_item": False, "is_current_item": True}]}
    assert collect.looks_like_reblog(reblog) == 1
    assert collect.looks_like_reblog({"id": 5}) == 0
    assert collect.looks_like_reblog({"reblogged_from_name": "someone"}) == 1   # old-style field


def test_has_image_finds_pictures_in_the_body_and_in_photo_posts():
    assert collect.has_image({"type": "photo"}) == 1
    assert collect.has_image({"type": "text", "body": '<figure><img src="x"></figure>'}) == 1
    assert collect.has_image({"type": "text", "body": "<p>only words</p>"}) == 0


def test_comment_text_is_what_the_poster_added():
    post = {"reblog": {"comment": "<p>my own words</p>"}}
    assert collect.get_comment_text(post) == "my own words"
    assert collect.get_comment_text({}) == ""


class FakeClient:
    """Pretends to be the Tumblr client, so we can test the paging without the internet."""

    def __init__(self, pages):
        self.pages = list(pages)

    def posts(self, blog, limit, offset):
        return self.pages.pop(0) if self.pages else {"meta": {"status": 404}}

    def tagged(self, tag, before, limit):
        return self.pages.pop(0) if self.pages else []


def fake_post(post_id, timestamp=1_600_000_000):
    return {"id": post_id, "type": "text", "body": "hello", "note_count": 3,
            "timestamp": timestamp, "tags": ["x"]}


def test_collect_blog_stops_when_tumblr_returns_nothing(monkeypatch):
    monkeypatch.setattr(collect.time, "sleep", lambda seconds: None)
    client = FakeClient([{"posts": [fake_post(1), fake_post(2)]}])
    rows = collect.collect_blog(client, "some-blog")
    assert len(rows) == 2          # got the first page, then hit the 404 page and stopped


def test_collect_tag_stops_politely_when_tumblr_sends_an_error_message(monkeypatch):
    monkeypatch.setattr(collect.time, "sleep", lambda seconds: None)
    client = FakeClient([[fake_post(1)], {"meta": {"status": 429, "msg": "Too many requests"}}])
    rows = collect.collect_tag(client, "dark academia")
    assert len(rows) == 1            # kept the first page, did not crash on the message


def test_one_odd_post_does_not_stop_the_download():
    posts = [fake_post(1), "this is not a post", fake_post(2)]
    assert len(collect.rows_from(posts, "tag:x")) == 2


def test_collect_tag_stops_if_the_time_does_not_move_back(monkeypatch):
    monkeypatch.setattr(collect.time, "sleep", lambda seconds: None)
    # Both pages end at a time that is later than "before", so the loop must stop by itself.
    future = 4_000_000_000
    client = FakeClient([[fake_post(1, future)], [fake_post(2, future)]])
    rows = collect.collect_tag(client, "dark academia")
    assert len(rows) == 1


# ---- predict.py -------------------------------------------------------------

class FakeModel:
    """A model that likes posts made at 10:00 and ignores everything else."""

    def predict(self, frame):
        return np.where(frame["hour"] == 10, 6.0, 3.0)


def make_bundle(trusted):
    return {
        "model": FakeModel(),
        "feature_columns": FEATURE_COLUMNS,
        "train_log_notes": np.array([1.0, 2.0, 3.0, 4.0]),
        "trusted_features": trusted,
    }


def test_predict_notes_turns_the_log_back_into_notes_and_gives_a_percentile():
    result = predict_notes(make_bundle(["hour"]), Draft("text", ["a", "b", "c"], "text", hour=10, day_of_week=0))
    assert round(result["notes"]) == round(np.expm1(6.0))
    assert result["percentile"] == 100.0     # 6.0 is above every training value


def test_suggestions_only_cover_trusted_columns():
    text = "some words here"
    draft = Draft(text, ["a", "b", "c"], "text", hour=2, day_of_week=0)
    with_hour = suggest_changes(make_bundle(["hour"]), draft)
    assert len(with_hour) == 1 and "10:00" in with_hour[0]

    nothing_trusted = suggest_changes(make_bundle([]), draft)
    assert nothing_trusted == []


class TagLovingModel:
    """A model that predicts more notes when the post has the tag 'vintage'."""

    def predict(self, frame):
        return np.where(frame[tag_column_name("vintage")] == 1, 6.0, 3.0)


def test_app_can_suggest_adding_a_tag_the_model_relies_on():
    bundle = {
        "model": TagLovingModel(),
        "feature_columns": FEATURE_COLUMNS + [tag_column_name("vintage")],
        "tag_vocab": ["vintage"],
        "train_log_notes": np.array([1.0, 2.0, 3.0]),
        "trusted_features": [tag_column_name("vintage")],
    }
    advice = suggest_changes(bundle, Draft("some words", ["books"], "text", hour=5, day_of_week=2))
    assert len(advice) == 1 and "#vintage" in advice[0]
    # once the post already has the tag, there is nothing left to add
    assert suggest_changes(bundle, Draft("some words", ["vintage"], "text", hour=5, day_of_week=2)) == []


# ---- train.py ---------------------------------------------------------------

def test_average_gap_is_negative_when_the_model_beats_the_baseline():
    results = {
        "a": {"model_rmse": 1.0, "baseline_rmse": 2.0},
        "b": {"model_rmse": 3.0, "baseline_rmse": 3.0},
    }
    assert average_gap(results) == -0.5


class EchoModel:
    """A model that simply repeats the blog's usual notes (log scale)."""

    def predict(self, frame):
        return frame["blog_typical_log_notes"].to_numpy()


def test_usual_notes_from_the_creator_drive_the_prediction():
    bundle = {
        "model": EchoModel(),
        "feature_columns": FEATURE_COLUMNS,
        "train_log_notes": np.array([1.0, 2.0, 3.0]),
        "default_typical_log": 1.0,
    }
    given = predict_notes(bundle, Draft("words", typical_notes=19))
    assert round(given["notes"]) == 19
    # when the creator does not say, the bundle's middle value is used instead
    missing = predict_notes(bundle, Draft("words"))
    assert round(missing["notes"], 3) == round(float(np.expm1(1.0)), 3)


def test_prediction_comes_with_a_range_around_the_answer():
    bundle = {
        "model": EchoModel(),
        "feature_columns": FEATURE_COLUMNS,
        "train_log_notes": np.array([1.0, 2.0, 3.0]),
        "error_range": (-1.0, 0.5),
    }
    result = predict_notes(bundle, Draft("words", typical_notes=19))   # log1p(19) is about 3.0
    assert result["low"] < result["notes"] < result["high"]
    assert round(result["low"]) == round(np.expm1(np.log1p(19) - 1.0))


def test_a_low_range_never_goes_below_zero_notes():
    bundle = {
        "model": EchoModel(),
        "feature_columns": FEATURE_COLUMNS,
        "train_log_notes": np.array([1.0]),
        "error_range": (-5.0, 5.0),
    }
    assert predict_notes(bundle, Draft("words", typical_notes=1))["low"] == 0.0


def test_draft_check_counts_words_and_tags_next_to_the_niche_median():
    bundle = {"niche_medians": {"word_count": 20.0, "tag_count": 9.0, "readability": 60.0}}
    rows = draft_check(bundle, Draft("one two three", tags=["a", "b"]))
    assert rows[0][:3] == ("Words", 3, 20.0)
    assert rows[1][:3] == ("Tags", 2, 9.0)


def test_usual_notes_model_keeps_up_with_blogs_outside_the_training_range():
    from sklearn.ensemble import RandomForestRegressor
    rng = np.random.default_rng(0)
    usual = rng.uniform(0, 3, 200)
    frame = pd.DataFrame({"blog_typical_log_notes": usual, "noise": rng.normal(size=200)})
    model = UsualNotesModel(RandomForestRegressor(n_estimators=50, random_state=0)).fit(frame, usual)
    # a blog far above anything seen in training: a plain forest would stop near 3
    far_above = pd.DataFrame({"blog_typical_log_notes": [6.0], "noise": [0.0]})
    assert model.predict(far_above)[0] > 5.0


def test_usual_notes_model_still_works_without_the_usual_notes_column():
    from sklearn.ensemble import RandomForestRegressor
    frame = pd.DataFrame({"a": np.arange(30.0)})
    model = UsualNotesModel(RandomForestRegressor(n_estimators=20, random_state=0)).fit(frame, np.arange(30.0))
    assert model.predict(frame).shape == (30,)
