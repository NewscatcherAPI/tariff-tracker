import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import altair as alt
from typing import Optional, Dict, List, Any, Union


def create_event_timeline(events_df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Create a timeline visualization of tariff events.

    Args:
        events_df: DataFrame containing event data

    Returns:
        Timeline figure or None if insufficient data
    """
    if events_df.empty or "announcement_date" not in events_df.columns:
        return None

    # Create a copy of the DataFrame to avoid modifying the original
    df = events_df.copy()

    # Filter out events without valid dates
    df = df[df["announcement_date"].notna() & (df["announcement_date"] != "")]

    if df.empty:
        return None

    # Convert dates to datetime format
    # First, ensure the date columns exist
    if "implementation_date" not in df.columns:
        df["implementation_date"] = df[
            "announcement_date"
        ]  # Use announcement date if implementation date is missing

    # Convert to datetime, handling any parsing errors by coercing to NaT
    df["announcement_date"] = pd.to_datetime(df["announcement_date"], errors="coerce")
    df["implementation_date"] = pd.to_datetime(
        df["implementation_date"], errors="coerce"
    )

    # Filter out rows where date conversion failed
    df = df.dropna(subset=["announcement_date"])

    # For rows where implementation_date is NaT, use announcement_date
    mask = df["implementation_date"].isna()
    df.loc[mask, "implementation_date"] = df.loc[mask, "announcement_date"]

    # For implementation dates before announcement dates, use announcement_date
    mask = df["implementation_date"] < df["announcement_date"]
    df.loc[mask, "implementation_date"] = df.loc[mask, "announcement_date"]

    # Add one month to implementation date if it equals announcement date
    # This ensures the timeline bar has sufficient width to be visible
    mask = df["implementation_date"] == df["announcement_date"]
    df.loc[mask, "implementation_date"] = df.loc[
        mask, "announcement_date"
    ] + pd.DateOffset(months=1)

    # Sort by date for better visualization
    df = df.sort_values("announcement_date")

    # Get the date range
    min_date = df["announcement_date"].min()
    max_date = df["implementation_date"].max()

    # If the date range is too small, extend it to ensure a reasonable visualization
    date_range = max_date - min_date
    if date_range.days < 90:  # Less than 3 months
        # Extend the range to at least 6 months
        new_min_date = max_date - pd.DateOffset(months=6)
        if new_min_date < min_date:
            min_date = new_min_date

    # Create timeline figure
    fig = px.timeline(
        df,
        x_start="announcement_date",
        x_end="implementation_date",
        y="imposing_country",
        color="measure_type",
        hover_name="summary",
        hover_data=["targeted_countries", "main_tariff_rate"],
        labels={
            "announcement_date": "Announcement Date",
            "implementation_date": "Implementation Date",
        },
        title="Tariff Event Timeline",
        color_discrete_map={
            "new tariff": "#FF4B4B",  # Bright red
            "tariff increase": "#5DADE2",  # Light blue
            "tariff reduction": "#4169E1",  # Royal blue
            "retaliatory tariff": "#1E8449",  # Dark green
            "import ban": "#8E44AD",  # Purple
            "quota": "#F39C12",  # Orange
            "other trade restriction": "#F5B7B1",  # Light red/pink
        },
    )

    # Customize layout
    fig.update_layout(
        height=600,
        legend_title="Measure Type",
        xaxis_title="Date",
        yaxis_title="Imposing Country",
        yaxis={"categoryorder": "total ascending"},
        hovermode="closest",
        # Set a fixed date range to make visualization more representative
        xaxis_range=[
            min_date,
            max_date + pd.DateOffset(days=15),
        ],  # Add a bit of padding on the right
    )

    # Add vertical line for current date using shapes instead of add_vline
    # This avoids the timestamp arithmetic issue
    today = pd.Timestamp.now().floor("D")

    fig.update_layout(
        shapes=[
            dict(
                type="line",
                xref="x",
                yref="paper",
                x0=today,
                y0=0,
                x1=today,
                y1=1,
                line=dict(
                    color="gray",
                    width=2,
                    dash="dash",
                ),
            )
        ],
        annotations=[
            dict(
                x=today,
                y=1.05,
                xref="x",
                yref="paper",
                text="Today",
                showarrow=False,
                font=dict(color="gray"),
            )
        ],
    )

    return fig


def create_world_map(
    events_df: pd.DataFrame, map_type: str = "imposing"
) -> Optional[go.Figure]:
    """
    Create a world map visualization of tariff events.

    Args:
        events_df: DataFrame containing event data
        map_type: Type of map to create ('imposing' or 'targeted')

    Returns:
        World map figure or None if insufficient data
    """
    if events_df.empty:
        return None

    # Create a copy of the DataFrame to avoid modifying the original
    df = events_df.copy()

    # Prepare data based on map type
    if map_type == "imposing":
        # Focus on country codes which work better with choropleth maps
        if "imposing_country_code" in df.columns:
            # Count events by imposing country code
            country_counts = df["imposing_country_code"].value_counts().reset_index()
            country_counts.columns = ["country_code", "count"]
            title = "Countries Imposing Tariffs"
        else:
            return None
    else:  # targeted countries
        # This is more complex because targeted_country_codes can be a list or string
        if "targeted_country_codes" not in df.columns:
            return None

        # Process the targeted country codes
        all_targeted_codes = []

        for codes in df["targeted_country_codes"]:
            if isinstance(codes, list):
                all_targeted_codes.extend(codes)
            elif isinstance(codes, str):
                # If it's a comma-separated string, split it
                all_targeted_codes.extend([code.strip() for code in codes.split(",")])

        # If no targeted countries found
        if not all_targeted_codes:
            return None

        # Count occurrences of each country code
        country_counts = pd.Series(all_targeted_codes).value_counts().reset_index()
        country_counts.columns = ["country_code", "count"]
        title = "Countries Targeted by Tariffs"

    if country_counts.empty:
        return None

    # Special handling for EU - represent as member countries
    # First, save a copy of the original data
    original_counts = country_counts.copy()

    # Create new dataframe with expanded EU countries if needed
    expanded_data = []
    eu_countries = [
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
    ]

    for _, row in original_counts.iterrows():
        if row["country_code"] == "EU":
            # Add each EU country with the same count
            for country in eu_countries:
                expanded_data.append({"country_code": country, "count": row["count"]})
        else:
            expanded_data.append(row.to_dict())

    # Convert back to DataFrame
    if expanded_data:
        country_counts = pd.DataFrame(expanded_data)

        # Aggregate if there are duplicates after expansion
        country_counts = (
            country_counts.groupby("country_code")["count"].sum().reset_index()
        )

    # Create choropleth map with Plotly Express
    fig = px.choropleth(
        country_counts,
        locations="country_code",
        color="count",
        hover_name="country_code",
        color_continuous_scale=px.colors.sequential.Blues,
        labels={"count": "Number of Events"},
        title=title,
    )

    # Customize layout
    fig.update_layout(
        height=600,
        coloraxis_colorbar=dict(title="Event Count"),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="natural earth",
            showcountries=True,
            countrycolor="lightgray",
            coastlinecolor="lightgray",
            # Make sure the map is centered properly
            center=dict(lon=0, lat=20),
            # Set an appropriate zoom level
            projection_scale=1.2,
        ),
    )

    return fig


def create_industry_chart(events_df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Create a bar chart of affected industries.

    Args:
        events_df: DataFrame containing event data

    Returns:
        Bar chart figure or None if insufficient data
    """
    if events_df.empty or "affected_industries" not in events_df.columns:
        return None

    # Extract industries from the comma-separated list
    industries = []
    for ind_str in events_df["affected_industries"]:
        if isinstance(ind_str, str) and ind_str:
            industries.extend([ind.strip() for ind in ind_str.split(",")])

    if not industries:
        return None

    # Count occurrences of each industry
    industry_counts = pd.Series(industries).value_counts().reset_index()
    industry_counts.columns = ["Industry", "Count"]

    # Create bar chart
    fig = px.bar(
        industry_counts,
        x="Count",
        y="Industry",
        orientation="h",
        title="Affected Industries",
        color="Count",
        color_continuous_scale=px.colors.sequential.Blues,
    )

    # Customize layout
    fig.update_layout(
        height=500,
        xaxis_title="Number of Events",
        yaxis_title="Industry",
        yaxis={"categoryorder": "total ascending"},
    )

    return fig


def create_measure_type_pie(events_df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Create a pie chart of measure types.

    Args:
        events_df: DataFrame containing event data

    Returns:
        Pie chart figure or None if insufficient data
    """
    if events_df.empty or "measure_type" not in events_df.columns:
        return None

    # Count occurrences of each measure type
    measure_counts = events_df["measure_type"].value_counts().reset_index()
    measure_counts.columns = ["Measure Type", "Count"]

    # Create pie chart
    fig = px.pie(
        measure_counts,
        values="Count",
        names="Measure Type",
        title="Distribution of Tariff Measure Types",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )

    # Customize layout
    fig.update_layout(height=500)

    return fig


def create_product_wordcloud(events_df: pd.DataFrame) -> Optional[plt.Figure]:
    """
    Create a word cloud of affected products.

    Note: This function will be implemented in a later phase using matplotlib
    and wordcloud library.

    Args:
        events_df: DataFrame containing event data

    Returns:
        Word cloud figure or None if insufficient data
    """
    # Implementation will be added in Phase 2.4
    pass


def create_tariff_rates_histogram(events_df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Create a histogram of main tariff rates.

    Args:
        events_df: DataFrame containing event data

    Returns:
        Histogram figure or None if insufficient data
    """
    if events_df.empty or "main_tariff_rate" not in events_df.columns:
        return None

    # Filter for numeric tariff rates
    df = events_df.copy()
    df = df[pd.to_numeric(df["main_tariff_rate"], errors="coerce").notna()]

    if df.empty:
        return None

    # Create histogram
    fig = px.histogram(
        df,
        x="main_tariff_rate",
        nbins=20,
        title="Distribution of Tariff Rates",
        labels={"main_tariff_rate": "Tariff Rate (%)"},
        color_discrete_sequence=["#0068c9"],
    )

    # Customize layout
    fig.update_layout(
        height=400, xaxis_title="Tariff Rate (%)", yaxis_title="Count", bargap=0.1
    )

    return fig


def create_time_series(
    events_df: pd.DataFrame,
    time_column: str = "announcement_date",
    group_by: str = "month",
) -> Optional[alt.Chart]:
    """
    Create a time series visualization of tariff events.

    Args:
        events_df: DataFrame containing event data
        time_column: Column to use for time axis
        group_by: Time grouping ('day', 'week', 'month', 'quarter', 'year')

    Returns:
        Time series chart or None if insufficient data
    """
    # Implementation will be added in Phase 4.2
    pass
