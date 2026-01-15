"""
Create demographic maps for Mamdani and Trump voters.
Generates 3 maps: Income, Education, and Race demographics.
"""

import os
import json
import geopandas as gpd
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

from config import SHAPEFILE_PATH, NYC_CENTER, NYC_ZOOM, MAYOR_DATA_PATH, PRESIDENT_DATA_PATH
from data_cleaner import ElectionDataCleaner
from census_data_cleaner import CensusDataCleaner


def load_election_and_demographic_data():
    """
    Load election data and Census demographic data, then merge them.
    
    Returns:
        GeoDataFrame with election results and demographic data merged
    """
    # Load election data
    print("Loading election data...")
    cleaner_mayor = ElectionDataCleaner(MAYOR_DATA_PATH, election_type='mayor')
    df_mayor, _, _ = cleaner_mayor.load_and_clean()
    
    cleaner_pres = ElectionDataCleaner(PRESIDENT_DATA_PATH, election_type='president')
    df_pres, _, _ = cleaner_pres.load_and_clean()
    
    # Pivot mayoral data
    mayor_pivot = df_mayor.pivot_table(
        index='ElectDist', columns='vote_choice',
        values='vote_count', aggfunc='sum'
    ).fillna(0)
    mayor_pivot['mayor_total'] = mayor_pivot.sum(axis=1)
    
    # Calculate Mamdani vote share
    if 'Zohran Mamdani' in mayor_pivot.columns:
        mayor_pivot['mamdani_pct'] = (mayor_pivot['Zohran Mamdani'] / mayor_pivot['mayor_total'] * 100).round(2)
    else:
        mayor_pivot['mamdani_pct'] = 0
    
    mayor_pivot = mayor_pivot.reset_index()
    
    # Pivot presidential data
    pres_pivot = df_pres.pivot_table(
        index='ElectDist', columns='vote_choice',
        values='vote_count', aggfunc='sum'
    ).fillna(0)
    pres_pivot['pres_total'] = pres_pivot.sum(axis=1)
    
    # Calculate Trump vote share
    if 'Trump' in pres_pivot.columns:
        pres_pivot['trump_pct'] = (pres_pivot['Trump'] / pres_pivot['pres_total'] * 100).round(2)
    else:
        pres_pivot['trump_pct'] = 0
    
    pres_pivot = pres_pivot.reset_index()
    
    # Load shapefile
    print("Loading shapefile...")
    gdf = gpd.read_file(SHAPEFILE_PATH)
    gdf['ElectDist'] = gdf['ElectDist'].astype(int)
    
    # Merge election data
    gdf = gdf.merge(mayor_pivot[['ElectDist', 'mamdani_pct']], on='ElectDist', how='left')
    gdf = gdf.merge(pres_pivot[['ElectDist', 'trump_pct']], on='ElectDist', how='left')
    
    # Add county info
    county_map = df_mayor[['ElectDist', 'county']].drop_duplicates()
    gdf = gdf.merge(county_map, on='ElectDist', how='left')
    
    # Load Census demographic data
    print("Loading Census demographic data...")
    load_dotenv('.env.local')
    census_cleaner = CensusDataCleaner()
    df_census = census_cleaner.load_and_clean()
    
    # Aggregate Census data by county (since we don't have tract-to-district mapping)
    county_demo = df_census.groupby('county').agg({
        'median_income': 'median',
        'pct_bachelors_plus': 'mean',
        'pct_white': 'mean',
        'pct_black': 'mean',
        'pct_asian': 'mean',
        'pct_hispanic': 'mean',
        'pct_other': 'mean',
    }).reset_index()
    
    # Find majority race for each county
    race_cols = ['pct_white', 'pct_black', 'pct_asian', 'pct_hispanic', 'pct_other']
    county_demo['majority_race'] = county_demo[race_cols].idxmax(axis=1).str.replace('pct_', '')
    
    # Merge demographic data with election districts
    gdf = gdf.merge(county_demo, on='county', how='left')
    
    # Convert to WGS84 for Plotly
    gdf = gdf.to_crs(epsg=4326)
    
    return gdf


