import streamlit as st
import pandas as pd
import json
import os
import sys
from urllib.parse import urlparse

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
    .article-links {
        margin-top: 1rem;
    }
    .article-link {
        display: block;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
    .article-source {
        color: #6c757d;
        font-size: 0.85rem;
        font-style: italic;
    }
    .sources-heading {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        font-weight: bold;
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


# Helper function to extract domain from URL
def extract_domain(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Remove 'www.' if present
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return "Unknown source"


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
            # Format affected products as comma-separated string
            affected_products = (
                ", ".join(event["affected_products"])
                if isinstance(event["affected_products"], list)
                and event["affected_products"]
                else "N/A"
            )

            # Format tariff rates as comma-separated string
            tariff_rates = (
                ", ".join(event["tariff_rates"])
                if isinstance(event["tariff_rates"], list) and event["tariff_rates"]
                else "N/A"
            )

            # Format industries as comma-separated string
            industries = (
                ", ".join(event["affected_industries"])
                if isinstance(event["affected_industries"], list)
                and event["affected_industries"]
                else "N/A"
            )

            # Format targeted countries
            targeted_countries = (
                ", ".join(event["targeted_countries"])
                if isinstance(event["targeted_countries"], list)
                and event["targeted_countries"]
                else "N/A"
            )

            # Prepare article links HTML with consistent formatting
            article_links_html = ""
            if event.get("articles") and len(event["articles"]) > 0:
                article_links_html = (
                    '<div class="article-links"><p class="sources-heading">Sources:</p>'
                )

                for article in event["articles"]:
                    if article.get("link") and article.get("title"):
                        domain = extract_domain(article["link"])
                        article_links_html += f'<a href="{article["link"]}" target="_blank" class="article-link">{article["title"]} <span class="article-source">({domain})</span></a>'

                article_links_html += "</div>"

            # Create the event card with proper HTML rendering
            event_card_html = f"""
            <div class="event-card">
                <div class="event-title">{event['imposing_country']} → {targeted_countries}</div>
                <div class="event-meta">
                    {event['announcement_date']} • {event['measure_type']} • 
                    <span class="tag tag-{event['relevance_score'].lower() if event['relevance_score'] else 'medium'}">{event['relevance_score']}</span>
                </div>
                <div class="event-summary">{event['summary']}</div>
                <div class="event-details">
                    <strong>Affected Products:</strong> {affected_products}<br>
                    <strong>Tariff Rates:</strong> {tariff_rates}<br>
                    <strong>Implementation Date:</strong> {event['implementation_date'] if event['implementation_date'] else 'Not specified'}<br>
                    <strong>Industries:</strong> {industries}<br>
                </div>
                {article_links_html}
            </div>
            """

            st.markdown(event_card_html, unsafe_allow_html=True)

        # Add expand/collapse for full details if needed
        with st.expander("Show full details"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Key Information")
                st.markdown(f"**Event ID:** {event.get('id', 'N/A')}")
                st.markdown(
                    f"**Extraction Date:** {event.get('extraction_date', 'N/A')}"
                )
                st.markdown(f"**Event Type:** {event.get('event_type', 'N/A')}")
                st.markdown(
                    f"**Global Event Type:** {event.get('global_event_type', 'N/A')}"
                )

                st.markdown("#### Countries")
                st.markdown(
                    f"**Imposing Country:** {event.get('imposing_country', 'N/A')} ({event.get('imposing_country_code', 'N/A')})"
                )
                st.markdown(f"**Targeted Countries:** {targeted_countries}")
                targeted_codes = (
                    ", ".join(event["targeted_country_codes"])
                    if isinstance(event["targeted_country_codes"], list)
                    and event["targeted_country_codes"]
                    else "N/A"
                )
                st.markdown(f"**Targeted Country Codes:** {targeted_codes}")

            with col2:
                st.markdown("#### Tariff Details")
                st.markdown(f"**Measure Type:** {event.get('measure_type', 'N/A')}")
                st.markdown(
                    f"**Main Tariff Rate:** {event.get('main_tariff_rate', 'N/A')}"
                )
                st.markdown(
                    f"**Announcement Date:** {event.get('announcement_date', 'N/A')}"
                )
                st.markdown(
                    f"**Implementation Date:** {event.get('implementation_date', 'N/A')}"
                )
                st.markdown(
                    f"**Expiration Date:** {event.get('expiration_date', 'Not specified') if event.get('expiration_date') else 'Not specified'}"
                )
                st.markdown(
                    f"**Policy Objective:** {event.get('policy_objective', 'Not specified') if event.get('policy_objective') else 'Not specified'}"
                )
                st.markdown(
                    f"**Legal Basis:** {event.get('legal_basis', 'Not specified') if event.get('legal_basis') else 'Not specified'}"
                )

                # Display article sources in the expander as well
                if event.get("articles") and len(event["articles"]) > 0:
                    st.markdown("#### Sources")
                    for article in event["articles"]:
                        if article.get("link") and article.get("title"):
                            domain = extract_domain(article["link"])
                            st.markdown(
                                f"- [{article['title']} ({domain})]({article['link']})"
                            )
else:
    st.info("No events match the selected filters. Try adjusting your filter criteria.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit • Data provided by NewsCatcher Events API")
