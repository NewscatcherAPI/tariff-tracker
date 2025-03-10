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


# Updated create_world_map function that leverages our existing standardization


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

    # Print debug info to help diagnose issues
    print(f"Map type: {map_type}")
    print(f"DataFrame columns: {events_df.columns.tolist()}")
    print(f"DataFrame shape: {events_df.shape}")

    # Create a copy of the DataFrame to avoid modifying the original
    df = events_df.copy()

    # Initialize country_counts DataFrame
    country_counts = None

    # Prepare data based on map type
    if map_type == "imposing":
        # Count events by imposing country code if available
        if "imposing_country_code" in df.columns:
            # Make sure the column is not empty
            valid_codes = df[
                df["imposing_country_code"].notna()
                & (df["imposing_country_code"] != "")
            ]

            if not valid_codes.empty:
                print(
                    f"Valid imposing country codes: {valid_codes['imposing_country_code'].unique().tolist()}"
                )
                country_counts = (
                    valid_codes["imposing_country_code"].value_counts().reset_index()
                )
                country_counts.columns = ["country_code", "count"]
                title = "Countries Imposing Tariffs"
            else:
                print("No valid imposing country codes found")
        else:
            print("No imposing_country_code column found")
    else:  # targeted countries
        # Process targeted country codes which can be in different formats
        all_targeted_codes = []

        if "targeted_country_codes" in df.columns:
            # Explicitly convert each value and handle different formats
            for i, row in df.iterrows():
                codes = row.get("targeted_country_codes")

                # Debug the value
                print(f"Row {i}, targeted_country_codes: {codes}, type: {type(codes)}")

                if isinstance(codes, list):
                    all_targeted_codes.extend([c for c in codes if c])
                elif isinstance(codes, str):
                    if "," in codes:
                        # Split comma-separated string
                        all_targeted_codes.extend(
                            [c.strip() for c in codes.split(",") if c.strip()]
                        )
                    else:
                        # Single code
                        all_targeted_codes.append(codes.strip())

            print(f"Processed targeted country codes: {all_targeted_codes}")

            if all_targeted_codes:
                country_counts = (
                    pd.Series(all_targeted_codes).value_counts().reset_index()
                )
                country_counts.columns = ["country_code", "count"]
                title = "Countries Targeted by Tariffs"
            else:
                print("No valid targeted country codes found")
        else:
            print("No targeted_country_codes column found")

    # If we couldn't get country codes, return None
    if country_counts is None or country_counts.empty:
        print("No country count data available for map")
        return None

    print(f"Original country counts: {country_counts.to_dict('records')}")

    # Special handling for EU - represent as member countries
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

    # Handle the EU special case
    expanded_data = []
    for _, row in country_counts.iterrows():
        code = row["country_code"]
        count = row["count"]

        if code == "EU":
            # Add each EU country with the same count
            for eu_code in eu_countries:
                expanded_data.append({"country_code": eu_code, "count": count})
        else:
            expanded_data.append({"country_code": code, "count": count})

    # Convert expanded data to DataFrame
    if expanded_data:
        country_counts = pd.DataFrame(expanded_data)

        # Aggregate if there are duplicates
        country_counts = (
            country_counts.groupby("country_code")["count"].sum().reset_index()
        )

    # Print final data for debugging
    print(f"Final map data: {country_counts.to_dict('records')}")

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
