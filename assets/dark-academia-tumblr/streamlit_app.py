"""
The app. Paste a draft post and see what the model predicts.

Run it from the project root:

    streamlit run streamlit_app.py

It can be hosted for free on Streamlit Community Cloud, which runs a file like this
straight from a GitHub repo. Train the model first (python -m src.train) and run
python -m src.analysis, because the app loads the files those two steps save.

The app has three tabs:
  Score a draft        the main tool
  What the data shows  charts and the main findings
  About                how it was built and what to keep in mind
"""
import json

import pandas as pd
import streamlit as st

from src import config
from src.features import FEATURE_COLUMNS
from src.predict import (DAY_NAMES, Draft, draft_check, load_bundle, popular_tags,
                         predict_notes, suggest_changes)

st.set_page_config(page_title="Dark Academia post scorer", layout="wide")


@st.cache_resource
def get_bundle():
    """Load the saved model once, not on every click."""
    return load_bundle()


@st.cache_data
def get_metrics():
    """The numbers train.py saved. They are quoted on the data and about tabs."""
    try:
        return json.loads(config.METRICS_FILE.read_text())
    except FileNotFoundError:
        return None


bundle = get_bundle()
metrics = get_metrics()


# ---------------------------------------------------------------------------
# Tab 1: score a draft
# ---------------------------------------------------------------------------

# Three drafts to try. Each one fills in the boxes on the first tab.
EXAMPLES = [
    {"draft_text": "Some nights the library is the only place that still feels like home. "
                   "The lamp, the dust, the sound of someone turning a page two tables away.",
     "tags_text": "dark academia, books, library, aesthetic", "usual_text": "6",
     "post_type": "text", "has_image": False, "day_name": "Thursday", "hour": 21},
    {"draft_text": "Marginalia are the oldest comment section.",
     "tags_text": "dark academia, quotes", "usual_text": "25",
     "post_type": "text", "has_image": False, "day_name": "Saturday", "hour": 14},
    {"draft_text": "Reading list for the autumn term: Middlemarch, The Secret History, and a "
                   "stack of poetry I will pretend to understand.",
     "tags_text": "dark academia, books, reading, autumn, literature, classic literature, "
                  "bookblr, light academia, poetry, aesthetic, academia, vintage",
     "usual_text": "3", "post_type": "text", "has_image": False, "day_name": "Monday", "hour": 10},
]

# The starting value of every box. setdefault leaves a value alone if it is already there.
DEFAULTS = {"draft_text": "", "tags_text": "dark academia, books, aesthetic", "usual_text": "",
            "post_type": "text", "has_image": False, "day_name": "Friday", "hour": 20}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def use_example(number):
    """Runs when an example button is pressed: copy that example into the boxes."""
    for key, value in EXAMPLES[number].items():
        st.session_state[key] = value


def answer_text(draft, typical_notes):
    """The prediction, the range, the suggested changes and the popular tags, as Markdown."""
    result = predict_notes(bundle, draft)
    lines = [
        f"### About {result['notes']:,.0f} notes",
        f"Most posts like this get between {result['low']:,.0f} and {result['high']:,.0f} notes. "
        "That range comes from how far off the model was on blogs it had never seen: "
        "about 8 posts in 10 landed inside it.",
        "",
    ]
    if typical_notes is None:
        lines += ["You did not say how many notes your posts usually get, so the middle value "
                  "for the niche was used. The prediction is much less reliable without it.", ""]
    limit = bundle.get("usual_notes_limit")
    if typical_notes is not None and limit is not None and typical_notes > limit:
        lines += [f"Only about 1 blog in 10 in the data usually gets more than {limit:,.0f} notes, "
                  "so the model has seen little like yours. Its answer tends to come out too low.", ""]
    lines.append(f"A post like this is predicted to get more notes than about "
                 f"{result['percentile']:.0f}% of the posts the model learned from.")

    lines += ["", "### Changes the model would suggest"]
    changes = suggest_changes(bundle, draft)
    if changes:
        lines += [f"- {change}" for change in changes]
    else:
        lines.append("None. Once your usual notes are counted, nothing about this draft "
                     "changes the prediction by much.")

    lines += ["", "### Tags many blogs in the niche use"]
    for tag, blogs, _ in popular_tags(draft.tags):
        lines.append(f"- #{tag}, used by {blogs} blogs")
    lines += ["", "*Times are in UTC. Changes are tested one at a time. They are patterns in "
                  "past posts, not promises.*"]
    return "\n".join(lines)


def check_table(draft):
    """The draft next to the niche median, as a small Markdown table."""
    rows = ["| | Your draft | Niche median |", "|---|---|---|"]
    for label, yours, median in draft_check(bundle, draft):
        middle = "" if median is None else f"{median:.0f}"
        rows.append(f"| {label} | {yours:.0f} | {middle} |")
    return "### Your draft next to the niche\n" + "\n".join(rows)


def read_usual_notes(text):
    """
    Turn the "usual notes" box into a number.

    Returns (number, problem). An empty box gives (None, None), which means "not given".
    """
    text = (text or "").strip().replace(",", "")
    if not text:
        return None, None
    try:
        number = float(text)
    except ValueError:
        return None, "Type the usual notes as a number, like 12."
    if number < 0:
        return None, "The usual notes cannot be below 0."
    return number, None


