import pandas as pd
import numpy as np
import os
import streamlit as st
from datetime import datetime
import re
import pycountry
from typing import List, Dict, Any, Union, Optional, Set


def clean_event_data(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean and preprocess event data for analysis.

    Args:
        events: List of event dictionaries from the API

    Returns:
        List of cleaned event data
    """
    if not events:
        return []

    cleaned_events = []
    code_to_name = load_country_codes()  # Load country code to name mapping

    for event in events:
        # Extract tariff_v2 data if it exists
        tariff_data = event.get("tariffs_v2", {})
        if not tariff_data:
            continue

        # Get country code
        imposing_country_code = tariff_data.get("imposing_country_code", "")

        # Use standardized country name if available, otherwise use the original name
        if imposing_country_code and imposing_country_code in code_to_name:
            imposing_country = code_to_name[imposing_country_code]
        else:
            imposing_country = tariff_data.get("imposing_country_name", "")

        # Standardize targeted countries
        targeted_country_codes = tariff_data.get("targeted_country_codes", [])
        targeted_countries = []

        if targeted_country_codes:
            for code in targeted_country_codes:
                if code in code_to_name:
                    targeted_countries.append(code_to_name[code])
                else:
                    # If code not found in mapping, use original name if available
                    original_names = tariff_data.get("targeted_country_names", [])
                    idx = (
                        targeted_country_codes.index(code)
                        if code in targeted_country_codes
                        else -1
                    )
                    if idx >= 0 and idx < len(original_names):
                        targeted_countries.append(original_names[idx])
                    else:
                        targeted_countries.append(code)  # Use code as fallback
        else:
            # If no codes available, use original country names
            targeted_countries = tariff_data.get("targeted_country_names", [])

        # Handle different formats of data, lists vs strings
        affected_industries = tariff_data.get("affected_industries", [])
        if isinstance(affected_industries, str):
            affected_industries = [
                ind.strip() for ind in affected_industries.split(",") if ind.strip()
            ]

        affected_products = tariff_data.get("affected_products", [])
        if isinstance(affected_products, str):
            affected_products = [
                prod.strip() for prod in affected_products.split(",") if prod.strip()
            ]

        hs_product_categories = tariff_data.get("hs_product_categories", [])
        if isinstance(hs_product_categories, str):
            hs_product_categories = [
                cat.strip() for cat in hs_product_categories.split(",") if cat.strip()
            ]

        tariff_rates = tariff_data.get("tariff_rates", [])
        if isinstance(tariff_rates, str):
            tariff_rates = [
                rate.strip() for rate in tariff_rates.split(",") if rate.strip()
            ]

        # Create a cleaned event object with standardized fields
        cleaned_event = {
            "id": event.get("id", ""),
            "extraction_date": normalize_date(event.get("extraction_date", "")),
            "event_type": event.get("event_type", ""),
            "global_event_type": event.get("global_event_type", ""),
            "imposing_country": imposing_country,
            "imposing_country_code": imposing_country_code,
            "targeted_countries": targeted_countries,
            "targeted_country_codes": targeted_country_codes,
            "measure_type": tariff_data.get("measure_type", ""),
            "affected_industries": affected_industries,
            "affected_products": affected_products,
            "hs_product_categories": hs_product_categories,
            "main_tariff_rate": tariff_data.get("main_tariff_rate", None),
            "tariff_rates": tariff_rates,
            "announcement_date": normalize_date(
                tariff_data.get("announcement_date", "")
            ),
            "implementation_date": normalize_date(
                tariff_data.get("implementation_date", "")
            ),
            "expiration_date": normalize_date(tariff_data.get("expiration_date", "")),
            "policy_objective": tariff_data.get("policy_objective", ""),
            "legal_basis": tariff_data.get("legal_basis", ""),
            "relevance_score": tariff_data.get("relevance_score", ""),
            "summary": tariff_data.get("summary", ""),
            "articles": clean_article_data(event.get("articles", [])),
        }

        cleaned_events.append(cleaned_event)

    # Debug output if no events were processed
    if not cleaned_events:
        print("Warning: No events were processed. Check if the data format is correct.")
        if events:
            first_event = events[0]
            print(f"Sample event structure: {list(first_event.keys())}")
            if "tariffs_v2" in first_event:
                print(
                    f"Sample tariffs_v2 structure: {list(first_event['tariffs_v2'].keys())}"
                )

    return cleaned_events


def normalize_date(date_str: str) -> str:
    """
    Normalize date strings to a standard format.

    Args:
        date_str: Date string in various formats

    Returns:
        Normalized date string (YYYY-MM-DD) or original if parsing fails
    """
    if not date_str:
        return ""

    # Handle YYYY/MM/DD format
    if re.match(r"^\d{4}/\d{1,2}(/\d{1,2})?$", date_str):
        parts = date_str.split("/")
        if len(parts) == 2:
            # Only year and month are provided
            return f"{parts[0]}-{parts[1].zfill(2)}"
        elif len(parts) == 3:
            # Year, month, and day are provided
            return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"

    # Handle datetime string with format "YYYY-MM-DD HH:MM:SS"
    if " " in date_str:
        try:
            return date_str.split(" ")[0]
        except:
            pass

    # Return original if we can't parse it
    return date_str


def clean_article_data(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean and standardize article data.

    Args:
        articles: List of article dictionaries

    Returns:
        List of cleaned article data
    """
    if not articles:
        return []

    cleaned_articles = []

    for article in articles:
        cleaned_article = {
            "id": article.get("id", ""),
            "title": article.get("title", ""),
            "link": article.get("link", ""),
            "media": article.get("media", ""),
            "published_date": article.get("published_date", ""),
            "name_source": article.get("name_source", ""),
        }

        # Add optional fields if they exist
        for field in ["description", "content", "authors", "language"]:
            if field in article:
                cleaned_article[field] = article[field]

        cleaned_articles.append(cleaned_article)

    return cleaned_articles


def events_to_dataframe(events: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of event dictionaries to a pandas DataFrame.

    Args:
        events: List of event dictionaries

    Returns:
        DataFrame containing event data
    """
    if not events:
        print("Warning: No events provided to events_to_dataframe")
        return pd.DataFrame()

    # Clean the event data first if not already cleaned
    if "tariffs_v2" in events[0]:
        print("Converting raw API events to cleaned format")
        cleaned_events = clean_event_data(events)
    else:
        print("Events already in cleaned format")
        cleaned_events = events

    # Create DataFrame
    try:
        df = pd.DataFrame(cleaned_events)

        # Debug information
        print(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {df.columns.tolist()}")

        # Handle list columns by converting to string representation
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, list)).any():
                print(f"Converting list column to string: {col}")
                df[col] = df[col].apply(
                    lambda x: (
                        ", ".join(
                            [
                                (
                                    str(item)
                                    if not isinstance(item, dict)
                                    else str(item.get("name", str(item)))
                                )
                                for item in x
                            ]
                        )
                        if isinstance(x, list)
                        else x
                    )
                )

        return df
    except Exception as e:
        print(f"Error creating DataFrame: {e}")
        # Return empty DataFrame if conversion fails
        return pd.DataFrame()


def detect_potential_duplicates(
    events: List[Dict[str, Any]], threshold: float = 0.7
) -> List[List[Dict[str, Any]]]:
    """
    Detect potential duplicate events based on similarity of key fields.

    Args:
        events: List of event dictionaries
        threshold: Similarity threshold for considering events as duplicates

    Returns:
        List of groups of potentially duplicate events
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    if not events or len(events) < 2:
        return []

    # Create a list of event summaries
    summaries = [event.get("summary", "") for event in events]

    # Calculate TF-IDF vectors for each summary
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(summaries)

    # Calculate cosine similarity between all pairs of summaries
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # Find groups of similar events
    duplicate_groups = []
    processed_indices = set()

    for i in range(len(events)):
        if i in processed_indices:
            continue

        # Find events similar to the current one
        similar_indices = [
            j
            for j in range(len(events))
            if j != i and similarity_matrix[i, j] >= threshold
        ]

        if similar_indices:
            # Create a group with the current event and all similar events
            group = [events[i]] + [events[j] for j in similar_indices]
            duplicate_groups.append(group)

            # Mark all events in this group as processed
            processed_indices.add(i)
            processed_indices.update(similar_indices)

    return duplicate_groups


def get_country_code(country_name: str) -> Optional[str]:
    """
    Get the ISO 3166-1 alpha-2 country code for a country name.

    Args:
        country_name: Name of the country

    Returns:
        Country code or None if not found
    """
    try:
        country = pycountry.countries.get(name=country_name)
        if country:
            return country.alpha_2

        # Try searching by partial name
        countries = pycountry.countries.search_fuzzy(country_name)
        if countries:
            return countries[0].alpha_2
    except:
        pass

    # Handle special cases
    special_cases = {
        "United States": "US",
        "United States of America": "US",
        "USA": "US",
        "UK": "GB",
        "United Kingdom": "GB",
        "European Union": "EU",
        "EU": "EU",
    }

    return special_cases.get(country_name)


def get_country_name(country_code: str) -> str:
    """
    Get the country name for an ISO 3166-1 alpha-2 country code.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        Country name or the original code if not found
    """
    if country_code == "EU":
        return "European Union"

    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if country:
            return country.name
    except:
        pass

    return country_code


# Improved load_country_codes function for utils/data_processing.py


def load_country_codes() -> Dict[str, str]:
    """
    Load ISO 3166 country codes and names from CSV file.

    Returns:
        Dictionary mapping country codes to standardized country names
    """
    # Default mapping for common countries and special cases
    default_mapping = {
        "US": "United States",
        "GB": "United Kingdom",
        "EU": "European Union",
        "CN": "China",
        "RU": "Russia",
        "JP": "Japan",
        "DE": "Germany",
        "FR": "France",
        "CA": "Canada",
        "AU": "Australia",
        "BR": "Brazil",
        "IN": "India",
        "MX": "Mexico",
        "KR": "South Korea",
        "IT": "Italy",
        "ES": "Spain",
        "NL": "Netherlands",
        "CH": "Switzerland",
        "SA": "Saudi Arabia",
        "TR": "Turkey",
        "ZA": "South Africa",
        "SG": "Singapore",
        "MY": "Malaysia",
        "ID": "Indonesia",
        "TH": "Thailand",
        "AE": "United Arab Emirates",
    }

    try:
        country_codes_path = os.path.join("data", "country_codes_iso_3166.csv")
        if os.path.exists(country_codes_path):
            country_df = pd.read_csv(country_codes_path)
            code_to_name = {
                row["Alpha-2 code"].strip(): row["Country"].strip()
                for _, row in country_df.iterrows()
            }

            # Add EU manually as it's not in ISO 3166 but used in our app
            code_to_name["EU"] = "European Union"

            return code_to_name
        else:
            st.warning(
                "Country codes CSV file not found. Using default country mapping."
            )
            return default_mapping
    except Exception as e:
        st.warning(f"Failed to load country codes: {e}. Using default country mapping.")
        return default_mapping


def standardize_countries_in_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize country names in a DataFrame to ensure consistency.

    Args:
        df: DataFrame with country names to standardize

    Returns:
        DataFrame with standardized country names
    """
    if df.empty:
        return df

    # Load country code to name mapping
    code_to_name = load_country_codes()

    # Create a copy of the DataFrame
    standardized_df = df.copy()

    # Country name cleanup and standardization
    country_name_mapping = {
        "United States of America": "United States",
        "USA": "United States",
        "United States": "United States",
        "UK": "United Kingdom",
        "Great Britain": "United Kingdom",
        "European Union": "European Union",
        "EU": "European Union",
    }

    # Update with any additional mappings from ISO codes
    if "imposing_country_code" in standardized_df.columns:
        for _, row in standardized_df.iterrows():
            if (
                pd.notna(row["imposing_country_code"])
                and row["imposing_country_code"] in code_to_name
            ):
                code = row["imposing_country_code"]
                country_name_mapping[code] = code_to_name[code]

                # Also map any existing country name to the standardized name
                if pd.notna(row["imposing_country"]):
                    country_name_mapping[row["imposing_country"]] = code_to_name[code]

    # Apply the mapping to imposing_country column
    if "imposing_country" in standardized_df.columns:
        standardized_df["imposing_country"] = standardized_df[
            "imposing_country"
        ].replace(country_name_mapping)

    return standardized_df


def calculate_event_statistics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate various statistics from a list of tariff events.

    Args:
        events: List of cleaned event dictionaries

    Returns:
        Dictionary of statistics
    """
    if not events:
        return {
            "total_events": 0,
            "imposing_countries": [],
            "targeted_countries": [],
            "measure_types": {},
            "avg_tariff_rate": 0,
            "affected_industries": {},
            "affected_products": [],
        }

    # Initialize variables
    imposing_countries: Set[str] = set()
    targeted_countries: Set[str] = set()
    measure_types: Dict[str, int] = {}
    tariff_rates: List[float] = []
    industries: Dict[str, int] = {}
    products: Set[str] = set()

    # Process each event
    for event in events:
        # Imposing country
        if event.get("imposing_country"):
            imposing_countries.add(event["imposing_country"])

        # Targeted countries
        if isinstance(event.get("targeted_countries"), list):
            targeted_countries.update(event["targeted_countries"])
        elif isinstance(event.get("targeted_countries"), str):
            targeted_countries.update(
                [c.strip() for c in event["targeted_countries"].split(",")]
            )

        # Measure type
        measure_type = event.get("measure_type", "unknown")
        measure_types[measure_type] = measure_types.get(measure_type, 0) + 1

        # Tariff rate
        if event.get("main_tariff_rate") is not None:
            try:
                rate = float(event["main_tariff_rate"])
                tariff_rates.append(rate)
            except (ValueError, TypeError):
                pass

        # Industries
        if isinstance(event.get("affected_industries"), list):
            for industry in event["affected_industries"]:
                industries[industry] = industries.get(industry, 0) + 1
        elif isinstance(event.get("affected_industries"), str):
            for industry in [
                i.strip() for i in event["affected_industries"].split(",")
            ]:
                if industry:
                    industries[industry] = industries.get(industry, 0) + 1

        # Products
        if isinstance(event.get("affected_products"), list):
            products.update(event["affected_products"])
        elif isinstance(event.get("affected_products"), str):
            products.update([p.strip() for p in event["affected_products"].split(",")])

    # Calculate average tariff rate
    avg_tariff_rate = sum(tariff_rates) / len(tariff_rates) if tariff_rates else 0

    # Return statistics
    return {
        "total_events": len(events),
        "imposing_countries": sorted(list(imposing_countries)),
        "targeted_countries": sorted(list(targeted_countries)),
        "measure_types": measure_types,
        "avg_tariff_rate": round(avg_tariff_rate, 2),
        "affected_industries": industries,
        "affected_products": sorted(list(products)),
    }
