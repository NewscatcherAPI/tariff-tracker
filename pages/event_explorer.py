import streamlit as st
import pandas as pd
import json
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_processing import events_to_dataframe, clean_event_data

# Set page configuration
st.set_page_config(
    page_title="Tariff Tracker - Event Explorer",
    page_icon="🔍",
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
    .event-card {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .event-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .event-meta {
        font-size: 0.9rem;
        color: #4d4d4d;
        margin-bottom: 1rem;
    }
    .event-summary {
        margin-bottom: 1rem;
    }
    .event-details {
        font-size: 0.9rem;
    }
    .tag {
        background-color: #e0e0e0;
        border-radius: 1rem;
        padding: 0.2rem 0.8rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        font-size: 0.8rem;
    }
    .tag-high {
        background-color: #ef476f;
        color: white;
    }
    .tag-medium {
        background-color: #ffd166;
    }
    .tag-low {
        background-color: #06d6a0;
        color: white;
    }
    .article-link {
        display: block;
        margin-top: 0.5rem;
        font-size: 0.9rem;
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
        return {"events": []}
    except json.JSONDecodeError:
        st.error("Error parsing the sample data file")
        return {"events": []}


sample_data = load_sample_data()
events = clean_event_data(sample_data.get("events", []))
events_df = events_to_dataframe(sample_data.get("events", []))

# Main content
st.markdown('<div class="main-header">Event Explorer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Analyze individual tariff events in detail</div>',
    unsafe_allow_html=True,
)

# Sidebar filters
st.sidebar.header("Filters")

# Create filters based on available data
if not events_df.empty:
    # Filter by imposing country
    if "imposing_country" in events_df.columns:
        imposing_countries = sorted(events_df["imposing_country"].unique())
        selected_countries = st.sidebar.multiselect(
            "Imposing Countries", imposing_countries, default=[]
        )
    else:
        selected_countries = []

    # Filter by measure type
    if "measure_type" in events_df.columns:
        measure_types = sorted(events_df["measure_type"].unique())
        selected_measures = st.sidebar.multiselect(
            "Measure Types", measure_types, default=[]
        )
    else:
        selected_measures = []

    # Filter by relevance score
    if "relevance_score" in events_df.columns:
        relevance_scores = sorted(events_df["relevance_score"].unique())
        selected_relevance = st.sidebar.multiselect(
            "Relevance Score", relevance_scores, default=[]
        )
    else:
        selected_relevance = []

    # Apply filters
    filtered_events = events.copy()

    if selected_countries:
        filtered_events = [
            e for e in filtered_events if e["imposing_country"] in selected_countries
        ]

    if selected_measures:
        filtered_events = [
            e for e in filtered_events if e["measure_type"] in selected_measures
        ]

    if selected_relevance:
        filtered_events = [
            e for e in filtered_events if e["relevance_score"] in selected_relevance
        ]

    # Search by keyword
    search_query = st.sidebar.text_input("Search by keyword in summary")
    if search_query:
        filtered_events = [
            e for e in filtered_events if search_query.lower() in e["summary"].lower()
        ]

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"Showing **{len(filtered_events)}** of **{len(events)}** events"
    )
else:
    filtered_events = []
    st.sidebar.warning("No event data available for filtering")

# Display events
if filtered_events:
    # Sort events by date (newest first)
    filtered_events.sort(
        key=lambda x: x["extraction_date"] if x["extraction_date"] else "", reverse=True
    )

    for event in filtered_events:
        with st.container():
            st.markdown(
                f"""
            <div class="event-card">
                <div class="event-title">{event['imposing_country']} → {', '.join(event['targeted_countries'])}</div>
                <div class="event-meta">
                    {event['announcement_date']} • {event['measure_type']} • 
                    <span class="tag tag-{event['relevance_score'].lower() if event['relevance_score'] else 'medium'}">{event['relevance_score']}</span>
                </div>
                <div class="event-summary">{event['summary']}</div>
                <div class="event-details">
                    <strong>Affected Products:</strong> {', '.join(event['affected_products']) if event['affected_products'] else 'N/A'}<br>
                    <strong>Tariff Rates:</strong> {', '.join(event['tariff_rates']) if event['tariff_rates'] else 'N/A'}<br>
                    <strong>Implementation Date:</strong> {event['implementation_date'] if event['implementation_date'] else 'Not specified'}<br>
                    <strong>Industries:</strong> {', '.join(event['affected_industries']) if event['affected_industries'] else 'N/A'}<br>
                </div>
                
                {f'<div class="article-links"><strong>Sources:</strong><br>' + '<br>'.join([f'<a href="{article["link"]}" target="_blank" class="article-link">{article["title"]}</a>' for article in event["articles"]]) + '</div>' if event['articles'] else ''}
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Add expand/collapse for full details if needed
        with st.expander("Show full details"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Key Information")
                st.markdown(f"**Event ID:** {event['id']}")
                st.markdown(f"**Extraction Date:** {event['extraction_date']}")
                st.markdown(f"**Event Type:** {event['event_type']}")
                st.markdown(f"**Global Event Type:** {event['global_event_type']}")

                st.markdown("#### Countries")
                st.markdown(
                    f"**Imposing Country:** {event['imposing_country']} ({event['imposing_country_code']})"
                )
                st.markdown(
                    f"**Targeted Countries:** {', '.join(event['targeted_countries'])}"
                )
                st.markdown(
                    f"**Targeted Country Codes:** {', '.join(event['targeted_country_codes'])}"
                )

            with col2:
                st.markdown("#### Tariff Details")
                st.markdown(f"**Measure Type:** {event['measure_type']}")
                st.markdown(f"**Main Tariff Rate:** {event['main_tariff_rate']}")
                st.markdown(f"**Announcement Date:** {event['announcement_date']}")
                st.markdown(f"**Implementation Date:** {event['implementation_date']}")
                st.markdown(
                    f"**Expiration Date:** {event['expiration_date'] if event['expiration_date'] else 'Not specified'}"
                )
                st.markdown(
                    f"**Policy Objective:** {event['policy_objective'] if event['policy_objective'] else 'Not specified'}"
                )
                st.markdown(
                    f"**Legal Basis:** {event['legal_basis'] if event['legal_basis'] else 'Not specified'}"
                )
else:
    st.info("No events match the selected filters. Try adjusting your filter criteria.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit • Data provided by Events API")
