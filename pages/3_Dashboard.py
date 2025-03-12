import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.visualization import (
    create_event_timeline,
    create_world_map,
    create_industry_chart,
    create_measure_type_pie,
)
from utils.data_manager import get_session_events_data, initialize_session_data


# Import the map debug component
# In a production environment, you might want to move this to utils
def add_map_debug_information(st, events_df, debug_mode=False):
    """
    Add debug information for the world map visualization.

    Args:
        st: Streamlit instance
        events_df: DataFrame containing event data
        debug_mode: Whether debug mode is enabled
    """
    if debug_mode:
        with st.expander("Map Debug Information"):
            st.write("#### Debug Information")
            st.write("This section helps diagnose the world map issue")

            # Check what's in the DataFrame
            st.write("DataFrame Info:")
            st.write(f"- Shape: {events_df.shape}")
            st.write(f"- Columns: {events_df.columns.tolist()}")

            # Check for country code columns
            if "imposing_country_code" in events_df.columns:
                unique_imposers = events_df["imposing_country_code"].unique().tolist()
                st.write(f"- Unique imposing country codes: {unique_imposers}")
            else:
                st.write("- No imposing_country_code column found")

            if "targeted_country_codes" in events_df.columns:
                st.write("- targeted_country_codes column exists")
                # Show the first few values to understand the format
                st.write("- Sample of targeted_country_codes:")
                for i, row in events_df.head(3).iterrows():
                    st.write(
                        f"  - Row {i}: {row.get('targeted_country_codes')} (Type: {type(row.get('targeted_country_codes'))})"
                    )
            else:
                st.write("- No targeted_country_codes column found")

            # Try creating a direct test map with ISO-3 codes
            st.write("### ISO-3 Test Map")

            # Create test data with ISO-3 codes
            import plotly.graph_objects as go

            # Convert data for test
            iso_codes_path = os.path.join("data", "country_codes_iso_3166.csv")
            try:
                iso_codes_df = pd.read_csv(iso_codes_path)
                iso2_to_iso3 = {
                    row["Alpha-2 code"].strip(): row["Alpha-3 code"].strip()
                    for _, row in iso_codes_df.iterrows()
                }
                iso2_to_iso3["EU"] = "EUR"  # Add EU mapping
            except Exception as e:
                st.error(f"Error loading ISO codes: {e}")
                iso2_to_iso3 = {
                    "US": "USA",
                    "CN": "CHN",
                    "CA": "CAN",
                    "MX": "MEX",
                    "EU": "EUR",
                    "GB": "GBR",
                    "JP": "JPN",
                    "KR": "KOR",
                    "IN": "IND",
                    "NG": "NGA",
                    "CH": "CHE",
                }

            # Create test data with ISO-3 codes
            test_data = [
                {
                    "country_code": "US",
                    "count": 5,
                    "iso3": iso2_to_iso3.get("US", "USA"),
                },
                {
                    "country_code": "CN",
                    "count": 3,
                    "iso3": iso2_to_iso3.get("CN", "CHN"),
                },
                {
                    "country_code": "CA",
                    "count": 3,
                    "iso3": iso2_to_iso3.get("CA", "CAN"),
                },
                {
                    "country_code": "MX",
                    "count": 2,
                    "iso3": iso2_to_iso3.get("MX", "MEX"),
                },
                {
                    "country_code": "GB",
                    "count": 2,
                    "iso3": iso2_to_iso3.get("GB", "GBR"),
                },
                {
                    "country_code": "DE",
                    "count": 4,
                    "iso3": iso2_to_iso3.get("DE", "DEU"),
                },
                {
                    "country_code": "FR",
                    "count": 1,
                    "iso3": iso2_to_iso3.get("FR", "FRA"),
                },
            ]
            test_df = pd.DataFrame(test_data)

            st.write("Test data for map:")
            st.write(test_df)

            # Create a direct choropleth map with test data
            try:
                test_fig = go.Figure(
                    data=go.Choropleth(
                        locations=test_df["iso3"],
                        z=test_df["count"],
                        colorscale="Blues",
                        marker_line_color="white",
                        marker_line_width=0.5,
                        colorbar_title="Test Count",
                    )
                )

                test_fig.update_layout(
                    title="Test Map with ISO-3 Codes",
                    height=400,
                    geo=dict(
                        showframe=False,
                        showcoastlines=True,
                        projection_type="natural earth",
                        showland=True,
                        landcolor="lightgray",
                    ),
                )

                st.plotly_chart(test_fig, use_container_width=True)
                st.info(
                    "If this test map shows colored countries but the actual map doesn't, the issue is in the data processing."
                )
            except Exception as e:
                st.error(f"Error creating test map: {e}")


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

# Initialize data if needed
if "events_initialized" not in st.session_state:
    with st.spinner("Loading initial data..."):
        initialize_session_data()

# Get the current data from session state
api_result, events, events_df, stats = get_session_events_data()

# Temporary data debug toggle in sidebar
with st.sidebar:
    st.checkbox("Enable debug mode", key="debug_mode")

    # Add refresh button
    if st.button("Refresh Data"):
        with st.spinner("Refreshing data..."):
            initialize_session_data(force_refresh=True)
            st.success("Data refreshed successfully!")
            # Reload the data after refresh
            api_result, events, events_df, stats = get_session_events_data()

    # Show last update time if available
    if "last_update_time" in st.session_state:
        st.info(
            f"Last updated: {st.session_state.last_update_time.strftime('%Y-%m-%d %H:%M')}"
        )

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
        <div class="metric-value">{len(events)}</div>
        <div class="metric-label">Total Events</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    # Count unique imposing countries
    imposing_countries = len(stats["imposing_countries"])

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
    targeted_countries = len(stats["targeted_countries"])

    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-value">{targeted_countries}</div>
        <div class="metric-label">Targeted Countries</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col4:
    # Count unique products
    products = len(stats["affected_products"])

    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-value">{products}</div>
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

# Add debug info for map data when debug mode is enabled
add_map_debug_information(st, events_df, st.session_state.get("debug_mode", False))

# Create the map visualization
map_fig = create_world_map(
    events_df,
    "imposing" if map_type == "Imposing Countries" else "targeted",
    debug=st.session_state.get("debug_mode", False),  # Pass debug flag
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
    st.warning("No events found in the data")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit • Data provided by NewsCatcher Events API")
