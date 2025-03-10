# Tariff Tracker

A Streamlit application for visualizing and analyzing global tariff events extracted from news data.

## Overview

Tariff Tracker provides an interactive interface to explore worldwide tariff announcements, changes, and retaliatory trade measures. The application uses the NewsCatcher Events API to access structured tariff event data extracted from news articles, presenting this information through intuitive visualizations and analysis tools.

## About Events Intelligence

This application is powered by NewsCatcher's Events Intelligence system, which transforms news content into structured event data using AI.

The `tariffs_v2` event type provides structured data about global tariff announcements, including imposing countries, targeted countries, affected products, industries, and implementation timelines.

To learn more, visit the [official documentation](https://www.newscatcherapi.com/docs/v3/events/overview/introduction).

## Features

- **Dashboard Overview**: Summary metrics and global visualizations of tariff events
- **Detailed Event Analysis**: In-depth examination of individual tariff events with source articles
- **Industry and Product Analysis**: Visual breakdown of affected industries and products
- **Live API Integration**: Real-time queries to the NewsCatcher Events API
- **Duplicate Detection**: Identification of potentially redundant event reports
- **Trend Analysis**: Time-series visualization of tariff trends and patterns

## Installation

1. Clone this repository:
 ```
 git clone https://github.com/NewscatcherAPI/tariff-tracker.git
 cd tariff-tracker
 ```

2. Install the required dependencies:
 ```
 pip install -r requirements.txt
 ```

3. Run the application:
 ```
 streamlit run app.py
 ```

## API Setup

To use the Events API integration:

1. Obtain an API key from [NewsCatcher's pricing page](https://www.newscatcherapi.com/pricing).
2. If running locally, create a `.streamlit/secrets.toml` file with your API key:
 ```
 [api]
 key = "your_api_key_here"
 ```
3. If deploying to Streamlit Cloud, add your API key to the repository secrets.

### API Request Format

The application makes calls to the Events API using the following format:

```json
{
  "event_type": "tariffs_v2",
  "attach_articles_data": true,
  "additional_filters": {
    "extraction_date": {
      "gte": "now-3d",
      "lte": "now"
 },
    "tariffs_v2.imposing_country_code": "US",
    "tariffs_v2.main_tariff_rate": {
      "gte": 10
 }
 }
}
```

For more information on available parameters and query formats, visit the [Parameter formats](https://www.newscatcherapi.com/docs/v3/events/overview/parameter-formats) page.

## Tariff Event Data Structure

The Events API returns structured tariff event data with the following key fields:

- **Country Information**:
  - `imposing_country_name` and `imposing_country_code`: The country implementing the tariff
  - `targeted_country_names` and `targeted_country_codes`: Countries affected by the tariff
  
 All country names and codes follow [ISO 3166 standard](https://www.iso.org/iso-3166-country-codes.html), except "EU" for the European Union.

- **Tariff Details**:
  - `measure_type`: Type of trade measure (e.g., "new tariff", "tariff increase", "retaliatory tariff")
  - `tariff_rates`: Specific rates applied to different products
  - `main_tariff_rate`: The primary tariff percentage
  - `previous_tariff_rate`: Rate before changes, if applicable
  - `announcement_date`: When the tariff was announced
  - `implementation_date`: When the tariff takes effect
  - `expiration_date`: When the tariff expires (if temporary)
  - `legal_basis`: Legal justification (e.g., "Section 301")
  - `policy_objective`: Stated goal (e.g., "national security", "protect domestic industry")
  - `exemptions`: Any exceptions to the tariff

- **Economic Impact**:
  - `affected_industries`: Industries impacted, following [GICS sectors](https://www.msci.com/our-solutions/indexes/gics)
  - `affected_products`: Specific products subject to the tariff
  - `hs_product_categories`: Categories from the [Harmonized System nomenclature](https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition/hs-nomenclature-2022-edition.aspx)
  - `estimated_trade_value`: Value of trade affected by the measure

- **Summary**:
  - `summary`: Comprehensive description of the tariff event

Each event is linked to one or more source articles, providing context and verification. For detailed information, see [Working with articles](https://www.newscatcherapi.com/docs/v3/events/overview/articles).

## Project Structure

```
tariff-tracker/
├── app.py                    # Main application entry point
├── pages/                    # Additional application pages
│   ├── 1_Dashboard.py        # Overview dashboard
│   ├── 2_Event_Explorer.py   # Individual event analysis
│   ├── 3_API_Query_Builder.py # Custom API query interface
│   └── 4_Industry_Analysis.py # Industry-specific insights
├── utils/                    # Utility functions
│   ├── api.py                # API integration utilities
│   ├── data_processing.py    # Data cleaning and transformation
│   └── visualization.py      # Visualization functions
├── data/                     # Sample data for testing
├── .streamlit/               # Streamlit configuration
│   ├── config.toml           # Streamlit configuration
│   └── secrets.toml          # API keys and secrets (local only, not committed)
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

## Development

This project is actively under development. Contributions are welcome!

For technical support or questions about the Events API:

- Contact: <support@newscatcherapi.com>
- Visit: [NewsCatcher API Documentation](https://www.newscatcherapi.com/docs/v3/events)
- Quickstart Guide: [Events API Quickstart](https://www.newscatcherapi.com/docs/v3/events/overview/quickstart)

### Upcoming Features

- Enhanced duplicate detection algorithms
- Time-series analysis of tariff patterns
- Integration with additional event types
- Advanced filtering for specific industries or regions
- Export functionality for reports and visualizations

## License

[MIT License](LICENSE)