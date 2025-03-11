import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Set page configuration
st.set_page_config(
    page_title="Tariff Tracker",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS for logo and about section
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        color: #4d4d4d;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0068c9;
    }
    .metric-label {
        font-size: 1rem;
        color: #4d4d4d;
    }
    .logo-text {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 2rem;
        text-align: left;
        font-family: monospace;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .about-section {
        padding-top: 1rem;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }
    /* Hide hamburger menu */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Add logo to sidebar
with st.sidebar:
    # Logo as text
    st.markdown(
        '<div class="logo-text">&lt;/newscatcher&gt;</div>', unsafe_allow_html=True
    )

    # About section at the bottom of sidebar
    st.markdown('<div class="about-section"></div>', unsafe_allow_html=True)
    st.markdown("### About")
    st.markdown(
        """
        This app visualizes global tariff events extracted from news data.
        
        Built with Streamlit and powered by the NewsCatcher Events API.
        
        © 2025 NewsCatcher Inc.
        """
    )


# Load sample data
@st.cache_data
def load_sample_data() -> Dict[str, Any]:
    """
    Load sample tariff events data from JSON file.

    Returns:
        Dict containing events data or empty dict if file not found
    """
    file_path = os.path.join("data", "sample_tariff_events.json")
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        st.error(f"Sample data file not found at {file_path}")
        return {"events": []}
    except json.JSONDecodeError:
        st.error("Error parsing the sample data file")
        return {"events": []}


sample_data = load_sample_data()

# Main content
st.markdown(
    '<div class="main-header">Tariff Tracker Dashboard</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Global overview of tariff events and trade policies</div>',
    unsafe_allow_html=True,
)

# Sample metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        """
    <div class="metric-card">
        <div class="metric-value">{}</div>
        <div class="metric-label">Total Events</div>
    </div>
    """.format(
            sample_data.get("count", len(sample_data.get("events", [])))
        ),
        unsafe_allow_html=True,
    )

with col2:
    # Count unique imposing countries
    imposing_countries = set()
    for event in sample_data.get("events", []):
        if "tariffs_v2" in event and "imposing_country_name" in event["tariffs_v2"]:
            imposing_countries.add(event["tariffs_v2"]["imposing_country_name"])

    st.markdown(
        """
    <div class="metric-card">
        <div class="metric-value">{}</div>
        <div class="metric-label">Imposing Countries</div>
    </div>
    """.format(
            len(imposing_countries)
        ),
        unsafe_allow_html=True,
    )

with col3:
    # Count unique targeted countries
    targeted_countries = set()
    for event in sample_data.get("events", []):
        if "tariffs_v2" in event and "targeted_country_names" in event["tariffs_v2"]:
            for country in event["tariffs_v2"]["targeted_country_names"]:
                targeted_countries.add(country)

    st.markdown(
        """
    <div class="metric-card">
        <div class="metric-value">{}</div>
        <div class="metric-label">Targeted Countries</div>
    </div>
    """.format(
            len(targeted_countries)
        ),
        unsafe_allow_html=True,
    )

with col4:
    # Count unique products
    products = set()
    for event in sample_data.get("events", []):
        if "tariffs_v2" in event and "affected_products" in event["tariffs_v2"]:
            for product in event["tariffs_v2"]["affected_products"]:
                products.add(product)

    st.markdown(
        """
    <div class="metric-card">
        <div class="metric-value">{}</div>
        <div class="metric-label">Affected Products</div>
    </div>
    """.format(
            len(products)
        ),
        unsafe_allow_html=True,
    )

# Global Tariff Heatmap
st.subheader("Global Tariff Heatmap")
map_type = st.radio(
    "Select map type:", ["Imposing Countries", "Targeted Countries"], horizontal=True
)

st.info("World map visualization of tariff events will be implemented here")

# Recent Tariff Events
st.subheader("Recent Tariff Events")
st.info("Event timeline visualization will be implemented here")

# Latest Events table
st.subheader("Latest Events")

# Convert events to a more readable format for the table
event_data = []
for event in sample_data.get("events", [])[:5]:  # Show only the first 5 events
    tariff_info = event.get("tariffs_v2", {})

    event_data.append(
        {
            "Date": tariff_info.get("announcement_date", "N/A"),
            "Imposing Country": tariff_info.get("imposing_country_name", "N/A"),
            "Targeted Countries": ", ".join(
                tariff_info.get("targeted_country_names", ["N/A"])
            ),
            "Measure Type": tariff_info.get("measure_type", "N/A"),
            "Main Rate": f"{tariff_info.get('main_tariff_rate', 'N/A')}%",
            "Relevance": tariff_info.get("relevance_score", "N/A"),
        }
    )

if event_data:
    st.table(event_data)
else:
    st.warning("No events found in the sample data")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit • Data provided by Events API")
