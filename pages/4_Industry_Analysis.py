import streamlit as st
import pandas as pd
import json
import os
import sys
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_processing import events_to_dataframe, clean_event_data
from utils.visualization import create_industry_chart, create_tariff_rates_histogram
from utils.data_manager import get_session_events_data, initialize_session_data

# Set page configuration
st.set_page_config(
    page_title="Tariff Tracker - Industry Analysis",
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
    .analysis-card {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .analysis-header {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
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

# Main content
st.markdown('<div class="main-header">Industry Analysis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Explore tariff impacts by industry and product categories</div>',
    unsafe_allow_html=True,
)

# Industry overview
with st.container():
    st.markdown(
        """
    <div class="analysis-card">
        <div class="analysis-header">Industry Overview</div>
        <p>
            Analyze the distribution of tariff events across different industries and sectors.
            Understand which industries are most affected by global trade policies.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# Extract and analyze industry data
if not events_df.empty and "affected_industries" in events_df.columns:
    # Extract all industries from the comma-separated lists
    all_industries = []
    for ind_str in events_df["affected_industries"]:
        if isinstance(ind_str, str) and ind_str:
            all_industries.extend([ind.strip() for ind in ind_str.split(",")])

    # Count occurrences of each industry
    industry_counts = pd.Series(all_industries).value_counts().reset_index()
    industry_counts.columns = ["Industry", "Event Count"]

    # Display industry distribution
    st.subheader("Industry Distribution")

    # Create industry chart
    industry_fig = create_industry_chart(events_df)

    if industry_fig:
        st.plotly_chart(industry_fig, use_container_width=True)
    else:
        st.info("Not enough industry data for visualization.")

    # Display industry data table
    st.markdown("#### Industry Breakdown")
    st.dataframe(industry_counts, use_container_width=True)

    # Industry-specific analysis
    st.subheader("Industry-Specific Analysis")

    # Allow user to select an industry to analyze
    selected_industry = st.selectbox(
        "Select an industry to analyze:",
        options=sorted(industry_counts["Industry"].unique()),
    )

    if selected_industry:
        # Filter events for the selected industry
        industry_events = []

        for event in events:
            industries = event.get("affected_industries", [])
            if isinstance(industries, list) and selected_industry in industries:
                industry_events.append(event)
            elif isinstance(industries, str) and selected_industry in industries:
                industry_events.append(event)

        if industry_events:
            # Convert to DataFrame for analysis
            industry_df = events_to_dataframe(industry_events)

            st.markdown(f"#### Analysis for {selected_industry} Industry")

            # Display key metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                # Count of events
                st.metric("Number of Events", len(industry_events))

            with col2:
                # Average tariff rate
                if "main_tariff_rate" in industry_df.columns:
                    avg_rate = (
                        industry_df["main_tariff_rate"]
                        .replace("", None)
                        .astype(float)
                        .mean()
                    )
                    st.metric("Average Tariff Rate", f"{avg_rate:.1f}%")
                else:
                    st.metric("Average Tariff Rate", "N/A")

            with col3:
                # Most common measure type
                if "measure_type" in industry_df.columns:
                    top_measure = (
                        industry_df["measure_type"].value_counts().index[0]
                        if not industry_df["measure_type"].empty
                        else "N/A"
                    )
                    st.metric("Most Common Measure", top_measure)
                else:
                    st.metric("Most Common Measure", "N/A")

            # Analyze affected products
            st.markdown("#### Affected Products")

            # Extract all products from the selected industry events
            all_products = []
            for event in industry_events:
                products = event.get("affected_products", [])
                if isinstance(products, list):
                    all_products.extend(products)
                elif isinstance(products, str) and products:
                    all_products.extend([p.strip() for p in products.split(",")])

            # Count product occurrences
            product_counts = pd.Series(all_products).value_counts().reset_index()
            product_counts.columns = ["Product", "Event Count"]

            if not product_counts.empty:
                # Create product chart
                fig = px.bar(
                    product_counts.head(10),
                    x="Event Count",
                    y="Product",
                    orientation="h",
                    title=f"Top Products Affected in {selected_industry} Industry",
                    color="Event Count",
                    color_continuous_scale=px.colors.sequential.Blues,
                )

                fig.update_layout(
                    height=400,
                    xaxis_title="Number of Events",
                    yaxis_title="Product",
                    yaxis={"categoryorder": "total ascending"},
                )

                st.plotly_chart(fig, use_container_width=True)

                # Display product table
                st.dataframe(product_counts, use_container_width=True)
            else:
                st.info("No product data available for this industry.")

            # Tariff rate analysis
            st.markdown("#### Tariff Rate Analysis")

            # Create tariff rate histogram
            rate_fig = create_tariff_rates_histogram(industry_df)

            if rate_fig:
                st.plotly_chart(rate_fig, use_container_width=True)
            else:
                st.info("Not enough tariff rate data for visualization.")

            # Display events table for this industry
            st.markdown("#### Events in this Industry")

            # Select columns to display
            display_cols = [
                "announcement_date",
                "imposing_country",
                "targeted_countries",
                "measure_type",
                "main_tariff_rate",
                "affected_products",
            ]
            existing_cols = [col for col in display_cols if col in industry_df.columns]

            st.dataframe(industry_df[existing_cols], use_container_width=True)
        else:
            st.info(
                f"No detailed event data available for the {selected_industry} industry."
            )
else:
    st.warning("No industry data available in the dataset.")

# Product category analysis
st.subheader("Product Category Analysis")

if not events_df.empty and "hs_product_categories" in events_df.columns:
    # Extract all HS categories - keeping categories intact without splitting
    all_categories = []

    for event in events:
        categories = event.get("hs_product_categories", [])
        if isinstance(categories, list):
            all_categories.extend(categories)
        elif isinstance(categories, str):
            # If it's already a string (from DataFrame conversion), add it directly
            all_categories.append(categories)

    # Count occurrences of each category
    category_counts = pd.Series(all_categories).value_counts().reset_index()
    category_counts.columns = ["HS Category", "Event Count"]

    # Create category chart
    fig = px.bar(
        category_counts.head(10),
        x="Event Count",
        y="HS Category",
        orientation="h",
        title="Top HS Product Categories Affected by Tariffs",
        color="Event Count",
        color_continuous_scale=px.colors.sequential.Blues,
    )

    fig.update_layout(
        height=500,
        xaxis_title="Number of Events",
        yaxis_title="HS Category",
        yaxis={"categoryorder": "total ascending"},
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display category data table
    st.dataframe(category_counts, use_container_width=True)
else:
    st.info("No HS product category data available in the dataset.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit • Data provided by NewsCatcher Events API")
