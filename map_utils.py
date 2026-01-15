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


# 3x3 Bivariate choropleth color scheme (9 categories)
# Grid layout: rows = Mamdani (Low/Med/High), cols = Trump (Low/Med/High)
BIVARIATE_COLORS = {
    # Low Mamdani row (bottom)
    'Low M / Low T': '#e8e8e8',      # Light Gray - Disengaged
    'Low M / Med T': '#d48a8a',      # Light Red - Lean Trump
    'Low M / High T': '#b33232',     # Deep Red - Trump Base
    # Medium Mamdani row (middle)
    'Med M / Low T': '#97b0c4',      # Sky Blue - Lean Mamdani
    'Med M / Med T': '#a88a9e',      # Muted Purple - Balanced
    'Med M / High T': '#823055',     # Wine - Trump-leaning crossover
    # High Mamdani row (top)
    'High M / Low T': '#4885c1',     # Strong Blue - Mamdani Base
    'High M / Med T': '#7078a3',     # Slate Blue - Mamdani-leaning crossover
    'High M / High T': '#4c2c58'     # Deep Purple - Strong Crossover
}

# Category order for consistent legend display (bottom-left to top-right)
BIVARIATE_CATEGORY_ORDER = [
    'Low M / Low T', 'Low M / Med T', 'Low M / High T',
    'Med M / Low T', 'Med M / Med T', 'Med M / High T',
    'High M / Low T', 'High M / Med T', 'High M / High T'
]


def assign_bivariate_category(mamdani_pct, trump_pct):
    """
    Assign a 3x3 bivariate category based on NYC-specific thresholds.
    
    Uses asymmetric thresholds to reflect NYC's political distribution:
    - Mamdani: Low (0-35%), Medium (35-55%), High (55-100%)
    - Trump: Low (0-20%), Medium (20-40%), High (40-100%)
    
    Args:
        mamdani_pct: Mamdani vote share percentage (0-100)
        trump_pct: Trump vote share percentage (0-100)
    
    Returns:
        Category string for the 3x3 bivariate classification
    """
    if pd.isna(mamdani_pct) or pd.isna(trump_pct):
        return 'Low M / Low T'  # Default for missing data
    
    # Classify Mamdani (Low 0-35%, Med 35-55%, High 55-100%)
    if mamdani_pct <= 35:
        m_level = 'Low M'
    elif mamdani_pct <= 55:
        m_level = 'Med M'
    else:
        m_level = 'High M'
    
    # Classify Trump (Low 0-20%, Med 20-40%, High 40-100%)
    if trump_pct <= 20:
        t_level = 'Low T'
    elif trump_pct <= 40:
        t_level = 'Med T'
    else:
        t_level = 'High T'
    
    return f'{m_level} / {t_level}'


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
    
    # Assign bivariate categories for borough maps (Mamdani vs Trump)
    gdf['bivariate_category'] = gdf.apply(
        lambda row: assign_bivariate_category(
            row['zohran_mamdani_pct'], 
            row['trump_pct']
        ), axis=1
    )
    
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
        title = '2025 Mayoral Election'
        hover_labels = {
            'zohran_mamdani_pct': 'Mamdani %',
            'andrew_cuomo_pct': 'Cuomo %',
            'curtis_sliwa_pct': 'Sliwa %',
            'ElectDist': 'District'
        }
        hover_data = {
            'ElectDist': True,
            'zohran_mamdani_pct': ':.1f',
            'andrew_cuomo_pct': ':.1f',
            'curtis_sliwa_pct': ':.1f',
            'mayor_diff': False
        }
    else:  # presidential
        col_name = 'pres_diff'
        title = '2024 Presidential Election'
        hover_labels = {
            'harris_pct': 'Harris %',
            'trump_pct': 'Trump %',
            'ElectDist': 'District'
        }
        hover_data = {
            'ElectDist': True,
            'harris_pct': ':.1f',
            'trump_pct': ':.1f',
            'pres_diff': False
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
    
    # Configure legend based on election type and calculate totals
    if election_type == 'mayoral':
        legend_title = '2025 Mayoral Election'
        # Calculate totals from the data
        mamdani_votes = int(gdf['Zohran Mamdani'].sum()) if 'Zohran Mamdani' in gdf.columns else 0
        cuomo_votes = int(gdf['Andrew Cuomo'].sum()) if 'Andrew Cuomo' in gdf.columns else 0
        sliwa_votes = int(gdf['Curtis Sliwa'].sum()) if 'Curtis Sliwa' in gdf.columns else 0
        total_votes = mamdani_votes + cuomo_votes + sliwa_votes
        mamdani_pct = (mamdani_votes / total_votes * 100) if total_votes > 0 else 0
        cuomo_pct = (cuomo_votes / total_votes * 100) if total_votes > 0 else 0
        sliwa_pct = (sliwa_votes / total_votes * 100) if total_votes > 0 else 0
        
        # Build table-style legend with 3 candidates
        legend_text = (
            f'<b>{legend_title}</b><br><br>'
            f'<span style="font-size:11px; color:#666;">   Candidate                Votes         Pct</span><br>'
            f'<span style="color:#2166AC; font-size:16px;">●</span> Zohran Mamdani    {mamdani_votes:>10,}    {mamdani_pct:>5.1f}%<br>'
            f'<span style="color:#B2182B; font-size:16px;">●</span> Andrew Cuomo      {cuomo_votes:>10,}    {cuomo_pct:>5.1f}%<br>'
            f'<span style="color:#DAA520; font-size:16px;">●</span> Curtis Sliwa      {sliwa_votes:>10,}    {sliwa_pct:>5.1f}%'
        )
    else:
        legend_title = '2024 Presidential Election'
        # Calculate totals from the data
        harris_votes = int(gdf['Harris'].sum()) if 'Harris' in gdf.columns else 0
        trump_votes = int(gdf['Trump'].sum()) if 'Trump' in gdf.columns else 0
        total_votes = harris_votes + trump_votes
        harris_pct = (harris_votes / total_votes * 100) if total_votes > 0 else 0
        trump_pct = (trump_votes / total_votes * 100) if total_votes > 0 else 0
        
        # Build table-style legend with 2 candidates
        legend_text = (
            f'<b>{legend_title}</b><br><br>'
            f'<span style="font-size:11px; color:#666;">   Candidate                Votes         Pct</span><br>'
            f'<span style="color:#2166AC; font-size:16px;">●</span> Kamala Harris     {harris_votes:>10,}    {harris_pct:>5.1f}%<br>'
            f'<span style="color:#B2182B; font-size:16px;">●</span> Donald Trump      {trump_votes:>10,}    {trump_pct:>5.1f}%'
        )
    # Determine candidate labels for colorbar based on election type
    if election_type == 'mayoral':
        left_candidate = 'Cuomo'
        right_candidate = 'Mamdani'
    else:
        left_candidate = 'Trump'
        right_candidate = 'Harris'
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=60, b=40),
        title=dict(
            text=f"{title}",
            x=0.5,
            xanchor='center',
            yanchor='middle',
            font=dict(size=28, family='system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif')
        ),
        coloraxis_showscale=True,  # Show the colorbar
        coloraxis_colorbar=dict(
            orientation='h',
            x=0.5,
            y=0.085,
            xanchor='center',
            yanchor='top',
            len=0.7,  # Shortened to make room for side labels
            thickness=15,
            title=None,
            tickvals=[],  # No tick marks
            ticks=''
        ),
        map=dict(
            bounds=dict(west=-74.32, east=-73.65, south=40.45, north=40.95)
        ),
        # Custom legend and colorbar labels using annotations
        annotations=[
            # Vote totals legend (top-left)
            dict(
                x=0.02, y=0.98,
                xref='paper', yref='paper',
                text=legend_text,
                showarrow=False,
                font=dict(size=13, color='black', family='monospace'),
                align='left',
                bgcolor='white',
                bordercolor='rgba(0,0,0,0.1)',
                borderwidth=1,
                borderpad=12,
                xanchor='left', yanchor='top'
            ),
            # Left candidate label (left of colorbar)
            dict(
                x=0.15, y=0.07,
                xref='paper', yref='paper',
                text=f'<b>{left_candidate}</b>',
                showarrow=False,
                font=dict(size=16, color='black'), 
                xanchor='right', yanchor='middle'
            ),
            # Right candidate label (right of colorbar)
            dict(
                x=0.855, y=0.069,
                xref='paper', yref='paper',
                text=f'<b>{right_candidate}</b>',
                showarrow=False,
                font=dict(size=15.5, color='black'), 
                xanchor='left', yanchor='middle'
            )
        ]
    )
    # Custom hovertemplate to hide index
    if election_type == 'mayoral':
        fig.update_traces(
            hovertemplate='<b>District %{customdata[0]}</b><br>Mamdani: %{customdata[1]:.1f}%<br>Cuomo: %{customdata[2]:.1f}%<br>Sliwa: %{customdata[3]:.1f}%<extra></extra>'
        )
    else:
        fig.update_traces(
            hovertemplate='<b>District %{customdata[0]}</b><br>Harris: %{customdata[1]:.1f}%<br>Trump: %{customdata[2]:.1f}%<extra></extra>'
        )
    
    return fig


