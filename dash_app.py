"""
Dash Borough Comparison Dashboard
Compares Mamdani (2025 Mayor) vs Trump (2024 President) vote shares by borough.

Run with: python dash_app.py
Then open: http://127.0.0.1:8050
"""

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import geopandas as gpd
import pandas as pd
import json
from data_cleaner import ElectionDataCleaner

# Borough configuration
BOROUGH_CONFIG = {
    'New York': {'name': 'Manhattan', 'center': {'lat': 40.7831, 'lon': -73.9712}, 'zoom': 11},
    'Kings': {'name': 'Brooklyn', 'center': {'lat': 40.6782, 'lon': -73.9442}, 'zoom': 10.5},
    'Queens': {'name': 'Queens', 'center': {'lat': 40.7282, 'lon': -73.7949}, 'zoom': 10},
    'Bronx': {'name': 'Bronx', 'center': {'lat': 40.8448, 'lon': -73.8648}, 'zoom': 11},
    'Richmond': {'name': 'Staten Island', 'center': {'lat': 40.5795, 'lon': -74.1502}, 'zoom': 11}
}

#     'New York': {'name': 'Manhattan', 'center': {'lat': 40.7831, 'lon': -73.9712}, 'zoom': 10},
#     'Kings': {'name': 'Brooklyn', 'center': {'lat': 40.6782, 'lon': -73.9442}, 'zoom': 9.5},
#     'Queens': {'name': 'Queens', 'center': {'lat': 40.7282, 'lon': -73.7949}, 'zoom': 9},
#     'Bronx': {'name': 'Bronx', 'center': {'lat': 40.8448, 'lon': -73.8648}, 'zoom': 10},
#     'Richmond': {'name': 'Staten Island', 'center': {'lat': 40.5795, 'lon': -74.1502}, 'zoom': 10}


def load_and_merge_data():
    """
    Load both elections and merge into comparison DataFrame.
    """
    # Load mayoral data (Mamdani)
    cleaner_mayor = ElectionDataCleaner('data/citywide_mayor_citywide.csv', election_type='mayor')
    df_mayor, _, _ = cleaner_mayor.load_and_clean()
    
    # Load presidential data (Trump)
    cleaner_pres = ElectionDataCleaner('data/citywide_president_citywide.csv', election_type='president')
    df_pres, _, _ = cleaner_pres.load_and_clean()
    
    # Pivot mayoral data for Mamdani
    mayor_pivot = df_mayor.pivot_table(
        index='ElectDist', columns='vote_choice',
        values='vote_count', aggfunc='sum'
    ).fillna(0)
    mayor_pivot['mayor_total'] = mayor_pivot.sum(axis=1)
    mayor_pivot['mamdani_pct'] = (mayor_pivot['Zohran Mamdani'] / mayor_pivot['mayor_total'] * 100).round(2)
    mayor_pivot = mayor_pivot[['Zohran Mamdani', 'mayor_total', 'mamdani_pct']].reset_index()
    
    # Pivot presidential data for Trump
    pres_pivot = df_pres.pivot_table(
        index='ElectDist', columns='vote_choice',
        values='vote_count', aggfunc='sum'
    ).fillna(0)
    pres_pivot['pres_total'] = pres_pivot.sum(axis=1)
    pres_pivot['trump_pct'] = (pres_pivot['Trump'] / pres_pivot['pres_total'] * 100).round(2)
    pres_pivot = pres_pivot[['Trump', 'pres_total', 'trump_pct']].reset_index()
    
    # Load shapefile
    gdf = gpd.read_file("data/nyc_districts/nyed.shp")
    gdf['ElectDist'] = gdf['ElectDist'].astype(int)
    
    # Merge all data
    gdf = gdf.merge(mayor_pivot, on='ElectDist', how='left')
    gdf = gdf.merge(pres_pivot, on='ElectDist', how='left')
    
    # Add county info from mayor data
    county_map = df_mayor[['ElectDist', 'county']].drop_duplicates()
    gdf = gdf.merge(county_map, on='ElectDist', how='left')
    
    # Calculate vote share difference (Mamdani - Trump)
    gdf['vote_diff'] = gdf['mamdani_pct'] - gdf['trump_pct']
    
    # Convert to WGS84 for Plotly
    gdf = gdf.to_crs(epsg=4326)
    
    return gdf


def create_borough_map(gdf, county_code):
    """Create a Plotly choropleth map for a single borough."""
    config = BOROUGH_CONFIG[county_code]
    borough_gdf = gdf[gdf['county'] == county_code].copy()
    
    # Convert to GeoJSON
    geojson = json.loads(borough_gdf.to_json())
    
    # Get max absolute difference for symmetric color scale
    max_diff = borough_gdf['vote_diff'].abs().max()
    if pd.isna(max_diff) or max_diff == 0:
        max_diff = 10  # Default range if no data
    
    fig = px.choropleth_map(
        borough_gdf,
        geojson=geojson,
        locations=borough_gdf.index,
        color='vote_diff',
        color_continuous_scale='RdBu',
        range_color=[-max_diff, max_diff],
        hover_data={
            'ElectDist': True,
            'mamdani_pct': ':.1f',
            'trump_pct': ':.1f',
            'vote_diff': ':.1f'
        },
        labels={
            'vote_diff': 'Difference (M-T)',
            'mamdani_pct': 'Mamdani %',
            'trump_pct': 'Trump %',
            'ElectDist': 'District'
        },
        map_style='carto-positron',
        center=config['center'],
        zoom=config['zoom'],
        opacity=0.7
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=60),
        title=dict(
            text=f"<b>{config['name']}</b>",
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        coloraxis_colorbar=dict(
            title='← Trump | Mamdani →',
            ticksuffix='%',
            orientation='h',
            y=-0.1,
            yanchor='top',
            x=0.5,
            xanchor='center',
            len=0.8,
            thickness=15
        )
    )
    
    return fig


# Initialize app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "NYC Election Comparison"

# Load data once at startup
gdf = load_and_merge_data()

# Create all borough maps
borough_maps = {
    county: create_borough_map(gdf, county)
    for county in BOROUGH_CONFIG.keys()
}

# App layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🗽 NYC Election Comparison Dashboard", className="text-center my-3"),
            html.P(
                "Comparing Zohran Mamdani (2025 Mayor) vs Trump (2024 President) vote share by district",
                className="text-center text-muted"
            ),
            html.P(
                "Blue = Higher Mamdani support | Red = Higher Trump support",
                className="text-center fw-bold"
            )
        ])
    ]),
    
    html.Hr(),
    
    # Top row: Manhattan and Brooklyn
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=borough_maps['New York'], style={'height': '450px'})
        ], md=6),
        dbc.Col([
            dcc.Graph(figure=borough_maps['Kings'], style={'height': '450px'})
        ], md=6)
    ], className="mb-3"),
    
    # Middle row: Queens and Bronx
    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=borough_maps['Queens'], style={'height': '450px'})
        ], md=6),
        dbc.Col([
            dcc.Graph(figure=borough_maps['Bronx'], style={'height': '450px'})
        ], md=6)
    ], className="mb-3"),
    
    # Bottom row: Staten Island (centered)
    dbc.Row([
        dbc.Col(md=3),
        dbc.Col([
            dcc.Graph(figure=borough_maps['Richmond'], style={'height': '450px'})
        ], md=6),
        dbc.Col(md=3)
    ]),
    
    # Footer
    html.Hr(),
    html.P(
        "Data: NYC Board of Elections | Hover over districts for details",
        className="text-center text-muted small"
    )
    
], fluid=True)


if __name__ == '__main__':
    app.run(debug=True)
