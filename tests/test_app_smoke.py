from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_without_exception() -> None:
    app = AppTest.from_file("app.py", default_timeout=10).run()
    assert not app.exception
    assert app.title[0].value == "AsterPeak HR Helpdesk Assistant"
    assert any("AI assistant, not a human" in item.value for item in app.warning)
    assert app.chat_input[0].placeholder == "Ask an HR question…"
