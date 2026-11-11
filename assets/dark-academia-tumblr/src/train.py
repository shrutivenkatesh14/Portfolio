"""
Step 3: train the models, test them, and save the best one.

Run it from the project root:

    python -m src.train

The most important idea in this file is how we test. A creator who uses the app
is usually NOT one of the blogs we trained on. So the main test keeps every post
from a blog together, either all in the training part or all in the test part.
The score then tells us how the model does on blogs it has never seen.
(If posts from the same blog were mixed into both parts, the model could just
learn "this blog gets lots of notes", and the score would look better than it is.)
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import (GroupKFold, GroupShuffleSplit, KFold, cross_val_predict,
                                     cross_val_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src import config
from src.features import FEATURE_COLUMNS, TAG_COLUMN_PREFIX, tag_vocab_from_columns
from src.usual_model import UsualNotesModel


def make_models():
    """The models we compare, from the simplest to the most flexible."""
    seed = config.RANDOM_SEED
    return {
        # Always guesses the average. Any real model has to beat this.
        "Baseline (average)": DummyRegressor(strategy="mean"),
        # A straight-line model. Needs the numbers on the same scale first, so it gets a scaler.
        "Ridge regression": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        # Many decision trees voting. Can pick up on "if X and Y then high".
        # min_samples_leaf stops the trees from memorizing single posts.
        # Both tree models sit on top of a straight line through the blog's usual notes
        # (see usual_model.py), so they do not squash blogs that get a lot of notes.
        "Random forest": UsualNotesModel(RandomForestRegressor(
            n_estimators=300, min_samples_leaf=3, random_state=seed, n_jobs=-1
        )),
        # Trees built one after another, each fixing the mistakes of the last.
        "Gradient boosting": UsualNotesModel(GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05, random_state=seed
        )),
    }


def rmse(actual, predicted):
    """The typical size of the mistakes, in the same units as the thing we predict. Lower is better."""
    return float(np.sqrt(mean_squared_error(actual, predicted)))


def split_by_blog(df):
    """Split the posts 80/20, keeping every blog entirely on one side."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=config.TEST_SIZE,
                                 random_state=config.RANDOM_SEED)
    train_rows, test_rows = next(splitter.split(df, groups=df["blog"]))
    return df.iloc[train_rows], df.iloc[test_rows]


def compare_models(df, columns):
    """Score every model three ways."""
    train, test = split_by_blog(df)
    X, y, blogs = df[columns], df["log_notes"], df["blog"]

    # Normal cross-validation: split into 5 parts, test on each in turn, average.
    random_folds = KFold(config.CV_FOLDS, shuffle=True, random_state=config.RANDOM_SEED)
    # The same idea, but a blog never appears in two parts.
    blog_folds = GroupKFold(n_splits=config.BLOG_FOLDS)

    results = {}
    for name, model in make_models().items():
        random_cv = cross_val_score(model, X, y, cv=random_folds, scoring="r2")
        unseen_cv = cross_val_score(model, X, y, cv=blog_folds, groups=blogs, scoring="r2")
        fitted = clone(model).fit(train[columns], train["log_notes"])
        predictions = fitted.predict(test[columns])
        results[name] = {
            "test_rmse_unseen_blogs": rmse(test["log_notes"], predictions),
            "test_r2_unseen_blogs": float(r2_score(test["log_notes"], predictions)),
            "cv_r2_unseen_blogs": float(unseen_cv.mean()),
            "cv_r2_unseen_blogs_std": float(unseen_cv.std()),
            "cv_r2_random_split": float(random_cv.mean()),
        }
    return results


