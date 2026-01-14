"""
Map creation utilities for NYC Election Dashboard.
Provides functions for loading election data and creating choropleth maps.
"""

import json
import geopandas as gpd
import pandas as pd
import plotly.express as px

from config import (
    BOROUGH_CONFIG, NYC_CENTER, NYC_ZOOM,
    MAYORAL_CANDIDATES, MAYOR_DATA_PATH, PRESIDENT_DATA_PATH, SHAPEFILE_PATH
)
from data_cleaner import ElectionDataCleaner


def load_and_merge_data():
    """Load both elections and merge into comparison DataFrame."""
    # Load mayoral data (all candidates)
    cleaner_mayor = ElectionDataCleaner(MAYOR_DATA_PATH, election_type='mayor')
    df_mayor, _, _ = cleaner_mayor.load_and_clean()
    
    # Load presidential data
    cleaner_pres = ElectionDataCleaner(PRESIDENT_DATA_PATH, election_type='president')
    df_pres, _, _ = cleaner_pres.load_and_clean()
    
    # Pivot mayoral data for all candidates
    mayor_pivot = df_mayor.pivot_table(
        index='ElectDist', columns='vote_choice',
        values='vote_count', aggfunc='sum'
    ).fillna(0)
    mayor_pivot['mayor_total'] = mayor_pivot.sum(axis=1)
    
    # Calculate vote percentages for mayoral candidates
    for candidate in MAYORAL_CANDIDATES:
        col_name = f'{candidate.lower().replace(" ", "_")}_pct'
        if candidate in mayor_pivot.columns:
            mayor_pivot[col_name] = (mayor_pivot[candidate] / mayor_pivot['mayor_total'] * 100).round(2)
        else:
            mayor_pivot[col_name] = 0
    
    mayor_pivot = mayor_pivot.reset_index()
    
    # Pivot presidential data
    pres_pivot = df_pres.pivot_table(
        index='ElectDist', columns='vote_choice',
        values='vote_count', aggfunc='sum'
    ).fillna(0)
    pres_pivot['pres_total'] = pres_pivot.sum(axis=1)
    
    # Calculate vote percentages for presidential candidates
    if 'Trump' in pres_pivot.columns:
        pres_pivot['trump_pct'] = (pres_pivot['Trump'] / pres_pivot['pres_total'] * 100).round(2)
    else:
        pres_pivot['trump_pct'] = 0
    if 'Harris' in pres_pivot.columns:
        pres_pivot['harris_pct'] = (pres_pivot['Harris'] / pres_pivot['pres_total'] * 100).round(2)
    else:
        pres_pivot['harris_pct'] = 0
    
    pres_pivot = pres_pivot.reset_index()
    
    # Load shapefile
    gdf = gpd.read_file(SHAPEFILE_PATH)
    gdf['ElectDist'] = gdf['ElectDist'].astype(int)
    
    # Merge all data
    gdf = gdf.merge(mayor_pivot, on='ElectDist', how='left')
    gdf = gdf.merge(pres_pivot, on='ElectDist', how='left', suffixes=('_mayor', '_pres'))
    
    # Add county info from mayor data
    county_map = df_mayor[['ElectDist', 'county']].drop_duplicates()
    gdf = gdf.merge(county_map, on='ElectDist', how='left')
    
    # Calculate vote share differences for comparisons
    gdf['vote_diff'] = gdf['zohran_mamdani_pct'] - gdf['trump_pct']  # Borough comparison
    gdf['mayor_diff'] = gdf['zohran_mamdani_pct'] - gdf['andrew_cuomo_pct']  # Mamdani vs Cuomo
    gdf['pres_diff'] = gdf['harris_pct'] - gdf['trump_pct']  # Harris vs Trump
    
    # Convert to WGS84 for Plotly
    gdf = gdf.to_crs(epsg=4326)
    
    return gdf


def create_citywide_comparison_map(gdf, election_type):
    """Create a Plotly choropleth map comparing two candidates with diverging scale."""
    # Convert to GeoJSON
    geojson = json.loads(gdf.to_json())
    
    # Configure for each election type
    if election_type == 'mayoral':
        col_name = 'mayor_diff'
        title = 'Zohran Mamdani vs Andrew Cuomo'
        colorbar_title = '← Andrew Cuomo | Zohran Mamdani →'
        hover_labels = {
            'mayor_diff': 'Difference',
            'zohran_mamdani_pct': 'Mamdani %',
            'andrew_cuomo_pct': 'Cuomo %',
            'ElectDist': 'District'
        }
        hover_data = {
            'ElectDist': True,
            'zohran_mamdani_pct': ':.1f',
            'andrew_cuomo_pct': ':.1f',
            'mayor_diff': ':.1f'
        }
    else:  # presidential
        col_name = 'pres_diff'
        title = 'Kamala Harris vs Donald Trump'
        colorbar_title = '← Donald Trump | Kamala Harris →'
        hover_labels = {
            'pres_diff': 'Difference',
            'harris_pct': 'Harris %',
            'trump_pct': 'Trump %',
            'ElectDist': 'District'
        }
        hover_data = {
            'ElectDist': True,
            'harris_pct': ':.1f',
            'trump_pct': ':.1f',
            'pres_diff': ':.1f'
        }
    
    fig = px.choropleth_map(
        gdf,
        geojson=geojson,
        locations=gdf.index,
        color=col_name,
        color_continuous_scale='RdBu',
        range_color=[-100, 100],
        hover_data=hover_data,
        labels=hover_labels,
        map_style='carto-positron',
        center=NYC_CENTER,
        zoom=NYC_ZOOM,
        opacity=0.9
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=80),
        title=dict(
            text=f"<b>{title}</b>",
            x=0.5,
            xanchor='center',
            font=dict(size=18)
        ),
        coloraxis_colorbar=dict(
            title=dict(
                text=colorbar_title,
                side='bottom'
            ),
            orientation='h',
            x=0.5,
            xanchor='center',
            y=-0.05,
            yanchor='top',
            len=0.8,
            thickness=15,
            ticksuffix=''
        ),
        map=dict(
            bounds=dict(west=-74.3, east=-73.7, south=40.45, north=40.95)
        )
    )
    
    return fig


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
            'zohran_mamdani_pct': ':.1f',
            'trump_pct': ':.1f',
            'vote_diff': ':.1f'
        },
        labels={
            'vote_diff': 'Difference (M-T)',
            'zohran_mamdani_pct': 'Mamdani %',
            'trump_pct': 'Trump %',
            'ElectDist': 'District'
        },
        map_style='carto-positron',
        center=config['center'],
        zoom=config['zoom'],
        opacity=0.7
    )
    
    fig.update_layout(
        margin = dict(l=0, r=0, t=40, b=0),
        title = dict(text=f"<b>{config['name']}</b>", x=0.5, xanchor='center', font=dict(size=16)),
        coloraxis_colorbar = dict(title = '← Trump | Mamdani →', ticksuffix='%', len=0.75),
        map=dict(
            bounds=dict(west=-74.3, east=-73.7, south=40.45, north=40.95)
        )
    )
    
    return fig
