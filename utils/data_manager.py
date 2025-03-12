import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

from utils.api import format_api_request, call_events_api, get_api_key

# Import the data processing functions directly to avoid circular imports
from utils.data_processing import (
    clean_event_data,
    events_to_dataframe,
    calculate_event_statistics,
    standardize_countries_in_dataframe,
)


# Cache the API connection as a resource
@st.cache_resource
def get_api_connection():
    """
    Create and cache an API connection.

    Returns:
        The API key for the connection or None if not available
    """
    return get_api_key()


# Cache data loading functions with st.cache_data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_tariff_events(
    hours_to_look_back: int = 24,
    event_type: str = "tariffs_v2",
    include_articles: bool = True,
    imposing_countries: Optional[List[str]] = None,
    targeted_countries: Optional[List[str]] = None,
    measure_types: Optional[List[str]] = None,
    min_tariff_rate: Optional[float] = None,
    keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Fetch tariff events from the API with caching.

    Args:
        hours_to_look_back: Number of hours to look back for events
        event_type: Type of event to query (default: tariffs_v2)
        include_articles: Whether to include article data in the response
        imposing_countries: List of imposing country codes to filter by
        targeted_countries: List of targeted country codes to filter by
        measure_types: List of measure types to filter by
        min_tariff_rate: Minimum tariff rate to filter by
        keywords: List of keywords to search for in the event summary

    Returns:
        Dictionary containing API response data or sample data if API call fails
    """
    # Format the request parameters
    date_range = {"gte": f"now-{hours_to_look_back}h", "lte": "now"}
    api_request = format_api_request(
        event_type=event_type,
        extraction_date_range=date_range,
        include_articles=include_articles,
        imposing_countries=imposing_countries,
        targeted_countries=targeted_countries,
        measure_types=measure_types,
        min_tariff_rate=min_tariff_rate,
        keywords=keywords,
    )

    # Get cached API connection
    api_key = get_api_connection()

    if not api_key:
        st.warning(
            "⚠️ Using sample data because no API key is configured. Add your API key to Streamlit secrets for live data."
        )
        return load_sample_data()

    # Call the API
    api_result = call_events_api(api_request, api_key)

    # Check if there was an error
    if "error" in api_result:
        st.error(f"Error: {api_result['error']}")
        if "details" in api_result:
            st.code(api_result["details"])
        # Fall back to sample data
        st.warning("Falling back to sample data.")
        return load_sample_data()

    return api_result


@st.cache_data
def load_sample_data() -> Dict[str, Any]:
    """
    Load sample tariff events data from JSON file with caching.

    Returns:
        Dictionary containing events data or empty dict if file not found
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


@st.cache_data
def process_events_data(
    api_result: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    """
    Process the event data from API result with caching.

    Args:
        api_result: Dictionary containing API response data

    Returns:
        Tuple containing processed events list and events DataFrame
    """
    if not api_result or "events" not in api_result:
        return [], pd.DataFrame()

    events = api_result.get("events", [])

    if not events:
        return [], pd.DataFrame()

    # Clean and process events
    processed_events = clean_event_data(events)

    # Convert to DataFrame
    events_df = events_to_dataframe(processed_events)

    # Important: Ensure country code columns exist and are in the correct format for mapping

    # Check if imposing_country_code exists
    if "imposing_country_code" not in events_df.columns and processed_events:
        # Extract codes from processed events
        events_df["imposing_country_code"] = [
            e.get("imposing_country_code", "") for e in processed_events
        ]

    # Check if targeted_country_codes exists
    if "targeted_country_codes" not in events_df.columns and processed_events:
        # Extract codes from processed events
        events_df["targeted_country_codes"] = [
            e.get("targeted_country_codes", []) for e in processed_events
        ]

    # Standardize countries - but keep country code formats intact
    events_df = standardize_countries_in_dataframe(events_df)

    return processed_events, events_df


@st.cache_data
def get_events_statistics(processed_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics from processed events with caching.

    Args:
        processed_events: List of processed event dictionaries

    Returns:
        Dictionary of statistics
    """
    return calculate_event_statistics(processed_events)


def initialize_session_data(force_refresh: bool = False) -> None:
    """
    Initialize or refresh session data from the API or sample data.

    Args:
        force_refresh: Whether to force a refresh of the data
    """
    # Check if we need to initialize or refresh the data
    if "events_initialized" not in st.session_state or force_refresh:
        # Fetch recent events (last 24 hours by default)
        api_result = fetch_tariff_events(hours_to_look_back=24)

        # Process the data
        processed_events, events_df = process_events_data(api_result)

        # Calculate statistics
        stats = get_events_statistics(processed_events)

        # Store in session state
        st.session_state.api_result = api_result
        st.session_state.processed_events = processed_events
        st.session_state.events_df = events_df
        st.session_state.stats = stats
        st.session_state.events_initialized = True
        st.session_state.last_update_time = datetime.now()


def get_session_events_data() -> (
    Tuple[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame, Dict[str, Any]]
):
    """
    Get the current events data from session state.

    Returns:
        Tuple containing API result, processed events, events DataFrame, and statistics
    """
    # Initialize data if needed
    if "events_initialized" not in st.session_state:
        initialize_session_data()

    return (
        st.session_state.api_result,
        st.session_state.processed_events,
        st.session_state.events_df,
        st.session_state.stats,
    )


def update_session_data_with_custom_query(api_result: Dict[str, Any]) -> None:
    """
    Update session data with custom query results.

    Args:
        api_result: Dictionary containing API response data from custom query
    """
    # Process the new data
    processed_events, events_df = process_events_data(api_result)

    # Calculate statistics
    stats = get_events_statistics(processed_events)

    # Update session state
    st.session_state.api_result = api_result
    st.session_state.processed_events = processed_events
    st.session_state.events_df = events_df
    st.session_state.stats = stats
    st.session_state.events_initialized = True
    st.session_state.last_update_time = datetime.now()
