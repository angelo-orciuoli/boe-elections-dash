# Demographic Analysis Feature

This document describes the new demographic analysis features added to the NYC Election Comparison Dashboard.

## Overview

The dashboard now includes demographic overlays showing how income, education, and race correlate with vote shares for Mamdani and Trump across NYC election districts. The data is fetched from the US Census Bureau's American Community Survey (ACS) 5-Year Estimates.

## New Files

### 1. `census_data_fetcher.py`
Fetches demographic data from the US Census API:
- **Median Household Income** (`B19013_001E`)
- **Education Attainment** (`B15003_*` series) - Calculates percentages for:
  - Less than high school
  - High school only
  - Some college
  - Associate's degree
  - Bachelor's degree or higher
- **Race and Ethnicity** (`B03002_*` series) - Calculates percentages for:
  - White alone
  - Black or African American alone
  - Asian alone
  - Hispanic or Latino (of any race)
  - Other races
  - Majority race category

### 2. `demographic_mapper.py`
Maps Census tract data to election districts:
- Currently uses a simplified county-level aggregation approach
- Maps demographic data to all election districts within each county
- Includes caching to avoid repeated API calls

### 3. Updated `map_utils.py`
Added functions:
- `load_election_data_with_demographics()` - Loads election data merged with demographics
- `create_demographic_map()` - Creates citywide demographic choropleth maps
- `create_borough_demographic_map()` - Creates borough-level demographic maps

### 4. Updated `layouts.py`
Added new tabs:
- **Demographic Analysis** - Citywide maps showing income, education, and race for both candidates
- **Borough Demographics** - Borough-level breakdowns of demographic data

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Census API Key**
   - Your Census API key should be in `.env.local` as `CENSUS_API_KEY`
   - The app will automatically load it using `python-dotenv`

3. **Run the App**
   ```bash
   python dash_app.py
   ```

## Data Sources

- **Census Data**: US Census Bureau ACS 5-Year Estimates (2023)
- **Geography**: Census tracts aggregated to NYC counties (boroughs)
- **Caching**: Census data is cached to `data/census_demographics_cache.csv` to avoid repeated API calls

## How It Works

1. **Data Fetching**: On first run, the app fetches Census data for all NYC counties
2. **Data Processing**: Education and race data are converted to percentages
3. **Mapping**: Demographic data is mapped to election districts by county
4. **Visualization**: Maps show demographic characteristics color-coded with vote share overlays

## Limitations

- Currently uses county-level aggregation (all districts in a county get the same demographic values)
- For more precise mapping, you would need Census tract boundary shapefiles and spatial joins
- Census API has rate limits; data is cached to minimize API calls

## Future Enhancements

- Download TIGER/Line shapefiles for Census tracts
- Implement spatial joins for tract-to-district mapping
- Add more demographic variables (age, housing, etc.)
- Add correlation analysis between demographics and vote shares
