import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from data_cleaner import ElectionDataCleaner, get_county_vote_tables

# Page config
st.set_page_config(page_title="NYC Election Map", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .block-container {padding-top: 1rem;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {min-width: 200px; max-width: 250px;}
    [data-testid="stSidebar"] .stRadio label p {font-size: 1.1rem; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# Election configurations
ELECTION_CONFIG = {
    'mayor': {
        'title': '🗽 NYC 2025 Mayoral Election Map',
        'file': 'data/citywide_mayor_citywide.csv',
        'candidates': ['Zohran Mamdani', 'Andrew Cuomo', 'Curtis Sliwa'],
        'chart_title': '2025 Mayoral Election',
        'matchups': [('Zohran Mamdani', 'Andrew Cuomo'), ('Zohran Mamdani', 'Curtis Sliwa'),('Andrew Cuomo', 'Curtis Sliwa')]
    },
    'president': {
        'title': '🗽 NYC 2024 Presidential Election Map',
        'file': 'data/citywide_president_citywide.csv',
        'candidates': ['Harris', 'Trump'],
        'chart_title': '2024 Presidential Election',
        'matchups': [('Harris', 'Trump')]
    }
}

# Election selector in sidebar
st.sidebar.title("Election Data")
election_type = st.sidebar.radio(
    " ",
    options=['mayor', 'president'],
    format_func=lambda x: '2025 Mayoral' if x == 'mayor' else '2024 Presidential'
)

st.sidebar.divider()

config = ELECTION_CONFIG[election_type]
st.title(config['title'])


# Load data
@st.cache_data
def load_data(election):
    cfg = ELECTION_CONFIG[election]
    cleaner = ElectionDataCleaner(cfg['file'], election_type=election)
    df_candidate, df_ballot_type, merged_districts = cleaner.load_and_clean()
    gdf_districts = gpd.read_file("data/nyc_districts/nyed.shp")
    return df_candidate, gdf_districts

df_candidate, gdf_districts = load_data(election_type)
candidates = config['candidates']

# Borough mapping for display
BOROUGH_NAMES = {'New York': 'Manhattan', 'Kings': 'Brooklyn', 'Queens': 'Queens', 'Bronx': 'Bronx', 'Richmond': 'Staten Island'}

# Process base data
df_pivot = df_candidate.pivot_table(
    index='ElectDist', columns='vote_choice', 
    values='vote_count', aggfunc='sum'
).fillna(0)
df_pivot['total_votes'] = df_pivot.sum(axis=1)

# Merge with shapes
gdf_districts['ElectDist'] = gdf_districts['ElectDist'].astype(int)
df_pivot.index = df_pivot.index.astype(int)
gdf_map = gdf_districts.merge(df_pivot, on='ElectDist', how='left')

# Add county info
gdf_map = gdf_map.merge(
    df_candidate[['ElectDist', 'county']].drop_duplicates(), 
    on='ElectDist', 
    how='left'
)

# Create tabs
tab1, tab2, tab3 = st.tabs(["Single Candidate", "Compare Candidates", "Summary Statistics"])

# ==================== TAB 1: SINGLE CANDIDATE ====================
with tab1:
    candidates = config['candidates']
    
    # Show header based on election type
    if len(candidates) > 2:
        st.markdown("<h2 style='text-align: center;'>2025 NYC Mayoral Election: Geographic Distribution of Vote Share</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='text-align: center;'>2024 Presidential Election: Geographic Distribution of Vote Share</h2>", unsafe_allow_html=True)
    
    # Initialize candidate selection in session state (reset if out of bounds)
    if 'candidate_idx' not in st.session_state or st.session_state.candidate_idx >= len(candidates):
        st.session_state.candidate_idx = 0
    
    # Create buttons for each candidate (selected = primary, others = secondary)
    cols = st.columns(len(candidates))
    for i, cand in enumerate(candidates):
        with cols[i]:
            is_selected = st.session_state.candidate_idx == i
            if st.button(cand, key=f"c{i}", use_container_width=True, type="primary" if is_selected else "secondary"):
                st.session_state.candidate_idx = i
                st.rerun()
    
    candidate_to_map = candidates[st.session_state.candidate_idx]
    
    # Calculate vote share
    gdf_plot = gdf_map.copy()
    gdf_plot['pct_share'] = (gdf_plot[candidate_to_map] / gdf_plot['total_votes']) * 100
    
    # Plot map
    fig, ax = plt.subplots(figsize=(10,10))
    gdf_plot.plot(
        column='pct_share',
        cmap='Blues',
        linewidth=0.1,
        edgecolor='grey',
        vmax=gdf_plot['pct_share'].max(),
        legend=True,
        legend_kwds={'label': f"% Vote Share for {candidate_to_map}", 'orientation': 'horizontal', 'pad': 0.02, 'aspect': 50},
        missing_kwds={'color': 'lightgrey', 'label': 'No Data'},
        ax=ax
    )
    
    # Borough boundaries
    gdf_boroughs = gdf_plot.dissolve(by='county')
    gdf_boroughs.boundary.plot(ax=ax, color='grey', linewidth=0.75)
    
    ax.set_title(f"{candidate_to_map} Vote Density: City-Level", fontsize=12)
    ax.axis('off')
    st.pyplot(fig)
    
    st.divider()
    st.markdown("<h3 style='text-align: center;'> View by Borough </h3>", unsafe_allow_html=True)

        # selected_boroughs_tab1 = []
        #selected_boroughs_tab1 = ['New York', 'Kings', 'Queens', 'Bronx', 'Richmond']    
        #for county, display_name in BOROUGH_NAMES.items():
        #    is_selected = st.toggle(display_name, value=True, key=f"tab1_{county}")
        #    if is_selected:
        #        selected_boroughs_tab1.append(county)

# ==================== TAB 2: COMPARE CANDIDATES ====================
with tab2:
    matchups = config['matchups']
    matchup_options = [f"{a} vs {b}" for a, b in matchups]
    
    # Show horizontal radio buttons if multiple matchups
    if len(matchups) > 1:
        st.markdown("<h2 style='text-align: center;'>2025 NYC Mayoral Election: Vote Share Differences</h2>", unsafe_allow_html=True)
        
        # Initialize matchup selection in session state
        if 'matchup_idx' not in st.session_state:
            st.session_state.matchup_idx = 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            is_sel = st.session_state.matchup_idx == 0
            if st.button(matchup_options[0], key="m1", use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state.matchup_idx = 0
                st.rerun()
        with col2:
            is_sel = st.session_state.matchup_idx == 1
            if st.button(matchup_options[1], key="m2", use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state.matchup_idx = 1
                st.rerun()
        with col3:
            is_sel = st.session_state.matchup_idx == 2
            if st.button(matchup_options[2], key="m3", use_container_width=True, type="primary" if is_sel else "secondary"):
                st.session_state.matchup_idx = 2
                st.rerun()
        
        matchup_idx = st.session_state.matchup_idx
    else:
        st.markdown("<h2 style='text-align: center;'>2024 Presidential Election: Vote Share Differences</h2>", unsafe_allow_html=True)
        matchup_idx = 0
    
    candidate_a, candidate_b = matchups[matchup_idx]
    
    # Calculate vote share difference
    gdf_compare = gdf_map.copy()
    gdf_compare['pct_a'] = (gdf_compare[candidate_a] / gdf_compare['total_votes']) * 100
    gdf_compare['pct_b'] = (gdf_compare[candidate_b] / gdf_compare['total_votes']) * 100
    gdf_compare['diff'] = gdf_compare['pct_a'] - gdf_compare['pct_b']
    
    # Plot map
    fig, ax = plt.subplots(figsize=(10,10))
    max_diff = gdf_compare['diff'].abs().max()
    gdf_compare.plot(
        column='diff',
        cmap='RdBu',
        linewidth=0.1,
        edgecolor='grey',
        vmin=-max_diff,
        vmax=max_diff,
        legend=True,
        legend_kwds={'label': f"← {candidate_b}  |  {candidate_a} →", 'orientation': 'horizontal', 'pad': 0.02, 'aspect': 50},
        missing_kwds={'color': 'lightgrey'},
        ax=ax
    )
    
    # Borough boundaries
    gdf_boroughs = gdf_compare.dissolve(by='county')
    gdf_boroughs.boundary.plot(ax=ax, color='grey', linewidth=0.75)
    
    ax.set_title(f"{candidate_a} vs {candidate_b}", fontsize=12)
    ax.axis('off')
    st.pyplot(fig)
    
    st.divider()
    st.markdown("---")

    # Borough toggles in horizontal row
    borough_cols = st.columns(5)
    selected_boroughs_tab2b = []
    for i, (county, display_name) in enumerate(BOROUGH_NAMES.items()):
        with borough_cols[i]:
            is_selected = st.toggle(display_name, value=True, key=f"tab2_{county}")
            if is_selected:
                selected_boroughs_tab2b.append(county)

    

# ==================== TAB 3: SUMMARY STATISTICS ====================
with tab3:
    st.subheader("Vote Counts by Assembly District")
    
    county_dfs = get_county_vote_tables(df_candidate)
    
    selected_candidate = st.selectbox(
        "Select Candidate",
        options=candidates,
        key='tab3_candidate'
    )
    
    st.divider()
    
    left_boroughs = ['Kings', 'Queens']
    right_boroughs = ['New York', 'Bronx', 'Richmond']
    
    def display_borough_table(county):
        display_name = BOROUGH_NAMES[county]
        df = county_dfs[county]
        
        table_df = df[[selected_candidate]].copy()
        table_df['Total Votes'] = df.sum(axis=1)
        table_df['Vote Share %'] = (table_df[selected_candidate] / table_df['Total Votes'] * 100).round(1)
        table_df = table_df.reset_index()
        table_df = table_df.rename(columns={'assembly_district': 'Assembly District'})
        
        total_votes = table_df[selected_candidate].sum()
        total_all = table_df['Total Votes'].sum()
        pct = (total_votes / total_all * 100) if total_all > 0 else 0
        table_df = table_df.drop(columns=[selected_candidate])
        
        st.markdown(f"### {display_name}")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Assembly Districts", len(table_df))
        with c2:
            st.metric("Borough Vote Share", f"{pct:.1f}%")
        
        st.dataframe(table_df, hide_index=True)
        st.divider()
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        for county in left_boroughs:
            display_borough_table(county)
    
    with col_right:
        for county in right_boroughs:
            display_borough_table(county)