def create_borough_map(gdf, county_code):
    """Create a bivariate choropleth map for a single borough.
    
    Uses a 2x2 classification based on Mamdani vs Trump vote shares:
    - High M / High T (Purple): Crossover/Populist areas
    - High M / Low T (Blue): Mamdani Base areas
    - Low M / High T (Red): Trump Base areas  
    - Low M / Low T (Grey): Disengaged/Moderate areas
    """
    config = BOROUGH_CONFIG[county_code]
    borough_gdf = gdf[gdf['county'] == county_code].copy()
    
    # Convert to GeoJSON
    geojson = json.loads(borough_gdf.to_json())
    
    # Create choropleth with discrete bivariate categories
    fig = px.choropleth_map(
        borough_gdf,
        geojson=geojson,
        locations=borough_gdf.index,
        color='bivariate_category',
        color_discrete_map=BIVARIATE_COLORS,
        category_orders={'bivariate_category': BIVARIATE_CATEGORY_ORDER},
        hover_data={
            'ElectDist': True,
            'zohran_mamdani_pct': ':.1f',
            'trump_pct': ':.1f',
            'bivariate_category': True
        },
        labels={
            'bivariate_category': 'Category',
            'zohran_mamdani_pct': 'Mamdani %',
            'trump_pct': 'Trump %',
            'ElectDist': 'District'
        },
        map_style='carto-positron',
        center=config['center'],
        zoom=config['zoom'],
        opacity=0.8
    )
    
    # Hide the default legend (using header legend instead)
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        title=dict(text=f"<b>{config['name']}</b>", x=0.5, xanchor='center', font=dict(size=16, family='system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'))
    )
    
    # Custom hovertemplate
    fig.update_traces(
        hovertemplate=(
            '<b>District %{customdata[0]}</b><br>'
            'Mamdani: %{customdata[1]:.1f}%<br>'
            'Trump: %{customdata[2]:.1f}%<br>'
            'Category: %{customdata[3]}<extra></extra>'
        )
    )
    
    return fig