def create_income_map(gdf):
    """Create side-by-side maps showing median income for Mamdani vs Trump districts."""
    geojson = json.loads(gdf.to_json())
    
    # Create two maps side by side
    fig_mamdani = px.choropleth_map(
        gdf,
        geojson=geojson,
        locations=gdf.index,
        color='median_income',
        color_continuous_scale='Viridis',
        hover_data={
            'ElectDist': True,
            'mamdani_pct': ':.1f',
            'median_income': '$,.0f'
        },
        labels={
            'ElectDist': 'District',
            'mamdani_pct': 'Mamdani %',
            'median_income': 'Median Income'
        },
        map_style='carto-positron',
        center=NYC_CENTER,
        zoom=NYC_ZOOM,
        opacity=0.8,
        title='Median Household Income: Mamdani Districts'
    )
    
    fig_trump = px.choropleth_map(
        gdf,
        geojson=geojson,
        locations=gdf.index,
        color='median_income',
        color_continuous_scale='Viridis',
        hover_data={
            'ElectDist': True,
            'trump_pct': ':.1f',
            'median_income': '$,.0f'
        },
        labels={
            'ElectDist': 'District',
            'trump_pct': 'Trump %',
            'median_income': 'Median Income'
        },
        map_style='carto-positron',
        center=NYC_CENTER,
        zoom=NYC_ZOOM,
        opacity=0.8,
        title='Median Household Income: Trump Districts'
    )
    
    # Update layouts
    for fig in [fig_mamdani, fig_trump]:
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            map=dict(
                bounds=dict(west=-74.3, east=-73.7, south=40.45, north=40.95)
            )
        )
    
    # Custom hovertemplates
    fig_mamdani.update_traces(
        hovertemplate='<b>District %{customdata[0]}</b><br>Mamdani: %{customdata[1]:.1f}%<br>Median Income: $%{customdata[2]:,.0f}<extra></extra>'
    )
    
    fig_trump.update_traces(
        hovertemplate='<b>District %{customdata[0]}</b><br>Trump: %{customdata[1]:.1f}%<br>Median Income: $%{customdata[2]:,.0f}<extra></extra>'
    )
    
    return fig_mamdani, fig_trump


def create_education_map(gdf):
    """Create side-by-side maps showing education level for Mamdani vs Trump districts."""
    geojson = json.loads(gdf.to_json())
    
    fig_mamdani = px.choropleth_map(
        gdf,
        geojson=geojson,
        locations=gdf.index,
        color='pct_bachelors_plus',
        color_continuous_scale='Blues',
        hover_data={
            'ElectDist': True,
            'mamdani_pct': ':.1f',
            'pct_bachelors_plus': ':.1f'
        },
        labels={
            'ElectDist': 'District',
            'mamdani_pct': 'Mamdani %',
            'pct_bachelors_plus': '% Bachelor\'s+'
        },
        map_style='carto-positron',
        center=NYC_CENTER,
        zoom=NYC_ZOOM,
        opacity=0.8,
        title='% Bachelor\'s Degree or Higher: Mamdani Districts'
    )
    
    fig_trump = px.choropleth_map(
        gdf,
        geojson=geojson,
        locations=gdf.index,
        color='pct_bachelors_plus',
        color_continuous_scale='Blues',
        hover_data={
            'ElectDist': True,
            'trump_pct': ':.1f',
            'pct_bachelors_plus': ':.1f'
        },
        labels={
            'ElectDist': 'District',
            'trump_pct': 'Trump %',
            'pct_bachelors_plus': '% Bachelor\'s+'
        },
        map_style='carto-positron',
        center=NYC_CENTER,
        zoom=NYC_ZOOM,
        opacity=0.8,
        title='% Bachelor\'s Degree or Higher: Trump Districts'
    )
    
    # Update layouts
    for fig in [fig_mamdani, fig_trump]:
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            map=dict(
                bounds=dict(west=-74.3, east=-73.7, south=40.45, north=40.95)
            )
        )
    
    # Custom hovertemplates
    fig_mamdani.update_traces(
        hovertemplate='<b>District %{customdata[0]}</b><br>Mamdani: %{customdata[1]:.1f}%<br>% Bachelor\'s+: %{customdata[2]:.1f}%<extra></extra>'
    )
    
    fig_trump.update_traces(
        hovertemplate='<b>District %{customdata[0]}</b><br>Trump: %{customdata[1]:.1f}%<br>% Bachelor\'s+: %{customdata[2]:.1f}%<extra></extra>'
    )
    
    return fig_mamdani, fig_trump


