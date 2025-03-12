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

# Ensure debug mode is set in session state but not displayed in UI
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

# Sidebar options
with st.sidebar:
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

# Create the map visualization - using session state for debug mode
map_fig = create_world_map(
    events_df,
    "imposing" if map_type == "Imposing Countries" else "targeted",
    debug=st.session_state.debug_mode,  # Use debug from session state
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