def hold_out_by_blog(model, df, columns):
    """
    Check 1: how far off is the model on blogs it has never seen,
    compared with just guessing the average?

    Each round trains on four parts and tests on the fifth. The baseline is the
    average of the training part. If the model learned what makes a post do well,
    its error should be lower than the baseline's.
    """
    results = {}
    folds = GroupKFold(n_splits=config.BLOG_FOLDS).split(df, groups=df["blog"])
    for number, (train_rows, test_rows) in enumerate(folds, start=1):
        train, test = df.iloc[train_rows], df.iloc[test_rows]
        fitted = clone(model).fit(train[columns], train["log_notes"])
        predictions = fitted.predict(test[columns])
        average_guess = np.full(len(test), train["log_notes"].mean())
        results[f"round {number}"] = {
            "posts": int(len(test)),
            "blogs": int(test["blog"].nunique()),
            "model_rmse": rmse(test["log_notes"], predictions),
            "baseline_rmse": rmse(test["log_notes"], average_guess),
        }
    return results


def average_gap(held_out):
    """
    One number for the check above: the model's error minus the baseline's error,
    averaged over the rounds. Lower is better, and below 0 means the model beats
    the baseline on blogs it has not seen.
    """
    return float(np.mean([r["model_rmse"] - r["baseline_rmse"] for r in held_out.values()]))


def choose_feature_set(model, df, base_columns, tag_columns):
    """
    Decide whether the has_tag_ columns are worth keeping.

    They stay only if they lower the average gap on blogs the model has not seen.
    """
    candidates = {"base columns": base_columns, "base + tag columns": base_columns + tag_columns}
    blog_folds = GroupKFold(n_splits=config.BLOG_FOLDS)
    scored = {}
    print("Does adding tag columns help? (judged on blogs the model has not seen)")
    for name, columns in candidates.items():
        r2 = float(cross_val_score(clone(model), df[columns], df["log_notes"],
                                   cv=blog_folds, groups=df["blog"], scoring="r2").mean())
        gap = average_gap(hold_out_by_blog(model, df, columns))
        scored[name] = {"cv_r2_unseen_blogs": r2, "unseen_blog_gap": gap}
        print(f"  {name:<20} R2 on unseen blogs {r2:.3f}   gap to baseline {gap:+.2f}")
    chosen = min(scored, key=lambda name: scored[name]["unseen_blog_gap"])
    print(f"  Using: {chosen}\n")
    return candidates[chosen], scored


def blog_average_check(df):
    """
    Check 2: how much of the difference between posts is just "which blog is it"?

    For every post we guess the average of the OTHER posts from the same blog.
    The post is never used to guess itself. If this scores well, the blog matters a lot.
    Blogs with only one post in the data fall back to the overall average.
    """
    y = df["log_notes"]
    blog_total = y.groupby(df["blog"]).transform("sum")
    blog_count = y.groupby(df["blog"]).transform("count")
    others_average = (blog_total - y) / (blog_count - 1).where(blog_count > 1)
    overall_others = (y.sum() - y) / (len(y) - 1)
    guess = others_average.fillna(overall_others)
    return float(r2_score(y, guess)), float((blog_count > 1).mean())


def usual_notes_check(model, df, columns):
    """
    Check 3: how much does the blog's usual notes matter next to the post itself?

    We score the model three ways on blogs it has not seen: with everything, with
    the blog's usual notes taken away, and with ONLY the blog's usual notes.
    """
    folds = GroupKFold(n_splits=config.BLOG_FOLDS)
    post_only = [c for c in columns if c != "blog_typical_log_notes"]

    def score(chosen):
        """Score the model on blogs it has not seen, using only the columns we give it."""
        return float(cross_val_score(clone(model), df[chosen], df["log_notes"],
                                     cv=folds, groups=df["blog"], scoring="r2").mean())

    return score(columns), score(post_only), score(["blog_typical_log_notes"])


def make_tag_stats(df):
    """
    For each tag: how many posts and how many different blogs use it.

    We rank by the number of blogs, not by notes. We looked at notes per tag after
    taking each blog's usual notes into account, and no tag stood out once it had
    enough posts, so ranking tags by notes would only show luck.
    """
    rows = df[["blog", "tags"]].copy()
    rows["tags"] = rows["tags"].apply(json.loads)
    rows = rows.explode("tags").dropna(subset=["tags"])
    stats = rows.groupby("tags").agg(posts=("blog", "size"), blogs=("blog", "nunique"))
    stats = stats[(stats["posts"] >= config.MIN_TAG_POSTS) & (stats["blogs"] >= config.MIN_TAG_BLOGS)]
    # The tags we searched for are on every post from that search, so they tell us nothing.
    stats = stats[~stats.index.isin(config.TAGS)]
    return stats.sort_values("blogs", ascending=False).reset_index(names="tag")


