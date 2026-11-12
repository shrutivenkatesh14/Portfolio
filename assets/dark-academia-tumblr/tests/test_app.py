"""
Tests for the Streamlit app. They run the app without opening a browser.

They need the saved model, so run python -m src.train first. If Streamlit is not
installed, these tests are skipped.
"""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402


# The app file sits one folder above the tests, so we give its full path.
APP_FILE = str(Path(__file__).resolve().parent.parent / "streamlit_app.py")


def open_app():
    return AppTest.from_file(APP_FILE, default_timeout=60).run()


def press_score(app):
    [button for button in app.button if button.label == "Score it"][0].click().run()


def page_text(app):
    return "\n".join(item.value for item in app.markdown)


def test_the_app_opens_with_three_tabs_and_no_errors():
    app = open_app()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Score a draft", "What the data shows", "About"]


def test_scoring_a_draft_shows_a_range_and_the_draft_check():
    app = open_app()
    app.text_area(key="draft_text").set_value("A short line about old books.")
    app.text_input(key="usual_text").set_value("12")
    press_score(app)
    text = page_text(app)
    assert not app.exception
    assert "Most posts like this get between" in text
    assert "Your draft next to the niche" in text


def test_an_empty_draft_asks_for_text():
    app = open_app()
    app.text_area(key="draft_text").set_value("")
    press_score(app)
    assert len(app.warning) == 1


def test_a_usual_notes_box_that_is_not_a_number_gets_a_message():
    app = open_app()
    app.text_area(key="draft_text").set_value("some words")
    app.text_input(key="usual_text").set_value("abc")
    press_score(app)
    assert "as a number" in app.warning[0].value


def test_a_very_high_usual_notes_number_shows_the_warning():
    app = open_app()
    app.text_area(key="draft_text").set_value("some words")
    app.text_input(key="usual_text").set_value("5000")
    press_score(app)
    assert "Only about 1 blog in 10" in page_text(app)


def test_an_example_button_fills_the_boxes():
    app = open_app()
    app.button(key="example_1").click().run()
    assert app.text_area(key="draft_text").value.startswith("Marginalia")
