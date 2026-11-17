"""
Tests for the Streamlit app. They run the app without opening a browser.

They need the saved model, so run python -m src.train first. If Streamlit is not
installed, these tests are skipped.
"""
import re
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

# The app file sits one folder above the tests, so we give its full path.
APP_FILE = str(Path(__file__).resolve().parent.parent / "streamlit_app.py")

HEADLINE = re.compile(r"Most posts like this get [\d,]+ to [\d,]+ notes")


def open_app():
    return AppTest.from_file(APP_FILE, default_timeout=60).run()


def press_score(app):
    [button for button in app.button if button.label == "Score this draft"][0].click().run()


def page_text(app):
    return "\n".join(item.value for item in app.markdown)


def test_the_app_opens_with_two_tabs_and_no_errors():
    app = open_app()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Score a draft", "What the data shows"]


def test_the_page_opens_with_an_example_already_scored():
    app = open_app()
    assert HEADLINE.search(page_text(app))
    assert app.text_area(key="draft_text").value.startswith("Some nights the library")
    assert app.session_state.scored["source"] == "Library line"


def test_scoring_your_own_draft_replaces_the_example():
    app = open_app()
    app.text_area(key="draft_text").set_value("A short line about old books.")
    app.text_input(key="usual_text").set_value("12")
    press_score(app)
    assert not app.exception
    assert HEADLINE.search(page_text(app))
    assert app.session_state.scored["source"] is None     # it is the person's draft now
    assert app.session_state.example_choice is None       # so no example chip stays lit


def test_an_empty_draft_asks_for_text():
    app = open_app()
    app.text_area(key="draft_text").set_value("")
    press_score(app)
    assert len(app.warning) == 1


def test_a_usual_notes_box_that_is_not_a_number_gets_a_message():
    app = open_app()
    app.text_input(key="usual_text").set_value("abc")
    press_score(app)
    assert "as a number" in app.warning[0].value


def test_a_very_high_usual_notes_number_shows_the_warning():
    app = open_app()
    app.text_input(key="usual_text").set_value("5000")
    press_score(app)
    assert "Few blogs are like yours" in page_text(app)


def test_choosing_an_example_chip_fills_the_boxes_and_scores_it():
    app = open_app()
    app.session_state.example_choice = "Short quote"
    app.run()
    assert app.text_area(key="draft_text").value.startswith("Marginalia")
    assert app.session_state.scored["source"] == "Short quote"


def test_the_result_card_is_a_stamp_with_a_range_bar_and_a_postmark():
    text = page_text(open_app())
    assert 'class="stamp"' in text and 'class="postmark"' in text
    assert 'class="range"' in text      # the bar


def test_the_persons_own_words_never_go_into_the_html_of_the_card():
    app = open_app()
    app.text_area(key="draft_text").set_value("<script>alert(1)</script> hello")
    press_score(app)
    assert "alert(1)" not in page_text(app)