def main():
    """Run the whole training step:
    1. Compare the models and pick the best one.
    2. Decide whether the tag columns help.
    3. Run the checks: unseen blogs, blog average, and with or without the blog's usual notes.
    4. Work out which columns the model leans on, and how far off a typical prediction is.
    5. Save the model, the tag table and the numbers for the app.
    """
    df = pd.read_csv(config.FEATURES_FILE)
    print(f"Training on {len(df)} posts from {df['blog'].nunique()} blogs.\n")

    # ---- Compare the models ------------------------------------------------
    results = compare_models(df, FEATURE_COLUMNS)
    table = pd.DataFrame(results).T.round(3)
    print("Model comparison (R2: 1 is perfect, 0 is no better than guessing the average)")
    print(table.to_string(), "\n")

    # Pick the best real model by its score on unseen blogs, because that is how the app is used.
    real_models = {name: r for name, r in results.items() if not name.startswith("Baseline")}
    best_name = max(real_models, key=lambda name: real_models[name]["cv_r2_unseen_blogs"])
    best_model = make_models()[best_name]
    print(f"Best model: {best_name}\n")

    # Tag columns (does the post use #vintage?) are optional. See choose_feature_set.
    tag_columns = [c for c in df.columns if c.startswith(TAG_COLUMN_PREFIX)]
    feature_columns, feature_set_scores = FEATURE_COLUMNS, {}
    if tag_columns:
        feature_columns, feature_set_scores = choose_feature_set(
            best_model, df, FEATURE_COLUMNS, tag_columns)

    # ---- Is the model learning posts, or just blogs? -----------------------
    held_out = hold_out_by_blog(best_model, df, feature_columns)
    print("Check 1: test on blogs the model has not seen (lower RMSE is better)")
    for name, r in held_out.items():
        verdict = "beats baseline" if r["model_rmse"] < r["baseline_rmse"] else "WORSE than baseline"
        print(f"  {name}: {r['posts']:>4} posts from {r['blogs']:>3} blogs  "
              f"model {r['model_rmse']:.2f}  baseline {r['baseline_rmse']:.2f}  {verdict}")

    blog_r2, share_with_peers = blog_average_check(df)
    print(f"\nCheck 2: guessing each post from the other posts of the same blog gets R2 = {blog_r2:.3f}")
    print(f"         ({share_with_peers:.0%} of posts have another post from the same blog in the data)")
    print(f"         the model on unseen blogs gets R2 = "
          f"{real_models[best_name]['cv_r2_unseen_blogs']:.3f}\n")

    full_r2, post_only_r2, usual_only_r2 = usual_notes_check(best_model, df, feature_columns)
    print(f"Check 3: with everything the model gets                   R2 = {full_r2:.3f}")
    print(f"         without the blog's usual notes it gets            R2 = {post_only_r2:.3f}")
    print(f"         with ONLY the blog's usual notes it gets          R2 = {usual_only_r2:.3f}\n")

    # ---- Which features does the model lean on? ----------------------------
    # Permutation importance: shuffle one column on the test posts and see how
    # much worse the predictions get. A big drop means the model needed that column.
    # The test posts come from blogs the model has not seen.
    train, test = split_by_blog(df)
    fitted = clone(best_model).fit(train[feature_columns], train["log_notes"])
    importance = permutation_importance(
        fitted, test[feature_columns], test["log_notes"],
        n_repeats=30, random_state=config.RANDOM_SEED, scoring="r2",
    )
    importance_table = pd.DataFrame({
        "feature": feature_columns,
        "drop_in_r2": importance.importances_mean,
        "spread": importance.importances_std,
    }).sort_values("drop_in_r2", ascending=False)
    print("Feature importance (how much R2 drops when the column is shuffled)")
    print(importance_table.head(8).round(3).to_string(index=False), "\n")

    # A column counts as "trusted" if shuffling it clearly hurts the model: the drop
    # is at least 0.02 and more than twice its spread. The app only gives advice about
    # trusted columns, because a column the model barely uses cannot give useful advice.
    trusted = importance_table[
        (importance_table["drop_in_r2"] >= 0.02)
        & (importance_table["drop_in_r2"] > 2 * importance_table["spread"])
    ]["feature"].tolist()
    print(f"Columns the app is allowed to give advice about: {trusted}\n")

    # ---- How far off is a typical prediction? ------------------------------
    # We predict every post from a model that never saw its blog, then look at the
    # mistakes (on the log scale). The app uses the 10th and 90th percentile of those
    # mistakes to draw a range around its answer: about 8 posts in 10 land inside it.
    out_of_fold = cross_val_predict(
        clone(best_model), df[feature_columns], df["log_notes"],
        cv=GroupKFold(n_splits=config.BLOG_FOLDS), groups=df["blog"])
    error_low, error_high = np.quantile(df["log_notes"] - out_of_fold, [0.10, 0.90])
    print(f"Typical mistake range (log scale): {error_low:+.2f} to {error_high:+.2f}\n")

    # Middle values for posts with some text. The app shows these next to a draft.
    with_text = df[df["has_caption"] == 1]
    niche_medians = {
        "word_count": float(with_text["word_count"].median()),
        "tag_count": float(df["tag_count"].median()),
        "readability": float(with_text["readability"].median()),
    }

    # ---- Save everything the app needs -------------------------------------
    # The final model is trained on all posts, since the checks above are done.
    final_model = clone(best_model).fit(df[feature_columns], df["log_notes"])
    config.MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump({
        "model": final_model,
        "model_name": best_name,
        "feature_columns": feature_columns,
        "tag_vocab": tag_vocab_from_columns(feature_columns),
        # The note counts the model was trained on. The app uses these to say
        # "this draft is predicted to beat X percent of posts".
        "train_log_notes": df["log_notes"].to_numpy(),
        "n_posts": int(len(df)),
        "n_blogs": int(df["blog"].nunique()),
        # What to use for "usual notes" when the creator does not tell us (log scale).
        "default_typical_log": float(df["log_notes"].median()),
        "trusted_features": trusted,
        # The app only suggests a tag count inside the range where most of our posts sit
        # (10th to 90th percentile). Beyond that we have too few posts to say anything.
        "tag_count_range": (int(df["tag_count"].quantile(0.10)), int(df["tag_count"].quantile(0.90))),
        "error_range": (float(error_low), float(error_high)),
        # Only about 1 blog in 10 in the data usually gets more notes than this (the 90th
        # percentile). The model has seen little above it, and its answer drifts toward
        # the average there. The app warns when a creator is above it.
        "usual_notes_limit": float(np.expm1(df["blog_typical_log_notes"].quantile(0.90))),
        "niche_medians": niche_medians,
    }, config.MODEL_FILE)

    make_tag_stats(df).to_csv(config.TAG_STATS_FILE, index=False)

    config.REPORT_DIR.mkdir(exist_ok=True)
    metrics = {
        "posts": int(len(df)),
        "blogs": int(df["blog"].nunique()),
        "sources": df["source"].value_counts().to_dict(),
        "best_model": best_name,
        "model_comparison": results,
        "feature_sets": feature_set_scores,
        "feature_columns_used": feature_columns,
        "unseen_blog_rounds": held_out,
        "error_range": [float(error_low), float(error_high)],
        "blog_average_r2": blog_r2,
        "final_cv_r2_unseen_blogs": full_r2,
        "post_features_only_r2": post_only_r2,
        "usual_notes_only_r2": usual_only_r2,
        "share_posts_with_blog_peers": share_with_peers,
        "top_features": importance_table.head(8).round(4).to_dict(orient="records"),
        "trusted_features": trusted,
    }
    config.METRICS_FILE.write_text(json.dumps(metrics, indent=2))
    print(f"Saved the model to {config.MODEL_FILE}")
    print(f"Saved the numbers to {config.METRICS_FILE}")


if __name__ == "__main__":
    main()
