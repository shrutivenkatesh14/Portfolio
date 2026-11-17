"""
The app. Paste a draft post and see what the model predicts.

Run it from the project root:

    streamlit run streamlit_app.py

It can be hosted for free on Streamlit Community Cloud, which runs a file like this
straight from a GitHub repo. Train the model first (python -m src.train) and run
python -m src.analysis, because the app loads the files those two steps save.

The app has two tabs:
  Score a draft        the main tool
  What the data shows  charts and the main findings

The colours and the result card are styled in app_style.css.
"""
import json
import math
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src import config
from src.predict import (DAY_NAMES, Draft, draft_check, load_bundle, popular_tags,
                         predict_notes, suggest_changes)

st.set_page_config(page_title="Dark Academia post scorer", layout="wide")

# Load the stylesheet once. It only contains our own colours and spacing.
STYLE_FILE = Path(__file__).resolve().parent / "app_style.css"
st.markdown(f"<style>{STYLE_FILE.read_text()}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_bundle():
    """Load the saved model once, not on every click."""
    return load_bundle()


@st.cache_data
def get_metrics():
    """The numbers train.py saved. They are quoted on the data tab."""
    try:
        return json.loads(config.METRICS_FILE.read_text())
    except FileNotFoundError:
        return None


bundle = get_bundle()
metrics = get_metrics()


# ---------------------------------------------------------------------------
# The examples and the starting values of the boxes
# ---------------------------------------------------------------------------

# Three drafts to try. The name is what shows on the chip.
EXAMPLES = [
    {"name": "Library line",
     "fields": {"draft_text": "Some nights the library is the only place that still feels like home. "
                              "The lamp, the dust, the sound of someone turning a page two tables away.",
                "tags_text": "dark academia, books, library, aesthetic", "usual_text": "6",
                "post_type": "text", "has_image": False, "day_name": "Thursday", "hour": 21}},
    {"name": "Short quote",
     "fields": {"draft_text": "Marginalia are the oldest comment section.",
                "tags_text": "dark academia, quotes", "usual_text": "25",
                "post_type": "text", "has_image": False, "day_name": "Saturday", "hour": 14}},
    {"name": "Reading list",
     "fields": {"draft_text": "Reading list for the autumn term: Middlemarch, The Secret History, and a "
                              "stack of poetry I will pretend to understand.",
                "tags_text": "dark academia, books, reading, autumn, literature, classic literature, "
                             "bookblr, light academia, poetry, aesthetic, academia, vintage",
                "usual_text": "3", "post_type": "text", "has_image": False,
                "day_name": "Monday", "hour": 10}},
]
EXAMPLE_NAMES = [example["name"] for example in EXAMPLES]

# The starting value of every box.
DEFAULTS = {"draft_text": "", "tags_text": "dark academia, books, aesthetic", "usual_text": "",
            "post_type": "text", "has_image": False, "day_name": "Friday", "hour": 20}

# First visit only: the page opens with the first example already scored, so there is
# something to look at straight away instead of an empty half of the page.
if "scored" not in st.session_state:
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.session_state.example_choice = EXAMPLE_NAMES[0]
    st.session_state.applied_example = None
    st.session_state.scored = None      # the last result: the draft, the usual notes and where it came from
    st.session_state.problem = None     # a message to show if the last press did not work


# ---------------------------------------------------------------------------
# Reading the boxes and scoring
# ---------------------------------------------------------------------------

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


def score_the_boxes(source, scroll=True):
    """
    Read the boxes, and if they make sense, keep the draft as the result to show.

    source is the name of the example that filled the boxes, or None if the person typed them.
    scroll says whether to bring the result into view afterwards (see scroll_to_result).
    """
    state = st.session_state
    text = state.draft_text.strip()
    if not text and not state.has_image:
        state.problem = "Paste some text first, or tick \"The post has an image\"."
        return
    typical_notes, problem = read_usual_notes(state.usual_text)
    if problem:
        state.problem = problem
        return
    draft = Draft(
        text=text,
        tags=[tag.strip().lower() for tag in state.tags_text.split(",") if tag.strip()],
        post_type=state.post_type,
        hour=int(state.hour),
        day_of_week=DAY_NAMES.index(state.day_name),
        has_image=bool(state.has_image),
        typical_notes=typical_notes,
    )
    state.problem = None
    state.scored = {"draft": draft, "typical": typical_notes, "source": source}
    state.scroll_to_result = scroll


def apply_example(name):
    """Copy an example into the boxes and score it straight away."""
    example = next(item for item in EXAMPLES if item["name"] == name)
    # On the very first visit the page is just opening, so there is nothing to scroll to.
    first_visit = st.session_state.scored is None
    for key, value in example["fields"].items():
        st.session_state[key] = value
    st.session_state.applied_example = name
    score_the_boxes(source=name, scroll=not first_visit)


def forget_example():
    """Runs when the person presses the score button: the boxes are theirs now, not an example's."""
    st.session_state.example_choice = None
    st.session_state.applied_example = None


# ---------------------------------------------------------------------------
# The result
# ---------------------------------------------------------------------------

SCALE_TOP = 1000   # the notes at the right end of the range bar


def position(notes):
    """Where a number of notes sits on the bar, as a percentage. The scale is logarithmic."""
    share = math.log1p(max(notes, 0)) / math.log1p(SCALE_TOP)
    return min(max(share, 0.0), 1.0) * 100


def range_bar_html(low, best, high, niche_median):
    """The range as a bar: a filled stretch, a tall mark for the best guess, a thin mark for the niche median."""
    left = position(low)
    width = max(position(high) - left, 1.5)
    ticks = "".join(f'<span style="left:{position(n):.1f}%">{n:,}</span>' for n in (1, 10, 100, 1000))
    description = (f"Likely range {low:,.0f} to {high:,.0f} notes, best guess {best:,.0f}, "
                   f"middle post in the data {niche_median:,.0f}, on a scale from 1 to 1,000")
    # The text above already says all of this, so the picture is hidden from screen readers
    # apart from this one description.
    return (f'<div class="range" role="img" aria-label="{description}">'
            f'<div class="track"><div class="fill" style="left:{left:.1f}%;width:{width:.1f}%"></div>'
            f'<div class="median" style="left:{position(niche_median):.1f}%"></div>'
            f'<div class="best" style="left:{position(best):.1f}%"></div></div>'
            f'<div class="ticks" aria-hidden="true">{ticks}</div></div>')


def result_html(result, niche_median):
    """
    The card at the top of the result: a perforated stamp with a postmark, like the stamps
    on the portfolio site. Only numbers go into this HTML, never the person's own text.
    """
    headline = f"Most posts like this get {result['low']:,.0f} to {result['high']:,.0f} notes"
    guess = f"Best guess: about {result['notes']:,.0f}."
    bar = range_bar_html(result["low"], result["notes"], result["high"], niche_median)
    legend = ("The tall mark is the best guess. The thin mark is the middle post in the data "
              f"({niche_median:,.0f} notes). About 8 posts in 10 landed inside a range like this "
              "when we tested on blogs the model had not seen.")
    return (f'<section class="result"><div class="stamp"><div class="stamp-inner">'
            f'<h2>{headline}</h2><p class="guess">{guess}</p>{bar}</div>'
            '<div class="postmark" aria-hidden="true"><span><b>8 in 10</b><br>in range</span></div>'
            f'</div><p class="legend">{legend}</p></section>')


def scroll_to_result():
    """
    On a narrow screen the result sits below the form, out of sight. After the person
    presses a button, move the page so the result is on screen. On a wide screen the
    result is already beside the form, so we do nothing there.
    """
    components.html(
        """<script>
        setTimeout(function () {
          try {
            var page = window.parent;
            if (page.innerWidth < 700) {
              var card = page.document.querySelector('.result');
              if (card) { card.scrollIntoView({behavior: 'smooth', block: 'start'}); }
            }
          } catch (error) { /* if the page will not let us, the result just stays where it is */ }
        }, 200);
        </script>""",
        height=0,
    )


def show_result(scored):
    """Everything on the right: the card, the notices, the suggestions, the draft check and the tags."""
    draft, typical_notes, source = scored["draft"], scored["typical"], scored["source"]
    result = predict_notes(bundle, draft)
    niche_median = math.expm1(bundle.get("default_typical_log", 0.0))

    if source:
        st.caption(f"This is the example \"{source}\". Change the draft and press the button to "
                   "try your own.")
    st.markdown(result_html(result, niche_median), unsafe_allow_html=True)

    notices = []
    if typical_notes is None:
        notices.append("**You did not say how many notes your posts usually get,** so the middle "
                       "value for the niche was used. The prediction is much less reliable without it.")
    limit = bundle.get("usual_notes_limit")
    if typical_notes is not None and limit is not None and typical_notes > limit:
        notices.append(f"**Few blogs are like yours.** Only about 1 blog in 10 in the data usually "
                       f"gets more than {limit:,.0f} notes, so the answer tends to come out too low.")
    notices.append(f"A post like this is predicted to get more notes than about "
                   f"{result['percentile']:.0f}% of the posts the model learned from.")
    st.markdown("\n\n".join(notices))

    st.markdown("## Changes the model would suggest")
    changes = suggest_changes(bundle, draft)
    if changes:
        st.markdown("\n".join(f"- {change}" for change in changes))
    else:
        st.markdown("None. Once your usual notes are counted, nothing about this draft "
                    "changes the prediction by much.")

    # The draft next to the middle value for the niche. This only describes the draft.
    words, tags, reading = draft_check(bundle, draft)
    def describe(row, unit):
        label, yours, median = row
        return f"{yours:.0f} {unit} (niche median {median:.0f})"
    st.markdown(f"**Your draft:** {describe(words, 'words')}, {describe(tags, 'tags')}, "
                f"reading ease {reading[1]:.0f} (niche median {reading[2]:.0f}).")

    st.markdown("## Tags many blogs in the niche use")
    st.markdown(", ".join(f"#{tag} ({blogs} blogs)" for tag, blogs, _ in popular_tags(draft.tags)))
    st.caption("Times are in UTC. Changes are tested one at a time. They are patterns in past "
               "posts, not promises.")
    if st.session_state.pop("scroll_to_result", False):
        scroll_to_result()


def score_tab():
    """The first tab: examples and the form on the left, the result on the right."""
    left, right = st.columns([1, 1.1], gap="large")
    with left:
        choice = st.pills("Try an example", EXAMPLE_NAMES, key="example_choice")
        if choice and choice != st.session_state.applied_example:
            apply_example(choice)

        # A form sends everything at once when the button is pressed,
        # instead of re-running the page after every key press.
        with st.form("draft_form", border=False):
            st.text_area("Your draft", key="draft_text", height=130,
                         placeholder="Paste the text of your post here")
            st.text_input("Tags (separate with commas)", key="tags_text")
            st.text_input("Notes your posts usually get", key="usual_text",
                          placeholder="For example 12")
            st.caption("The middle number from your last 10 to 20 posts. Leave it empty if unsure.")
            # These change the answer less than the usual notes do, so they are folded away.
            with st.expander("More details (small effect)"):
                st.caption("These change the answer much less than your usual notes do.")
                st.selectbox("Post type", ["text", "photo", "other"], key="post_type")
                st.checkbox("The post has an image", key="has_image")
                st.selectbox("Day", DAY_NAMES, key="day_name")
                st.slider("Hour (UTC)", 0, 23, key="hour")
            submitted = st.form_submit_button("Score this draft", type="primary",
                                              on_click=forget_example)
        if submitted:
            score_the_boxes(source=None)

    with right:
        if st.session_state.problem:
            st.warning(st.session_state.problem)
        if st.session_state.scored:
            show_result(st.session_state.scored)


# ---------------------------------------------------------------------------
# Tab 2: the findings
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
    """The second tab: the main finding, the chart and the tag table."""
    st.markdown(data_text())
    chart = config.FIGURE_DIR / "03_group_medians.png"
    if chart.exists():
        st.image(str(chart), caption="Median notes by post choices")
    if config.TAG_GROUPS_FILE.exists():
        st.markdown("## Notes by number of tags")
        st.dataframe(pd.read_csv(config.TAG_GROUPS_FILE), hide_index=True)
        st.write("Posts with more tags have more notes in the raw numbers. Part of that is "
                 "probably bigger blogs using more tags, so it is not proof that adding "
                 "tags will help.")
    spread = config.FIGURE_DIR / "01_note_distribution.png"
    if spread.exists():
        st.markdown("## How uneven notes are")
        st.image(str(spread))


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

st.title("Dark Academia post scorer")
st.write("What notes might a Tumblr draft get?")

tab_score, tab_data = st.tabs(["Score a draft", "What the data shows"])
with tab_score:
    score_tab()
with tab_data:
    data_tab()
