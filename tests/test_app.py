from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_default_view_and_filters():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert [metric.value for metric in app.metric][0:1] == ["100"]
    app.sidebar.multiselect(key="countries").set_value(["India"]).run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == ["1", "3", "3", "1"]
    app.sidebar.text_input(key="search").set_value("no such service").run()
    assert not app.exception
    assert app.info[0].value.startswith("No listings")
    app.sidebar.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "100"


def test_comparison_and_methodology_views():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.radio(key="section").set_value("Compare markets").run()
    assert not app.exception
    app.multiselect(key="compare").set_value([]).run()
    assert app.info[0].value == "Choose a market to start the comparison."
    app.multiselect(key="compare").set_value(["India", "United States"]).run()
    assert not app.exception
    app.radio(key="section").set_value("Data & methodology").run()
    assert not app.exception
    assert app.metric[2].value == "100"
