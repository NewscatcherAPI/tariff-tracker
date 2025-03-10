import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_processing import events_to_dataframe, clean_event_data
from utils.visualization import (
    create_event_timeline,
    create_world_map,
    create_industry_chart,
    create_measure_type_pie,
)

# Set page configuration
st.set_page_config(
    page_title="Tariff Tracker - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS
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
</style>
""",
    unsafe_allow_html=True,
)


# Load sample data
@st.cache_data
def load_sample_data():
    file_path = os.path.join("data", "sample_tariff_events.json")
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        st.error(f"Sample data file not found at {file_path}")
        # Return minimal data structure to prevent errors
        return {"events": []}
    except json.JSONDecodeError:
        st.error("Error parsing the sample data file")
        return {"events": []}


# When loading the data, provide fallbacks for empty data
sample_data = load_sample_data()

# Print the sample data for debugging
if st.session_state.get("debug_mode", False):
    st.write("Raw sample data:", sample_data)

# Apply cleanup to events
events = clean_event_data(sample_data.get("events", []))

# Print cleaned events for debugging
if st.session_state.get("debug_mode", False):
    st.write("Cleaned events:", events)

# Convert to DataFrame
events_df = events_to_dataframe(events)

# After getting the DataFrame, apply country standardization
# Import here to avoid circular imports
from utils.data_processing import standardize_countries_in_dataframe

events_df = standardize_countries_in_dataframe(events_df)

# Enable this for debugging
if st.session_state.get("debug_mode", False):
    st.write("Data frame after standardization:", events_df)

# Temporary data debug toggle in sidebar
with st.sidebar:
    st.checkbox("Enable debug mode", key="debug_mode")

# Main content
st.markdown(
    '<div class="main-header">Tariff Tracker Dashboard</div>', unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-header">Global overview of tariff events and trade policies</div>',
    unsafe_allow_html=True,
)

# Sample metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-value">{sample_data.get("count", len(sample_data.get("events", [])))}</div>
        <div class="metric-label">Total Events</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    # Count unique imposing countries
    imposing_countries = (
        events_df["imposing_country"].nunique() if not events_df.empty else 0
    )

    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-value">{imposing_countries}</div>
        <div class="metric-label">Imposing Countries</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col3:
    # Count unique targeted countries
    targeted_countries = set()
    if not events_df.empty and "targeted_countries" in events_df.columns:
        for countries_str in events_df["targeted_countries"]:
            if isinstance(countries_str, str) and countries_str:
                targeted_countries.update([c.strip() for c in countries_str.split(",")])

    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-value">{len(targeted_countries)}</div>
        <div class="metric-label">Targeted Countries</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col4:
    # Count unique products
    products = set()
    if not events_df.empty and "affected_products" in events_df.columns:
        for products_str in events_df["affected_products"]:
            if isinstance(products_str, str) and products_str:
                products.update([p.strip() for p in products_str.split(",")])

    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-value">{len(products)}</div>
        <div class="metric-label">Affected Products</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# Visualizations
# World map visualization
st.subheader("Global Tariff Heatmap")
map_type = st.radio(
    "Select map type:", ["Imposing Countries", "Targeted Countries"], horizontal=True
)

# Add debug info for map data
if st.session_state.get("debug_mode", False):
    with st.expander("Map Data Debug Info"):
        if "imposing_country_code" in events_df.columns:
            st.write(
                "Imposing country codes:", events_df["imposing_country_code"].unique()
            )
        else:
            st.write("No imposing_country_code column found")

        if "targeted_country_codes" in events_df.columns:
            st.write("Sample targeted country codes:")
            for i, codes in enumerate(events_df["targeted_country_codes"].head()):
                st.write(f"Row {i}: {codes}, Type: {type(codes)}")
        else:
            st.write("No targeted_country_codes column found")

# Create the map visualization
map_fig = create_world_map(
    events_df, "imposing" if map_type == "Imposing Countries" else "targeted"
)

if map_fig:
    st.plotly_chart(map_fig, use_container_width=True)
else:
    st.info("Not enough data to create the map visualization.")

# Two-column layout for additional charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Industry Distribution")
    industry_fig = create_industry_chart(events_df)

    if industry_fig:
        st.plotly_chart(industry_fig, use_container_width=True)
    else:
        st.info("Not enough industry data for visualization.")

with col2:
    st.subheader("Tariff Measure Types")
    measure_fig = create_measure_type_pie(events_df)

    if measure_fig:
        st.plotly_chart(measure_fig, use_container_width=True)
    else:
        st.info("Not enough measure type data for visualization.")

# Recent events timeline
st.subheader("Recent Tariff Events Timeline")
timeline_fig = create_event_timeline(events_df)

if timeline_fig:
    st.plotly_chart(timeline_fig, use_container_width=True)
else:
    st.info("Not enough timeline data for visualization.")

# Sample events table
st.subheader("Latest Events")

if not events_df.empty:
    # Show only essential columns for the table view
    display_cols = [
        "announcement_date",
        "imposing_country",
        "targeted_countries",
        "measure_type",
        "main_tariff_rate",
        "relevance_score",
    ]

    # Filter for display columns that actually exist in the dataframe
    existing_cols = [col for col in display_cols if col in events_df.columns]

    # Display table with the top 5 events
    st.dataframe(events_df[existing_cols].head(5), use_container_width=True)
else:
    st.warning("No events found in the sample data")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit • Data provided by Events API")


def debug_sample_data():
    """
    Check the contents of the sample data file and display debug information.
    """
    try:
        file_path = os.path.join("data", "sample_tariff_events.json")

        # Check if file exists
        if not os.path.exists(file_path):
            st.error(f"Sample data file not found at {file_path}")
            return

        # Get file size
        file_size = os.path.getsize(file_path)
        st.write(f"Sample data file size: {file_size} bytes")

        # Read the file content
        with open(file_path, "r") as file:
            content = file.read()

        # Try to parse JSON
        try:
            data = json.loads(content)

            # Check structure
            if "events" in data:
                st.write(f"Number of events in file: {len(data['events'])}")

                if data["events"]:
                    # Check first event
                    first_event = data["events"][0]
                    st.write("First event keys:", list(first_event.keys()))

                    if "tariffs_v2" in first_event:
                        st.write(
                            "First event tariffs_v2 keys:",
                            list(first_event["tariffs_v2"].keys()),
                        )
                    else:
                        st.warning("No tariffs_v2 data in first event")
                else:
                    st.warning("Events array is empty")
            else:
                st.warning("No 'events' key in sample data")
                st.write("Top-level keys:", list(data.keys()))

        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON: {e}")
            # Show first 500 chars of the file
            st.text(f"First 500 characters of file:\n{content[:500]}...")

    except Exception as e:
        st.error(f"Error checking sample data: {e}")


# In the dashboard, add:
if st.session_state.get("debug_mode", False):
    with st.expander("Debug Sample Data"):
        debug_sample_data()


def debug_map_data(events_df):
    """
    Debug the data used for map visualization.
    """
    if st.session_state.get("debug_mode", False):
        with st.expander("Debug Map Data"):
            # Check DataFrame basics
            st.subheader("DataFrame Info")
            st.write(f"Shape: {events_df.shape}")
            st.write(f"Columns: {events_df.columns.tolist()}")

            # Check country columns
            st.subheader("Country Data")

            if "imposing_country" in events_df.columns:
                imposing_countries = (
                    events_df["imposing_country"].value_counts().reset_index()
                )
                imposing_countries.columns = ["Country", "Count"]
                st.write("Imposing Countries:")
                st.dataframe(imposing_countries)

            if "imposing_country_code" in events_df.columns:
                imposing_codes = (
                    events_df["imposing_country_code"].value_counts().reset_index()
                )
                imposing_codes.columns = ["Country Code", "Count"]
                st.write("Imposing Country Codes:")
                st.dataframe(imposing_codes)

            if "targeted_countries" in events_df.columns:
                st.write("Sample Targeted Countries:")
                for i, row in events_df.iloc[:5].iterrows():
                    st.write(
                        f"Row {i}: {row.get('targeted_countries')}, Type: {type(row.get('targeted_countries'))}"
                    )

            if "targeted_country_codes" in events_df.columns:
                st.write("Sample Targeted Country Codes:")
                for i, row in events_df.iloc[:5].iterrows():
                    st.write(
                        f"Row {i}: {row.get('targeted_country_codes')}, Type: {type(row.get('targeted_country_codes'))}"
                    )


# Use this after loading the data and before creating visualizations
debug_map_data(events_df)
