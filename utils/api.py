import requests
from typing import Dict, List, Union, Optional, Any
import streamlit as st
from datetime import datetime, timedelta
import json


def get_api_key() -> Optional[str]:
    """
    Retrieve the API key from Streamlit secrets.

    Returns:
        Optional[str]: The API key if found, None otherwise.
    """
    try:
        return st.secrets["api"]["key"]
    except KeyError:
        return None


def format_api_request(
    event_type: str = "tariffs_v2",
    extraction_date_range: Optional[Dict[str, str]] = None,
    event_date_range: Optional[Dict[str, str]] = None,
    imposing_countries: Optional[List[str]] = None,
    targeted_countries: Optional[List[str]] = None,
    measure_types: Optional[List[str]] = None,
    affected_industries: Optional[List[str]] = None,
    min_tariff_rate: Optional[float] = None,
    keywords: Optional[List[str]] = None,
    include_articles: bool = True,
    additional_article_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Format the Events API request parameters.

    Args:
        event_type: Type of event to query for (default: tariffs_v2)
        extraction_date_range: Dict with "gte" and "lte" date strings for extraction dates
        event_date_range: Dict with "gte" and "lte" date strings for event dates
        imposing_countries: List of imposing country codes to filter by
        targeted_countries: List of targeted country codes to filter by
        measure_types: List of measure types to filter by
        affected_industries: List of industry categories to filter by
        min_tariff_rate: Minimum tariff rate to filter by
        keywords: List of keywords to search for in the event summary
        include_articles: Whether to include article data in response
        additional_article_fields: Additional article fields to include

    Returns:
        Dict[str, Any]: Formatted request parameters
    """
    # Set up default extraction date range if not provided (last 30 days)
    if extraction_date_range is None:
        extraction_date_range = {"gte": "now-30d", "lte": "now"}

    # Build request parameters
    params: Dict[str, Any] = {
        "event_type": event_type,
        "attach_articles_data": include_articles,
        "additional_filters": {},
    }

    # Add extraction date range
    if extraction_date_range:
        params["additional_filters"]["extraction_date"] = extraction_date_range

    # Add event date range if provided
    if event_date_range:
        params["additional_filters"]["event_date"] = event_date_range

    # Add imposing country filters if provided
    if imposing_countries and len(imposing_countries) > 0:
        if len(imposing_countries) == 1:
            params["additional_filters"]["tariffs_v2.imposing_country_code"] = (
                imposing_countries[0]
            )
        else:
            params["additional_filters"][
                "tariffs_v2.imposing_country_code"
            ] = imposing_countries

    # Add targeted country filters if provided
    if targeted_countries and len(targeted_countries) > 0:
        if len(targeted_countries) == 1:
            params["additional_filters"]["tariffs_v2.targeted_country_codes"] = (
                targeted_countries[0]
            )
        else:
            params["additional_filters"][
                "tariffs_v2.targeted_country_codes"
            ] = targeted_countries

    # Add measure type filters if provided
    if measure_types and len(measure_types) > 0:
        if len(measure_types) == 1:
            params["additional_filters"]["tariffs_v2.measure_type"] = measure_types[0]
        else:
            params["additional_filters"]["tariffs_v2.measure_type"] = measure_types

    # Add industry filters if provided
    if affected_industries and len(affected_industries) > 0:
        if len(affected_industries) == 1:
            params["additional_filters"]["tariffs_v2.affected_industries"] = (
                affected_industries[0]
            )
        else:
            params["additional_filters"][
                "tariffs_v2.affected_industries"
            ] = affected_industries

    # Add minimum tariff rate filter if provided
    if min_tariff_rate is not None:
        params["additional_filters"]["tariffs_v2.main_tariff_rate"] = {
            "gte": min_tariff_rate
        }

    # Add keyword filters if provided
    if keywords and len(keywords) > 0:
        params["additional_filters"]["tariffs_v2.summary"] = " ".join(keywords)

    # Add additional article fields if provided
    if include_articles and additional_article_fields:
        params["additional_article_fields"] = additional_article_fields

    return params


def call_events_api(
    params: Dict[str, Any], api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Call the Events API with the provided parameters.

    Args:
        params: API request parameters
        api_key: API key for authentication

    Returns:
        Dict[str, Any]: API response data or error message
    """
    if not api_key:
        api_key = get_api_key()

    if not api_key:
        return {"error": "API key not found. Please set it in the Streamlit secrets."}

    # API endpoint
    url = "https://events.newscatcherapi.xyz/api/events_search"

    # Set headers
    headers = {"x-api-token": api_key, "Content-Type": "application/json"}

    try:
        # Make API call
        response = requests.post(url, headers=headers, json=params)

        # Check for successful response
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API request failed with status code {response.status_code}",
                "details": response.text,
            }
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse API response as JSON"}


def check_api_health(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Check the health status of the Events API.

    Args:
        api_key: API key for authentication

    Returns:
        Dict[str, Any]: API health status
    """
    if not api_key:
        api_key = get_api_key()

    if not api_key:
        return {"error": "API key not found. Please set it in the Streamlit secrets."}

    # API endpoint
    url = "https://events.newscatcherapi.xyz/api/health"

    # Set headers
    headers = {"x-api-token": api_key}

    try:
        # Make API call
        response = requests.get(url, headers=headers)

        # Check for successful response
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API health check failed with status code {response.status_code}",
                "details": response.text,
            }
    except requests.exceptions.RequestException as e:
        return {"error": f"Health check request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse API response as JSON"}


def get_subscription_info(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about the user's API subscription.

    Args:
        api_key: API key for authentication

    Returns:
        Dict[str, Any]: Subscription information
    """
    if not api_key:
        api_key = get_api_key()

    if not api_key:
        return {"error": "API key not found. Please set it in the Streamlit secrets."}

    # API endpoint
    url = "https://events.newscatcherapi.xyz/api/subscription"

    # Set headers
    headers = {"x-api-token": api_key}

    try:
        # Make API call
        response = requests.get(url, headers=headers)

        # Check for successful response
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Failed to get subscription info with status code {response.status_code}",
                "details": response.text,
            }
    except requests.exceptions.RequestException as e:
        return {"error": f"Subscription info request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse API response as JSON"}


def get_event_fields(
    event_type: str = "tariffs_v2", api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the available fields for a specific event type.

    Args:
        event_type: The event type to get fields for
        api_key: API key for authentication

    Returns:
        Dict[str, Any]: Available event fields and their descriptions
    """
    if not api_key:
        api_key = get_api_key()

    if not api_key:
        return {"error": "API key not found. Please set it in the Streamlit secrets."}

    # API endpoint
    url = "https://events.newscatcherapi.xyz/api/events_info/get_event_fields"

    # Set headers
    headers = {"x-api-token": api_key}

    # Set parameters
    params = {"event_type": event_type}

    try:
        # Make API call
        response = requests.get(url, headers=headers, params=params)

        # Check for successful response
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Failed to get event fields with status code {response.status_code}",
                "details": response.text,
            }
    except requests.exceptions.RequestException as e:
        return {"error": f"Event fields request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse API response as JSON"}
