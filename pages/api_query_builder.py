import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import pycountry
from typing import Dict, List, Any, Optional, Union, Tuple

from utils.api import format_api_request, call_events_api, check_api_health

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api import format_api_request, call_events_api
from utils.data_processing import events_to_dataframe, clean_event_data

# Set page configuration
st.set_page_config(
    page_title="Tariff Tracker - API Query Builder",
    page_icon="🔌",
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
    .api-card {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .api-header {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .code-block {
        background-color: #f8f9fa;
        border-radius: 0.3rem;
        padding: 1rem;
        font-family: monospace;
        overflow-x: auto;
        margin-bottom: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Main content
st.markdown('<div class="main-header">API Query Builder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Construct custom queries to the Events API</div>',
    unsafe_allow_html=True,
)

# API configuration section
with st.container():
    st.markdown(
        """
    <div class="api-card">
        <div class="api-header">API Configuration</div>
        <p>
            Configure your query parameters to fetch tariff events from the Events API.
            You can filter by date range, countries, and other criteria.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# Query parameters form
st.subheader("Query Parameters")

col1, col2 = st.columns(2)

with col1:
    # Date type selection
    st.markdown("#### Date Selection")
    date_type = st.radio(
        "Select date type to filter by:",
        ["Extraction Date", "Announcement Date", "Implementation Date"],
    )

    date_field = "extraction_date"
    if date_type == "Announcement Date":
        date_field = "tariffs_v2.announcement_date"
    elif date_type == "Implementation Date":
        date_field = "tariffs_v2.implementation_date"

    # Date range selection
    date_option = st.radio(
        "Select date range type:", ["Last N days", "Custom date range"]
    )

    date_range = {}
    if date_option == "Last N days":
        days_ago = st.slider("Number of days to look back:", 1, 365, 30)
        date_range = {"gte": f"now-{days_ago}d", "lte": "now"}
    else:
        col1a, col1b = st.columns(2)
        with col1a:
            start_date = st.date_input(
                "Start date:", datetime.now() - timedelta(days=30)
            )
        with col1b:
            end_date = st.date_input("End date:", datetime.now())

        date_range = {
            "gte": start_date.strftime("%Y-%m-%d"),
            "lte": end_date.strftime("%Y-%m-%d"),
        }

    # Event type - Currently only tariffs_v2 is supported
    st.markdown("#### Event Type")
    event_type = st.selectbox("Select event type:", ["tariffs_v2"], index=0)

with col2:
    # Country selection
    st.markdown("#### Countries")

    # Get list of countries for the selector
    countries = sorted(
        [(country.alpha_2, country.name) for country in pycountry.countries],
        key=lambda x: x[1],
    )
    countries.append(("EU", "European Union"))  # Add EU manually

    country_options = [f"{code}: {name}" for code, name in countries]

    # Country filter type
    country_filter_type = st.radio(
        "Filter by:", ["Imposing Country", "Targeted Country", "Both"]
    )

    # Imposing countries
    imposing_countries = []
    if country_filter_type in ["Imposing Country", "Both"]:
        selected_imposing = st.multiselect(
            "Select imposing countries (optional):",
            options=country_options,
            key="imposing_countries",
        )
        imposing_countries = [c.split(":")[0].strip() for c in selected_imposing]

    # Targeted countries
    targeted_countries = []
    if country_filter_type in ["Targeted Country", "Both"]:
        selected_targeted = st.multiselect(
            "Select targeted countries (optional):",
            options=country_options,
            key="targeted_countries",
        )
        targeted_countries = [c.split(":")[0].strip() for c in selected_targeted]

    # Measure type selection
    st.markdown("#### Measure Type")
    measure_options = [
        "new tariff",
        "tariff increase",
        "tariff reduction",
        "retaliatory tariff",
        "import ban",
        "quota",
        "other trade restriction",
    ]
    selected_measures = st.multiselect(
        "Select measure types (optional):", options=measure_options
    )

    # Tariff rate range
    st.markdown("#### Tariff Rate")
    min_rate = st.slider("Minimum tariff rate (%):", 0, 100, 0)

    # Keywords for summary search
    st.markdown("#### Keywords in Summary")
    keywords = st.text_input("Enter keywords to search in summary (space-separated):")

    # Article data options
    st.markdown("#### Article Data")
    include_articles = st.checkbox("Include article data", value=True)

    if include_articles:
        st.markdown("##### Additional Article Fields")
        article_field_options = [
            "description",
            "content",
            "published_date",
            "published_date_precision",
            "author",
            "authors",
            "journalists",
            "domain_url",
            "full_domain_url",
            "name_source",
            "extraction_data.parent_url",
            "is_headline",
            "paid_content",
            "rights",
            "rank",
            "is_opinion",
            "language",
            "word_count",
            "twitter_account",
            "all_links",
            "all_domain_links",
            "nlp.theme",
            "nlp.summary",
            "nlp.sentiment",
            "nlp.ner_PER",
            "nlp.ner_ORG",
            "nlp.ner_MISC",
            "nlp.ner_LOC",
        ]
        additional_article_fields = st.multiselect(
            "Select additional article fields to include:",
            options=article_field_options,
        )

# Generate API request preview
st.subheader("API Request Preview")

# Format the request
api_request = format_api_request(
    event_type=event_type,
    extraction_date_range=date_range if date_field == "extraction_date" else None,
    event_date_range=date_range if date_field.startswith("tariffs_v2") else None,
    imposing_countries=imposing_countries if imposing_countries else None,
    targeted_countries=targeted_countries if targeted_countries else None,
    measure_types=selected_measures if selected_measures else None,
    min_tariff_rate=min_rate if min_rate > 0 else None,
    keywords=keywords.split() if keywords else None,
    include_articles=include_articles,
    additional_article_fields=(
        additional_article_fields
        if include_articles and additional_article_fields
        else None
    ),
)

# Override the date field if not extraction_date
if date_field != "extraction_date" and "additional_filters" in api_request:
    # Move the date range to the correct field
    if "extraction_date" in api_request["additional_filters"]:
        api_request["additional_filters"][date_field] = api_request[
            "additional_filters"
        ].pop("extraction_date")

# Display the request JSON
st.code(json.dumps(api_request, indent=2), language="json")

# Execute API query
st.subheader("Execute Query")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("Click the button to execute this query against the Events API.")

with col2:
    query_button = st.button("Execute Query", type="primary")

# Results section
if query_button:
    with st.spinner("Querying Events API..."):
        # First check API health
        use_sample = False
        api_key = None

        try:
            api_key = st.secrets.get("api", {}).get("key")
        except:
            use_sample = True

        if not api_key:
            use_sample = True

        if not use_sample:
            # Check API health
            health_result = check_api_health(api_key)
            if "error" in health_result:
                st.error(f"API health check failed: {health_result['error']}")
                use_sample = True
            elif health_result.get("message") != "Healthy":
                st.warning(
                    f"API health status: {health_result.get('message', 'Unknown')}"
                )

        if use_sample:
            st.warning(
                "⚠️ Using sample data because no API key is configured or API is not available. For live data, add your API key to Streamlit secrets."
            )

            # Load sample data
            with open(os.path.join("data", "sample_tariff_events.json"), "r") as file:
                api_result = json.load(file)
        else:
            # Call the actual API
            api_result = call_events_api(api_request)

    # Display results
    st.subheader("Query Results")

    if "error" in api_result:
        st.error(f"Error: {api_result['error']}")
        if "details" in api_result:
            st.code(api_result["details"])
    else:
        st.success(
            f"Query successful! Retrieved {api_result.get('count', len(api_result.get('events', [])))} events."
        )

        # Process results
        events = api_result.get("events", [])
        if events:
            # Create DataFrame
            events_df = events_to_dataframe(events)

            # Display summary
            st.markdown("#### Results Overview")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Events", len(events))

            with col2:
                imposing_countries = set()
                for event in events:
                    if (
                        "tariffs_v2" in event
                        and "imposing_country_name" in event["tariffs_v2"]
                    ):
                        imposing_countries.add(
                            event["tariffs_v2"]["imposing_country_name"]
                        )
                st.metric("Imposing Countries", len(imposing_countries))

            with col3:
                targeted_countries = set()
                for event in events:
                    if (
                        "tariffs_v2" in event
                        and "targeted_country_names" in event["tariffs_v2"]
                    ):
                        for country in event["tariffs_v2"]["targeted_country_names"]:
                            targeted_countries.add(country)
                st.metric("Targeted Countries", len(targeted_countries))

            # Display events table
            st.markdown("#### Events Table")

            # Select columns to display
            if not events_df.empty:
                display_cols = [
                    "announcement_date",
                    "imposing_country",
                    "targeted_countries",
                    "measure_type",
                    "main_tariff_rate",
                    "relevance_score",
                    "summary",
                ]
                existing_cols = [
                    col for col in display_cols if col in events_df.columns
                ]

                st.dataframe(events_df[existing_cols], use_container_width=True)

                # Option to download results
                csv = events_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download results as CSV",
                    data=csv,
                    file_name=f"tariff_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

                # Raw response
                with st.expander("View raw API response"):
                    st.code(json.dumps(api_result, indent=2), language="json")
            else:
                st.warning("No events found in the API response.")
        else:
            st.warning("No events found in the API response.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit • Data provided by Events API")
