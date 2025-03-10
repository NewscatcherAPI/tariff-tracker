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
# In pages/dashboard.py, modify the world map section:

# World map visualization
st.subheader("Global Tariff Heatmap")
map_type = st.radio(
    "Select map type:", ["Imposing Countries", "Targeted Countries"], horizontal=True
)

# Add debug info for map data when debug mode is enabled
if st.session_state.get("debug_mode", False):
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
            {"country_code": "US", "count": 5, "iso3": iso2_to_iso3.get("US", "USA")},
            {"country_code": "CN", "count": 3, "iso3": iso2_to_iso3.get("CN", "CHN")},
            {"country_code": "CA", "count": 3, "iso3": iso2_to_iso3.get("CA", "CAN")},
            {"country_code": "MX", "count": 2, "iso3": iso2_to_iso3.get("MX", "MEX")},
            {"country_code": "GB", "count": 2, "iso3": iso2_to_iso3.get("GB", "GBR")},
            {"country_code": "DE", "count": 4, "iso3": iso2_to_iso3.get("DE", "DEU")},
            {"country_code": "FR", "count": 1, "iso3": iso2_to_iso3.get("FR", "FRA")},
        ]
        test_df = pd.DataFrame(test_data)

        st.write("Test data for map:")
        st.write(test_df)

        # Create a direct choropleth map with test data
        import plotly.graph_objects as go

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

# Only show test maps when debug mode is enabled
if st.session_state.get("debug_mode", False):
    with st.expander("Test Maps"):
        st.write("### Direct Map Implementation Test")
        st.write("Testing direct map implementation using go.Choropleth")

        # Directly using the data we see in the debug output
        direct_map_data = pd.DataFrame(
            [
                {"country_code": "CN", "count": 15},
                {"country_code": "CA", "count": 14},
                {"country_code": "MX", "count": 8},
                {"country_code": "NG", "count": 2},
                {"country_code": "US", "count": 1},
                {"country_code": "IN", "count": 1},
                {"country_code": "CH", "count": 1},
            ]
        )

        st.write("Direct map data:")
        st.write(direct_map_data)

        # Create direct choropleth map
        try:
            import plotly.graph_objects as go

            direct_fig = go.Figure(
                data=go.Choropleth(
                    locations=direct_map_data["country_code"],
                    z=direct_map_data["count"],
                    locationmode="ISO-3",  # Try explicitly setting locationmode
                    colorscale="Blues",
                    marker_line_color="white",
                    marker_line_width=0.5,
                    colorbar_title="Event Count",
                )
            )

            direct_fig.update_layout(
                title_text="Direct Map Test",
                geo=dict(
                    showframe=False,
                    showcoastlines=True,
                    projection_type="natural earth",
                    showland=True,
                    landcolor="lightgray",
                    countrycolor="white",
                    coastlinecolor="white",
                    lakecolor="white",
                    showocean=True,
                    oceancolor="aliceblue",
                ),
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
            )

            st.plotly_chart(direct_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating direct map: {e}")

        st.write("### ISO-2 Format Map Test")
        st.write("Testing with explicit ISO-2 format")

        # Convert 2-letter ISO codes (ISO-2) to 3-letter ISO codes (ISO-3)
        iso2_to_iso3 = {
            "CN": "CHN",  # China
            "CA": "CAN",  # Canada
            "MX": "MEX",  # Mexico
            "NG": "NGA",  # Nigeria
            "US": "USA",  # United States
            "IN": "IND",  # India
            "CH": "CHE",  # Switzerland
            "LI": "LIE",  # Liechtenstein
            "NO": "NOR",  # Norway
            "IS": "ISL",  # Iceland
            "EU": "EUR",  # European Union (not a standard ISO but used for testing)
        }

        # Use the same data but with ISO-3 codes
        iso3_map_data = pd.DataFrame(
            [
                {"country_code": iso2_to_iso3.get("CN", "CN"), "count": 15},
                {"country_code": iso2_to_iso3.get("CA", "CA"), "count": 14},
                {"country_code": iso2_to_iso3.get("MX", "MX"), "count": 8},
                {"country_code": iso2_to_iso3.get("NG", "NG"), "count": 2},
                {"country_code": iso2_to_iso3.get("US", "US"), "count": 1},
                {"country_code": iso2_to_iso3.get("IN", "IN"), "count": 1},
                {"country_code": iso2_to_iso3.get("CH", "CH"), "count": 1},
            ]
        )

        st.write("ISO-3 formatted map data:")
        st.write(iso3_map_data)

        # Create direct choropleth map with ISO-3 codes
        try:
            import plotly.graph_objects as go

            iso3_fig = go.Figure(
                data=go.Choropleth(
                    locations=iso3_map_data["country_code"],
                    z=iso3_map_data["count"],
                    # No locationmode needed for ISO-3
                    colorscale="Blues",
                    marker_line_color="white",
                    marker_line_width=0.5,
                    colorbar_title="Event Count",
                )
            )

            iso3_fig.update_layout(
                title_text="ISO-3 Map Test",
                geo=dict(
                    showframe=False,
                    showcoastlines=True,
                    projection_type="natural earth",
                    showland=True,
                    landcolor="lightgray",
                    countrycolor="white",
                    coastlinecolor="white",
                    lakecolor="white",
                    showocean=True,
                    oceancolor="aliceblue",
                ),
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
            )

            st.plotly_chart(iso3_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating ISO-3 map: {e}")
