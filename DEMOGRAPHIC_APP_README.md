# Demographic Analysis Dash App

A separate Dash application to display demographic maps for Mamdani and Trump voters.

## Quick Start

```bash
# Run the demographic Dash app
python demographic_dash_app.py
```

Then open: http://127.0.0.1:8051

(Note: This runs on port 8051 to avoid conflict with the main `dash_app.py` which runs on port 8050)

## Features

The app displays 3 tabs, each showing side-by-side maps comparing Mamdani and Trump districts:

1. **Income Tab**: Median household income in districts where each candidate received votes
2. **Education Tab**: Percentage of population with bachelor's degree or higher
3. **Race Tab**: Majority race demographics in each district

## Files

- `demographic_dash_app.py` - Main Dash app entry point
- `demographic_layouts.py` - Layout components and tab definitions
- `create_demographic_maps.py` - Functions to generate the map figures

## How It Works

1. Loads election data (Mamdani and Trump vote shares by district)
2. Loads Census demographic data (aggregated by county)
3. Merges the data together
4. Creates interactive Plotly maps for each demographic category
5. Displays maps side-by-side for easy comparison

## Data Sources

- **Election Data**: NYC Board of Elections (2024 Presidential, 2025 Mayoral)
- **Demographic Data**: US Census Bureau ACS 5-Year Estimates (2023)
