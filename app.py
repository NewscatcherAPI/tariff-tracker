import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.visualization import create_world_map, create_industry_chart
from utils.data_manager import (
    initialize_session_data,
    get_session_events_data,
    fetch_tariff_events,
    process_events_data,
    get_events_statistics,
)

# Set page configuration
st.set_page_config(
    page_title="Tariff Tracker",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS for styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        color: #4d4d4d;
        margin-bottom: 1.5rem;
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
    .action-card {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .action-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .quick-link {
        text-decoration: none;
        color: #0068c9;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background-color: #e6f2ff;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        display: inline-block;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
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

    # Add data refresh options
    st.subheader("Data Options")

    # Debug mode toggle for development
    debug_mode = st.checkbox("Enable debug mode", key="debug_mode")

    if st.button("Refresh Data"):
        initialize_session_data(force_refresh=True)
        st.success("Data refreshed successfully!")

    # Show last update time if available
    if "last_update_time" in st.session_state:
        st.info(
            f"Last updated: {st.session_state.last_update_time.strftime('%Y-%m-%d %H:%M')}"
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

# Main content
st.markdown(
    '<div class="main-header">Tariff Tracker</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Instant insights into global tariff events and trade policies</div>',
    unsafe_allow_html=True,
)

# Quick action card
with st.container():
    st.markdown(
        """
        <div class="action-card">
            <div class="action-title">Get Started</div>
            <p>View the most recent tariff events or use the API Query Builder to customize your search.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick action buttons in two columns
    col1, col2 = st.columns(2)

    with col1:
        hours_to_look_back = st.slider(
            "Hours to look back:",
            min_value=6,
            max_value=48,
            value=24,
            step=6,
            help="Select how many hours of data to fetch",
        )

    with col2:
        # Add a fetch button
        fetch_data = st.button("Fetch Recent Events", type="primary")

# If the fetch button is pressed, fetch new data
if fetch_data:
    with st.spinner("Fetching recent tariff events..."):
        # Fetch the data with the specified time range
        api_result = fetch_tariff_events(hours_to_look_back=hours_to_look_back)

        # Process the data and update session state
        processed_events, events_df = process_events_data(api_result)
        stats = get_events_statistics(processed_events)

        # Update session state
        st.session_state.api_result = api_result
        st.session_state.processed_events = processed_events
        st.session_state.events_df = events_df
        st.session_state.stats = stats
        st.session_state.events_initialized = True
        st.session_state.last_update_time = datetime.now()

        st.success(
            f"Successfully fetched {len(processed_events)} events from the past {hours_to_look_back} hours!"
        )
else:
    # Initialize data if needed
    if "events_initialized" not in st.session_state:
        with st.spinner("Loading initial data..."):
            initialize_session_data()

# Get the current data from session state
api_result, processed_events, events_df, stats = get_session_events_data()

# Display metrics if we have data
if processed_events:
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{stats['total_events']}</div>
                <div class="metric-label">Total Events</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(stats['imposing_countries'])}</div>
                <div class="metric-label">Imposing Countries</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(stats['targeted_countries'])}</div>
                <div class="metric-label">Targeted Countries</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(stats['affected_products'])}</div>
                <div class="metric-label">Affected Products</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Simple visualization
    st.subheader("Global Tariff Heatmap")
    map_type = st.radio(
        "Select map type:",
        ["Imposing Countries", "Targeted Countries"],
        horizontal=True,
    )

    # Add simple debug info for map data when debug mode is enabled
    if st.session_state.get("debug_mode", False):
        with st.expander("Map Debug Information"):
            st.write("#### Basic Debug Information")
            st.write(f"DataFrame shape: {events_df.shape}")
            st.write(f"DataFrame columns: {events_df.columns.tolist()}")

            if "imposing_country_code" in events_df.columns:
                st.write(
                    f"Unique imposing country codes: {events_df['imposing_country_code'].unique().tolist()}"
                )

            if "targeted_country_codes" in events_df.columns:
                st.write("First few targeted country codes:")
                for i, row in events_df.head(3).iterrows():
                    st.write(f"Row {i}: {row.get('targeted_country_codes')}")

    # Create the map visualization
    map_fig = create_world_map(
        events_df,
        "imposing" if map_type == "Imposing Countries" else "targeted",
        debug=st.session_state.get("debug_mode", False),
    )

    if map_fig:
        st.plotly_chart(map_fig, use_container_width=True)
    else:
        st.info("Not enough data to create the map visualization.")

    # Display recent events table
    st.subheader("Recent Tariff Events")

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

        # Display table
        st.dataframe(events_df[existing_cols], use_container_width=True)

        # Option to download results
        csv = events_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"tariff_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

        # Option to view raw JSON
        with st.expander("View raw API response"):
            st.code(json.dumps(api_result, indent=2), language="json")
    else:
        st.warning("No events found in the data")
else:
    st.error("Failed to load data. Please check the API connection or sample data.")

# Navigation cards section
st.markdown("## Explore Insights")

# Create three columns for navigation cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="action-card">
            <div class="action-title">Tariff Event Explorer</div>
            <p>Browse and filter individual tariff events in detail. View source articles and analyze event information.</p>
            <a href="/Event_Explorer" target="_self" class="quick-link">Explore Events →</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="action-card">
            <div class="action-title">Industry Analysis</div>
            <p>Explore how tariffs impact different industries and product categories. Identify trends across sectors.</p>
            <a href="/Industry_Analysis" target="_self" class="quick-link">Analyze Industries →</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="action-card">
            <div class="action-title">API Query Builder</div>
            <p>Create custom queries to the Events API. Filter by date, countries, industries, and more.</p>
            <a href="/API_Query_Builder" target="_self" class="quick-link">Build Queries →</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit • Data provided by NewsCatcher Events API")
