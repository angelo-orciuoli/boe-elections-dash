# NYC Election Comparison Dashboard

An interactive dashboard comparing election results across NYC boroughs. Visualizes Mayoral (2025) and Presidential (2024) vote shares at the election district level using choropleth maps.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Dash app
python dash_app.py
```

Then open: http://127.0.0.1:8050

## Project Structure

```
boe-elections-dash/
├── dash_app.py          # Main app entry point - initializes Dash app
├── config.py            # Constants & configuration (borough centers, candidates)
├── map_utils.py         # Map creation functions (choropleth maps)
├── layouts.py           # UI layout components (tabs, grids)
├── data_cleaner.py      # Election data loading and cleaning
├── streamlit_app.py     # Alternative Streamlit version of the app
├── requirements.txt     # Python dependencies
├── data/                # Election data files
│   ├── citywide_mayor_citywide.csv
│   ├── citywide_president_citywide.csv
│   └── nyc_districts/   # Shapefile for district boundaries
└── public/              # Static assets
```

## Module Descriptions

| Module | Purpose |
|--------|---------|
| `dash_app.py` | App initialization and entry point |
| `config.py` | Borough configurations, map settings, candidate lists, file paths |
| `map_utils.py` | `load_and_merge_data()`, `create_citywide_comparison_map()`, `create_borough_map()` |
| `layouts.py` | `create_citywide_tab()`, `create_borough_tab()`, `create_app_layout()` |
| `data_cleaner.py` | `ElectionDataCleaner` class for processing raw election CSVs |

## Features

- **Citywide Overview Tab**: Side-by-side comparison of Presidential and Mayoral races
- **Borough Comparison Tab**: Detailed borough-level maps showing vote share differences
- **Interactive Tooltips**: Hover over districts to see exact vote percentages
- **Diverging Color Scale**: Red/Blue choropleth showing relative candidate support

## Data Sources

Election data from NYC Board of Elections. Shapefiles for election district boundaries from NYC Open Data.
