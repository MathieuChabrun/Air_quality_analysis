"""Smoke tests: the app runs for every pollutant / reference level, and data checks hold."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from streamlit.testing.v1 import AppTest

from utils.io import load_data
from utils.prep import make_tables, project_share_above

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(scope="module")
def tables():
    return make_tables(load_data())


def test_tables_are_clean(tables):
    s = tables["stations"]
    assert not s.duplicated(["pollutant", "year", "site_id"]).any()
    assert s["value"].between(0, 500).all()
    assert set(s["year"]) == {2015, 2025}


def test_paired_counts(tables):
    n = tables["paired"].groupby("pollutant").size().to_dict()
    assert n == {"NO2": 243, "PM10": 208, "PM2.5": 87}


def test_projection_is_monotonic_with_pace_zero(tables):
    p = tables["paired"]
    p = p[p.pollutant == "NO2"]
    flat = project_share_above(p, 20, 0.0)
    assert flat["share_above"].nunique() == 1  # no progress -> constant share


@pytest.mark.parametrize("pol_index", [0, 1, 2])
@pytest.mark.parametrize("ref_index", [0, 1, 2])
def test_app_runs(pol_index, ref_index):
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception
    at.selectbox[0].select_index(pol_index)
    at.radio[0].set_value(list(at.radio[0].options)[ref_index])
    at.run()
    assert not at.exception, at.exception
    assert len(at.metric) >= 4