def create_race_map(gdf):
    """Create side-by-side maps showing majority race for Mamdani vs Trump districts."""
    geojson = json.loads(gdf.to_json())
    
    fig_mamdani = px.choropleth_map(
        gdf,
        geojson=geojson,
        locations=gdf.index,
        color='majority_race',
        color_discrete_sequence=px.colors.qualitative.Set3,
        hover_data={
            'ElectDist': True,
            'mamdani_pct': ':.1f',
            'majority_race': True,
            'pct_white': ':.1f',
            'pct_black': ':.1f',
            'pct_asian': ':.1f',
            'pct_hispanic': ':.1f'
        },
        labels={
            'ElectDist': 'District',
            'mamdani_pct': 'Mamdani %',
            'majority_race': 'Majority Race'
        },
        map_style='carto-positron',
        center=NYC_CENTER,
        zoom=NYC_ZOOM,
        opacity=0.8,
        title='Majority Race: Mamdani Districts'
    )
    
    fig_trump = px.choropleth_map(
        gdf,
        geojson=geojson,
        locations=gdf.index,
        color='majority_race',
        color_discrete_sequence=px.colors.qualitative.Set3,
        hover_data={
            'ElectDist': True,
            'trump_pct': ':.1f',
            'majority_race': True,
            'pct_white': ':.1f',
            'pct_black': ':.1f',
            'pct_asian': ':.1f',
            'pct_hispanic': ':.1f'
        },
        labels={
            'ElectDist': 'District',
            'trump_pct': 'Trump %',
            'majority_race': 'Majority Race'
        },
        map_style='carto-positron',
        center=NYC_CENTER,
        zoom=NYC_ZOOM,
        opacity=0.8,
        title='Majority Race: Trump Districts'
    )
    
    # Update layouts
    for fig in [fig_mamdani, fig_trump]:
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=0),
            map=dict(
                bounds=dict(west=-74.3, east=-73.7, south=40.45, north=40.95)
            )
        )
    
    # Custom hovertemplates
    fig_mamdani.update_traces(
        hovertemplate=(
            '<b>District %{customdata[0]}</b><br>'
            'Mamdani: %{customdata[1]:.1f}%<br>'
            'Majority Race: %{customdata[2]}<br>'
            'White: %{customdata[3]:.1f}% | Black: %{customdata[4]:.1f}%<br>'
            'Asian: %{customdata[5]:.1f}% | Hispanic: %{customdata[6]:.1f}%<extra></extra>'
        )
    )
    
    fig_trump.update_traces(
        hovertemplate=(
            '<b>District %{customdata[0]}</b><br>'
            'Trump: %{customdata[1]:.1f}%<br>'
            'Majority Race: %{customdata[2]}<br>'
            'White: %{customdata[3]:.1f}% | Black: %{customdata[4]:.1f}%<br>'
            'Asian: %{customdata[5]:.1f}% | Hispanic: %{customdata[6]:.1f}%<extra></extra>'
        )
    )
    
    return fig_mamdani, fig_trump


def main():
    """Main function to create all demographic maps."""
    print("=" * 60)
    print("Creating Demographic Maps for Mamdani and Trump Voters")
    print("=" * 60)
    
    # Load data
    gdf = load_election_and_demographic_data()
    
    print(f"\nLoaded data for {len(gdf)} election districts")
    print(f"Counties: {gdf['county'].unique()}")
    
    # Create the 3 map pairs
    print("\n1. Creating Income maps...")
    fig_income_mamdani, fig_income_trump = create_income_map(gdf)
    
    print("2. Creating Education maps...")
    fig_edu_mamdani, fig_edu_trump = create_education_map(gdf)
    
    print("3. Creating Race maps...")
    fig_race_mamdani, fig_race_trump = create_race_map(gdf)
    
    # Save maps as HTML files
    print("\nSaving maps to HTML files...")
    fig_income_mamdani.write_html('demographic_income_mamdani.html')
    fig_income_trump.write_html('demographic_income_trump.html')
    fig_edu_mamdani.write_html('demographic_education_mamdani.html')
    fig_edu_trump.write_html('demographic_education_trump.html')
    fig_race_mamdani.write_html('demographic_race_mamdani.html')
    fig_race_trump.write_html('demographic_race_trump.html')
    
    print("\n✓ All maps created successfully!")
    print("\nFiles created:")
    print("  - demographic_income_mamdani.html")
    print("  - demographic_income_trump.html")
    print("  - demographic_education_mamdani.html")
    print("  - demographic_education_trump.html")
    print("  - demographic_race_mamdani.html")
    print("  - demographic_race_trump.html")
    
    return {
        'income': (fig_income_mamdani, fig_income_trump),
        'education': (fig_edu_mamdani, fig_edu_trump),
        'race': (fig_race_mamdani, fig_race_trump)
    }


if __name__ == '__main__':
    maps = main()
