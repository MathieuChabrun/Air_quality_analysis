"""Hook, context, audience and how to read the dashboard."""
import streamlit as st

from utils.constants import POLLUTANTS, YEAR_AFTER, YEAR_BEFORE
from utils.io import SOURCE_TEXT


def render() -> None:
    st.title("Is the air in France getting cleaner?")
    st.caption(f"{YEAR_BEFORE} vs {YEAR_AFTER} — nitrogen dioxide and fine particles at monitoring stations")
    st.caption(SOURCE_TEXT)

    st.markdown(
        f"""
**Why it matters.** Air pollution is one of the main environmental risks for health.
Cleaner air means fewer lung and heart problems. Rules are also getting stricter:
new EU limits start in **2030**, and the WHO advises even lower levels.

**This story has four steps:** 1) the big picture, 2) where it changed, 3) who is still
above the limits, 4) what it means for the next years.

**Who is it for?** Citizens and local decision-makers who want to know *where* the air
improved and *where* work is still needed.
"""
    )
    with st.expander("What are these pollutants? How do I read the charts?"):
        for p in POLLUTANTS.values():
            st.markdown(f"- **{p['label']}** — {p['source']} {p['health']}")
        st.markdown(
            f"""
- **Annual mean** = the average over a full year at one station, in µg/m³.
- **Same stations** = only stations validated in *both* {YEAR_BEFORE} and {YEAR_AFTER}, for a fair comparison.
- **Dashed line** = the reference level you choose in the sidebar (WHO guideline or EU limit).
- **Station type** = *Background* (away from direct sources), *Traffic* (near roads), *Industrial*.
"""
        )
