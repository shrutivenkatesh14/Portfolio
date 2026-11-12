# Why did this post blow up? Dark Academia on Tumblr

Tumblr has no analytics page for creators, so most people post without knowing
what to expect. This project is a pre-publish tool for Dark Academia creators. You
paste a draft, say how many notes your posts usually get, pick your tags, post type
and posting time, and it tells you:

- how many notes (likes and reblogs) a post like that is predicted to get, with a
  range around the answer
- how that compares with the posts the model learned from
- your draft's length, tag count and reading ease next to the niche median
- a different number of tags, if the model expects it to help (it says so when it has
  nothing to suggest)
- tags that many blogs in the niche use

It started as a group project for CIS 434 (Social Media and Text Analytics) at the
Simon Business School, Spring 2026. Team 5: Aditya Batwal, Arpita Patnaik,
Parnika Kulkarni, Ritwik Pandey and Shruti Venkatesh. This repo is the cleaned-up
version of the code, split into steps and with tests.

## How it works

1. **Collect** (`src/collect.py`). Downloads posts from five Tumblr tag searches
   (#dark academia, #aesthetic academia, #classic literature, #dark academia
   aesthetic and #dark academia quotes) and from three large Dark Academia blogs,
   using the Tumblr API. Tag searches only look at posts at least 30 days old,
   because a newer post has not had time to collect notes.
2. **Features** (`src/features.py`). Turns every post into 17 numbers: word count,
   average word length, how many of the words are different, a reading ease score,
   three sentiment scores (VADER), whether there is a question or an exclamation
   mark, whether there is any text and whether there is an image, the number
   of tags, the hour and day posted (UTC), the post type, and
   how many notes the blog's other posts usually get. The 10 most common tags can
   also get their own yes/no column. The tags we searched for are left out,
   because every post found through that search has the tag.
3. **Train** (`src/train.py`). Predicts `log(notes + 1)`. The two tree models sit on
   top of a straight line through the blog's usual notes (`src/usual_model.py`), so
   they keep up with blogs that get a lot of notes. The log is there because a
   few posts have thousands of times more notes than the rest. Four models are
   compared: an "always guess the average" baseline, ridge regression, a random
   forest and gradient boosting. The best one is saved.
4. **Explore** (`src/analysis.py`). Prints median notes by tags, day, time of day,
   post type, question and length, and saves charts to `reports/figures`.
5. **Score** (`src/predict.py` and `streamlit_app.py`). Builds the same numbers for your
   draft, runs the saved model, and tries one change at a time to see what the
   model prefers. The range comes from how far off the model was on blogs it had
   never seen. The app has three tabs: score a draft, what the data shows, and about.

**How the model is tested.** Someone using the app is usually not one of the blogs
we trained on. So every test keeps all the posts of a blog together, either all in
the training part or all in the test part. The score then says how the model does
on blogs it has never seen.

**The blog's usual notes.** A blog's usual notes is the average of its other posts.
It never includes the post being predicted. In the app you type it in yourself,
from your own last 10 to 20 posts.

## Results

2,455 posts from 1,001 different blogs. R² of 1 is perfect and 0 is no better than
guessing the average. Both columns are scores on posts the model has not seen. The
first is the one that matters for the app, because those blogs were never in training.

| Model | R² on unseen blogs | R² on a random split |
|---|---|---|
| Baseline (average) | -0.03 | 0.00 |
| Ridge regression | 0.50 | 0.54 |
| Gradient boosting | 0.66 | 0.73 |
| Random forest | 0.67 | 0.75 |
| **Random forest + tag columns** | **0.68** | n/a |

The random forest with tag columns beat the baseline's error in every one of the 5
test rounds.

**What the prediction is built on.** How a blog usually does is the biggest thing
behind a post's notes.

| What the random forest is told | R² on unseen blogs |
|---|---|
| Only the blog's usual notes | 0.60 |
| Only the post (words, tags, time, image) | 0.21 |
| Both | 0.68 |

So the blog's usual notes explain most of it. The post by itself explains about a
fifth, and adds a few points on top of the usual notes.

**Tags.** In the raw numbers, posts with more tags have more notes:

| Tags on the post | Posts | Median notes |
|---|---|---|
| 1 to 3 | 160 | 2 |
| 4 to 7 | 705 | 3 |
| 8 to 12 | 731 | 5 |
| 13 or more | 859 | 16 |

Part of this pattern is probably bigger blogs using more tags. Once the blog's usual
notes are in the model, shuffling the tag count lowers R² by only 0.03. That is still
the largest of any post feature, so the app can suggest a different number of tags, but
it is a pattern in past posts, not a promise. Day of the week, time of day, text length
and questions show small differences too, and the app does not give advice about them.

## The data

| Source | Posts | Different blogs |
|---|---|---|
| #dark academia | 600 | 316 |
| #classic literature | 598 | 379 |
| #dark academia quotes | 597 | 138 |
| #dark academia aesthetic | 590 | 164 |
| #aesthetic academia | 70 | 32 |

The raw download also has 372 posts from three large blogs (academia-aesthetics,
darkcabin, scholars-ink). They are old accounts whose posts have had years to collect
notes, and each one is a single blog, so they are kept out of the model. Set
`INCLUDE_NAMED_BLOGS = True` in `src/config.py` to use them.

## Run it

You need Python 3.10 or newer.

```bash
pip install -r requirements.txt

python -m src.collect       # optional: download fresh posts (needs a Tumblr API key, see .env.example)
python -m src.features      # clean the posts and build the numbers
python -m src.train         # train, test and save the model
python -m src.analysis      # tables and charts
streamlit run streamlit_app.py   # open the app in your browser
python -m pytest            # run the tests
```

The repo already includes `data/features.csv` and the trained model, so you can run
`streamlit_app.py` straight away. `data/tumblr_posts_raw.csv` is not included because it holds
other people's posts. Step 1 creates it. In `data/features.csv` the blogs are
numbered, not named. If you use a different version of scikit-learn, run
`python -m src.train` again so the saved model matches.

**Using a new data sheet.** Save it as `data/tumblr_posts_raw.csv`, then run
`python -m src.features`, `python -m src.train` and `python -m src.analysis`. The
sheet needs these columns: `source`, `post_id`, `blog_name`, `text`, `note_count`,
`timestamp`, `tags`, `post_type`. Columns for `has_image` and
`scraped_at` are used if they are there. Update the tables above from
`reports/metrics.json`.

To put the app online for free, use Streamlit Community Cloud. Push the repo to
GitHub, go to share.streamlit.io, sign in with GitHub, and click "Create app". Pick
this repo, the `main` branch and `streamlit_app.py` as the main file. Under advanced
settings choose Python 3.12, then Deploy. The
app reads the model from `models/` and its charts and numbers from `reports/`, so run
`python -m src.train` and `python -m src.analysis` and commit those folders first.
Free apps go to sleep when nobody visits and wake up on the next visit.

## What is in the repo

```
streamlit_app.py        The app (Streamlit)
.streamlit/config.toml  Colors and font for the app
src/config.py           Every setting in one place (tags, file paths, cleaning rules)
src/collect.py          Download posts from the Tumblr API
src/features.py         Clean the posts and build the numbers the model uses
src/train.py            Compare models, run the checks, save the best one
src/analysis.py         Tables and charts
src/predict.py          Scores a draft post (used by the app)
tests/                  Tests that run without internet
data/features.csv       One row per post, numbers only
models/                 The saved model and a table of popular tags
reports/                metrics.json and the charts
```

## Limits and next steps

The model learned from 2,455 posts, and a blog's usual notes comes from only a few
other posts per blog, so it is rough. The app says so. Where to go next:

1. Download more posts for each blog, so the usual notes is steadier and the
   effect of tags and timing can be measured within one blog.
2. Add the blog's follower count as a feature.
3. Add image features. Right now the model only knows whether there is an image.
4. Predict likes and reblogs separately. A reblog spreads a post and a like does not.
