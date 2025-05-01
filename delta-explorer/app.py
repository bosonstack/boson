import os
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from scan_deltalake import scan_deltalake, DeltaLake

st.set_page_config("Delta Table Browser", layout="wide")

# 🔧 Custom styling
st.markdown("""
    <style>
        /* Hide header */
        header {
            visibility: hidden;
        }

        /* Hide first two element containers (for spacing cleanup) */
        .stMainBlockContainer > div > div > .stVerticalBlock > .stElementContainer:nth-of-type(1),
        .stMainBlockContainer > div > div > .stVerticalBlock > .stElementContainer:nth-of-type(2) {
            display: none !important;
        }

        /* Tighten layout */
        .block-container {
            padding-top: 1rem !important;
        }
            
        /* Theme */
        div.stAlertContainer[data-testid="stAlertContainer"] {
            background-color: rgba(72, 49, 167, 0.2);
            color: rgba(72, 49, 167, 1);
        }
    </style>
""", unsafe_allow_html=True)

st_autorefresh(interval=5000, key="autorefresh")

with st.container():
    st.markdown("### Delta Explorer")
    if st.button("🔄 Refresh"):
        st.session_state["_refresh"] = not st.session_state.get("_refresh", False)

search = st.text_input(
    label="Search",
    placeholder="🔍 Search tables or columns...",
    label_visibility="collapsed"
).strip().lower()

lake: DeltaLake = scan_deltalake()

def matches(table):
    if search in table.name.lower():
        return True
    for col in table.schema:
        if search in col.lower():
            return True
    return False

filtered_tables = [t for t in lake.delta_tables if matches(t)]

def format_ts(ts) -> str:
    if ts is None:
        return "-"
    if isinstance(ts, int):
        try:
            ts = datetime.fromtimestamp(ts / 1000)
        except Exception:
            return str(ts)
    return ts.astimezone().strftime("%Y-%m-%d %H:%M:%S")

if not filtered_tables:
    st.info("No tables match your search.")
else:
    st.success(f"Found `{len(filtered_tables)}` matching Delta table(s):")

    for table in filtered_tables:
        with st.expander(f"📊 **{table.name}**", expanded=False):
            st.code(table.path)

            # 🧾 Metadata (clean vertical display)
            st.markdown(f"""
**Latest Version:** {table.latest_version}  
**Created:** {format_ts(table.created_time)}  
**Last Updated:** {format_ts(table.last_updated_time)}
""")

            # 📐 Schema Table
            st.dataframe(
                [{"Column": col, "Type": typ} for col, typ in table.schema.items()],
                hide_index=True,
                use_container_width=True,
            )