def score_tab():
    st.write("Try an example:")
    columns = st.columns(len(EXAMPLES))
    for number, column in enumerate(columns):
        column.button(f"Example {number + 1}", key=f"example_{number}",
                      on_click=use_example, args=(number,))

    left, right = st.columns(2)
    with left:
        # A form sends everything at once when the button is pressed,
        # instead of re-running the page after every key press.
        with st.form("draft_form"):
            st.text_area("Your draft", key="draft_text", height=170,
                         placeholder="Paste the text of your post here")
            st.text_input("Tags (separate with commas)", key="tags_text")
            st.text_input("Notes your posts usually get", key="usual_text",
                          help="Look at your last 10 to 20 posts and take the middle number. "
                               "You can leave this empty.")
            # These change the answer less than the usual notes do, so they are tucked away.
            with st.expander("More details (these change the answer much less)"):
                st.selectbox("Post type", ["text", "photo", "other"], key="post_type")
                st.checkbox("The post has an image", key="has_image")
                st.selectbox("Day", DAY_NAMES, key="day_name")
                st.slider("Hour (UTC)", 0, 23, key="hour")
            submitted = st.form_submit_button("Score it", type="primary")

    with right:
        if not submitted:
            return
        text = st.session_state.draft_text.strip()
        if not text and not st.session_state.has_image:
            st.warning("Paste some text first, or tick \"The post has an image\".")
            return
        typical_notes, problem = read_usual_notes(st.session_state.usual_text)
        if problem:
            st.warning(problem)
            return
        draft = Draft(
            text=text,
            tags=[tag.strip().lower() for tag in st.session_state.tags_text.split(",")
                  if tag.strip()],
            post_type=st.session_state.post_type,
            hour=int(st.session_state.hour),
            day_of_week=DAY_NAMES.index(st.session_state.day_name),
            has_image=bool(st.session_state.has_image),
            typical_notes=typical_notes,
        )
        st.markdown(answer_text(draft, typical_notes))
        st.markdown(check_table(draft))


# ---------------------------------------------------------------------------
# Tab 2 and 3: the findings and the notes
# ---------------------------------------------------------------------------

def data_text():
    """The words on the data tab. The numbers come from metrics.json."""
    if metrics is None:
        return "Run `python -m src.train` to create the numbers for this page."
    return (
        f"We looked at {metrics['posts']:,} posts from {metrics['blogs']:,} different blogs. "
        "All of them came from Tumblr tag searches, and all were at least 30 days old when "
        "we downloaded them.\n\n"
        "Every score below is on blogs the model had not seen. R² is 1 for a perfect "
        "prediction and 0 for no better than guessing the average.\n\n"
        f"- Told only the blog's usual notes: R² {metrics['usual_notes_only_r2']:.2f}\n"
        f"- Told only about the post (words, tags, time, image): R² {metrics['post_features_only_r2']:.2f}\n"
        f"- Told both: R² {metrics['final_cv_r2_unseen_blogs']:.2f}\n\n"
        "So most of a post's notes come from the blog it is on. The post itself adds a "
        "smaller part."
    )


def data_tab():
    st.markdown(data_text())
    chart = config.FIGURE_DIR / "03_group_medians.png"
    if chart.exists():
        st.image(str(chart), caption="Median notes by post choices")
    if config.TAG_GROUPS_FILE.exists():
        st.markdown("### Notes by number of tags")
        st.dataframe(pd.read_csv(config.TAG_GROUPS_FILE), hide_index=True)
        st.write("Posts with more tags have more notes in the raw numbers. Part of that is "
                 "probably bigger blogs using more tags, so it is not proof that adding "
                 "tags will help.")
    spread = config.FIGURE_DIR / "01_note_distribution.png"
    if spread.exists():
        st.markdown("### How uneven notes are")
        st.image(str(spread))


def about_text():
    """The words on the about tab: where the project came from and what to keep in mind."""
    names = "Aditya Batwal, Arpita Patnaik, Parnika Kulkarni, Ritwik Pandey and Shruti Venkatesh"
    best = metrics["best_model"].lower() if metrics else "a model"
    return (
        "This started as a group project for CIS 434 (Social Media and Text Analytics) at the "
        f"Simon Business School, Spring 2026. Team 5: {names}.\n\n"
        f"The model is a {best} trained on log(notes + 1). It sees {len(FEATURE_COLUMNS)} numbers "
        "for each post: length, reading ease, sentiment, question and exclamation marks, "
        "whether there is an image, the number of tags, the hour and day, and the blog's "
        "usual notes.\n\n"
        "Keep in mind:\n"
        "- It learned from a small sample of Dark Academia posts, so treat the answer as a "
        "rough guide.\n"
        "- The range around the answer is wide on purpose. Notes are very uneven from post to post.\n"
        "- It cannot see the picture in a post, only whether there is one.\n"
        "- It describes patterns in past posts. It cannot say what would make your post do better."
    )


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

st.title("Dark Academia post scorer")
st.write("What notes might a Tumblr draft get?")

score, data, about = st.tabs(["Score a draft", "What the data shows", "About"])
with score:
    score_tab()
with data:
    data_tab()
with about:
    st.markdown(about_text())
