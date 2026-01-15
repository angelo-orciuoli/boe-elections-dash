"""
Map creation utilities for NYC Election Dashboard.
Provides functions for loading election data and creating choropleth maps.
"""

import json
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import (
    BOROUGH_CONFIG, NYC_CENTER, NYC_ZOOM,
    MAYORAL_CANDIDATES, MAYOR_DATA_PATH, PRESIDENT_DATA_PATH, SHAPEFILE_PATH
)
from data_cleaner import ElectionDataCleaner


# Bivariate choropleth color scheme
BIVARIATE_COLORS = {
    'High M / High T': '#984ea3',  # Purple - Crossover/Populist
    'High M / Low T': '#377eb8',   # Blue - Mamdani Base
    'Low M / High T': '#e41a1c',   # Red - Trump Base
    'Low M / Low T': '#d9d9d9'     # Grey - Disengaged/Moderate
}

# Category order for consistent legend display
BIVARIATE_CATEGORY_ORDER = ['High M / High T', 'High M / Low T', 'Low M / High T', 'Low M / Low T']


def assign_bivariate_category(mamdani_pct, trump_pct, threshold=50.0):
    """
    Assign a bivariate category based on vote share thresholds.
    
    Args:
        mamdani_pct: Mamdani vote share percentage (0-100)
        trump_pct: Trump vote share percentage (0-100)
        threshold: Threshold for high/low classification (default 50%)
    
    Returns:
        Category string for the 2x2 bivariate classification
    """
    if pd.isna(mamdani_pct) or pd.isna(trump_pct):
        return 'Low M / Low T'  # Default for missing data
    
    if mamdani_pct > threshold and trump_pct > threshold:
        return 'High M / High T'  # Purple - Crossover
    elif mamdani_pct > threshold and trump_pct <= threshold:
        return 'High M / Low T'   # Blue - Mamdani Base
    elif mamdani_pct <= threshold and trump_pct > threshold:
        return 'Low M / High T'   # Red - Trump Base
    else:
        return 'Low M / Low T'    # Grey - Disengaged


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
        title = 'Zohran Mamdani vs Andrew Cuomo'
        colorbar_title = '← Andrew Cuomo | Zohran Mamdani →'
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
        title = 'Kamala Harris vs Donald Trump'
        colorbar_title = '← Donald Trump | Kamala Harris →'
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
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=20),
        title=dict(
            text=f"<b>{title}</b>",
            x=0.5,
            xanchor='center',
            font=dict(size=18)
        ),
        coloraxis_showscale=False,  # Hide the colorbar
        map=dict(
            bounds=dict(west=-74.3, east=-73.7, south=40.45, north=40.95)
        ),
        # Custom legend using a single annotation (unified card)
        annotations=[
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
            )
        ]
    )
    
    # Custom hovertemplate to hide index
    if election_type == 'mayoral':
        # Get Sliwa percentage for hover
        sliwa_pct_col = 'curtis_sliwa_pct' if 'curtis_sliwa_pct' in gdf.columns else None
        if sliwa_pct_col:
            fig.update_traces(
                hovertemplate='<b>District %{customdata[0]}</b><br>Mamdani: %{customdata[1]:.1f}%<br>Cuomo: %{customdata[2]:.1f}%<br>Sliwa: %{customdata[3]:.1f}%<extra></extra>'
            )
        else:
            fig.update_traces(
                hovertemplate='<b>District %{customdata[0]}</b><br>Mamdani: %{customdata[1]:.1f}%<br>Cuomo: %{customdata[2]:.1f}%<extra></extra>'
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
    
    # Hide the default legend (we'll create a custom 2x2 grid)
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        title=dict(text=f"<b>{config['name']}</b>", x=0.5, xanchor='center', font=dict(size=16))
    )
    
    # Add custom 2x2 bivariate legend using shapes and annotations
    # Legend position (paper coordinates)
    lx, ly = 0.02, 0.95  # Top-left corner
    box_size = 0.06  # Size of each color box
    gap = 0.005  # Gap between boxes
    
    # Draw 4 colored boxes in 2x2 grid
    # Row 1 (High M): [High M/Low T (Blue), High M/High T (Purple)]
    # Row 2 (Low M): [Low M/Low T (Grey), Low M/High T (Red)]
    legend_layout = [
        # (x_offset, y_offset, category)
        (0, box_size + gap, 'High M / Low T'),       # Top-left: Blue
        (box_size + gap, box_size + gap, 'High M / High T'),  # Top-right: Purple
        (0, 0, 'Low M / Low T'),                     # Bottom-left: Grey
        (box_size + gap, 0, 'Low M / High T'),       # Bottom-right: Red
    ]
    
    shapes = []
    for x_off, y_off, category in legend_layout:
        shapes.append(dict(
            type='rect',
            xref='paper', yref='paper',
            x0=lx + x_off, y0=ly - box_size - y_off + box_size,
            x1=lx + x_off + box_size, y1=ly - y_off + box_size,
            fillcolor=BIVARIATE_COLORS[category],
            line=dict(color='white', width=1)
        ))
    
    # Add axis labels for the legend
    annotations = [
        # Y-axis label (Mamdani)
        dict(
            x=lx - 0.01, y=ly + box_size/2,
            xref='paper', yref='paper',
            text='<b>M</b>', font=dict(size=10, color='#333'),
            showarrow=False, xanchor='right', yanchor='middle'
        ),
        # X-axis label (Trump)
        dict(
            x=lx + box_size + gap/2, y=ly - box_size - gap - 0.02,
            xref='paper', yref='paper',
            text='<b>T →</b>', font=dict(size=10, color='#333'),
            showarrow=False, xanchor='center', yanchor='top'
        ),
        # Legend title
        dict(
            x=lx + box_size + gap/2, y=ly + box_size + gap + 0.03,
            xref='paper', yref='paper',
            text='<b>Mamdani vs Trump</b>', font=dict(size=9, color='#333'),
            showarrow=False, xanchor='center', yanchor='bottom'
        )
    ]
    
    fig.update_layout(shapes=shapes, annotations=annotations)
    
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
