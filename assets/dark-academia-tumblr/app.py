"""
The app. Paste a draft post and see what the model predicts.

Run it from the project root:

    python app.py

It also works on Hugging Face Spaces, which looks for a file called app.py.
Train the model first (python -m src.train) and run python -m src.analysis,
because the app loads the files those two steps save.

The app has three tabs:
  Score a draft        the main tool
  What the data shows  charts and the main findings
  About                how it was built and what to keep in mind
"""
import json

import gradio as gr
import pandas as pd

from src import config
from src.features import FEATURE_COLUMNS
from src.predict import (DAY_NAMES, Draft, draft_check, load_bundle, popular_tags,
                         predict_notes, suggest_changes)

bundle = load_bundle()

# The numbers quoted on the "data" and "about" tabs come from the file train.py wrote,
# so the text always matches the model that is loaded.
try:
    metrics = json.loads(config.METRICS_FILE.read_text())
except FileNotFoundError:
    metrics = None


# ---------------------------------------------------------------------------
# Tab 1: score a draft
# ---------------------------------------------------------------------------

def score(text, tags_text, typical_notes, post_type, has_image, day_name, hour):
    """Runs when the button is pressed. Returns the answer and the draft check."""
    text = (text or "").strip()
    if not text and not has_image:
        return "Paste some text first, or tick \"The post has an image\".", ""

    tags = [tag.strip().lower() for tag in (tags_text or "").split(",") if tag.strip()]
    draft = Draft(
        text=text,
        tags=tags,
        post_type=post_type,
        hour=int(hour),
        day_of_week=DAY_NAMES.index(day_name),
        has_image=bool(has_image),
        typical_notes=typical_notes,   # None when the box is empty
    )

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
    for tag, blogs, _ in popular_tags(tags):
        lines.append(f"- #{tag}, used by {blogs} blogs")
    lines += ["", "*Times are in UTC. Changes are tested one at a time. They are patterns in "
              "past posts, not promises.*"]

    return "\n".join(lines), check_table(draft)


def check_table(draft):
    """The draft next to the niche median, as a small table."""
    rows = ["| | Your draft | Niche median |", "|---|---|---|"]
    for label, yours, median in draft_check(bundle, draft):
        middle = "" if median is None else f"{median:.0f}"
        rows.append(f"| {label} | {yours:.0f} | {middle} |")
    return "### Your draft next to the niche\n" + "\n".join(rows)


# Three drafts to click on. Each row fills the boxes on the first tab, in order:
# text, tags, usual notes, post type, image, day, hour.
EXAMPLES = [
    ["Some nights the library is the only place that still feels like home. "
     "The lamp, the dust, the sound of someone turning a page two tables away.",
     "dark academia, books, library, aesthetic", 6, "text", False, "Thursday", 21],
    ["Marginalia are the oldest comment section.",
     "dark academia, quotes", 25, "text", False, "Saturday", 14],
    ["Reading list for the autumn term: Middlemarch, The Secret History, and a stack of "
     "poetry I will pretend to understand.",
     "dark academia, books, reading, autumn, literature, classic literature, bookblr, "
     "light academia, poetry, aesthetic, academia, vintage",
     3, "text", False, "Monday", 10],
]


# ---------------------------------------------------------------------------
# Tab 2 and 3: the findings and the notes
# ---------------------------------------------------------------------------

def data_text():
    """The words on the "What the data shows" tab. The numbers come from metrics.json."""
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


def tag_text():
    """One plain sentence to read next to the tag table."""
    return ("Posts with more tags have more notes in the raw numbers. Part of that is probably "
            "bigger blogs using more tags, so it is not proof that adding tags will help.")


def about_text():
    """The words on the "About" tab: where the project came from and what to keep in mind."""
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


def load_figure(name):
    """Return the path of a saved chart, or None if the chart has not been made yet."""
    path = config.FIGURE_DIR / name
    return str(path) if path.exists() else None


# ---------------------------------------------------------------------------
# Look of the app: dark paper, brass and a serif font
# ---------------------------------------------------------------------------

THEME = gr.themes.Base(
    primary_hue="amber",
    secondary_hue="stone",
    neutral_hue="stone",
    font=[gr.themes.GoogleFont("EB Garamond"), "Georgia", "serif"],
).set(
    body_background_fill_dark="#1d1914",
    body_text_color_dark="#e9e0cf",
    block_background_fill_dark="#26211b",
    block_border_color_dark="#3d352b",
    button_primary_background_fill_dark="#8a6d3b",
    button_primary_background_fill_hover_dark="#a3814a",
    button_primary_text_color_dark="#fffaf0",
)

# Headings in brass. Everything else comes from the theme above.
CSS = "h1, h2, h3 { font-family: 'Playfair Display', Georgia, serif; } .dark h1, .dark h2, .dark h3 { color: #c9a96a; }"

# Page loads in dark mode.
FORCE_DARK = "() => { document.body.classList.add('dark'); }"


with gr.Blocks(title="Dark Academia post scorer") as demo:
    gr.Markdown("# Dark Academia post scorer\nWhat notes might a Tumblr draft get?")

    with gr.Tabs():
        with gr.Tab("Score a draft"):
            with gr.Row():
                with gr.Column():
                    text_box = gr.Textbox(label="Your draft", lines=7,
                                          placeholder="Paste the text of your post here")
                    tags_box = gr.Textbox(label="Tags (separate with commas)",
                                          value="dark academia, books, aesthetic")
                    typical_box = gr.Number(
                        label="Notes your posts usually get", value=None, minimum=0,
                        info="Look at your last 10 to 20 posts and take the middle number.")
                    # These change the answer less than the usual notes do, so they are tucked away.
                    with gr.Accordion("More details (these change the answer much less)", open=False):
                        type_box = gr.Dropdown(["text", "photo", "other"], value="text",
                                               label="Post type")
                        image_box = gr.Checkbox(label="The post has an image")
                        day_box = gr.Dropdown(DAY_NAMES, value="Friday", label="Day")
                        hour_box = gr.Slider(0, 23, value=20, step=1, label="Hour (UTC)")
                    button = gr.Button("Score it", variant="primary")
                with gr.Column():
                    answer = gr.Markdown()
                    check = gr.Markdown()

            inputs = [text_box, tags_box, typical_box, type_box, image_box, day_box, hour_box]
            button.click(score, inputs, [answer, check])
            gr.Examples(examples=EXAMPLES, inputs=inputs, label="Try an example")

        with gr.Tab("What the data shows"):
            gr.Markdown(data_text())
            if load_figure("03_group_medians.png"):
                gr.Image(load_figure("03_group_medians.png"), show_label=False,
                         interactive=False, label="Median notes by post choices")
            if config.TAG_GROUPS_FILE.exists():
                gr.Markdown("### Notes by number of tags")
                gr.Dataframe(pd.read_csv(config.TAG_GROUPS_FILE), interactive=False)
                gr.Markdown(tag_text())
            if load_figure("01_note_distribution.png"):
                gr.Markdown("### How uneven notes are")
                gr.Image(load_figure("01_note_distribution.png"), show_label=False,
                         interactive=False)

        with gr.Tab("About"):
            gr.Markdown(about_text())


if __name__ == "__main__":
    demo.launch(theme=THEME, css=CSS, js=FORCE_DARK)
