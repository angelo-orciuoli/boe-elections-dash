"""
Layout components for NYC Election Dashboard.
Provides functions to create Dash Bootstrap layout components.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from config import BOROUGH_CONFIG
from map_utils import load_and_merge_data, create_citywide_comparison_map, create_borough_map


def create_citywide_tab(pres_map, mayor_map):
    """Create the Citywide Overview tab content."""
    return dbc.Container([
        # Maps Row
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=pres_map, style={'height': '1025px'}, config={'scrollZoom': False})
            ], md=6),
            dbc.Col([
                dcc.Graph(figure=mayor_map, style={'height': '1025px'}, config={'scrollZoom': False})
            ], md=6)
        ]),
        html.Hr(),
        html.P(
            "Red = Higher support for first candidate | Blue = Higher support for second candidate",
            className="text-center text-muted small"
        )
    ], fluid=True)


def create_borough_tab(borough_maps):
    """Create the Borough Comparison tab content with 3x3 bivariate choropleth maps."""
    return dbc.Container([
        # Row 1: Manhattan, Brooklyn, Queens
        dbc.Row([
            dbc.Col(md=1),
            dbc.Col([
                dcc.Graph(figure=borough_maps['New York'], style={'height': '600px'}, config={'scrollZoom': False})
            ], md=3),
            dbc.Col([
                dcc.Graph(figure=borough_maps['Kings'], style={'height': '600px'}, config={'scrollZoom': False})
            ], md=4),
            dbc.Col([
                dcc.Graph(figure=borough_maps['Queens'], style={'height': '600px'}, config={'scrollZoom': False})
            ], md=4),
            dbc.Col(md=2)
        ], className="mb-2"),
        
        # Row 2: Bronx and Staten Island
        dbc.Row([
            dbc.Col(md=2),
            dbc.Col([
                dcc.Graph(figure=borough_maps['Bronx'], style={'height': '600px'}, config={'scrollZoom': False})
            ], md=4),
            dbc.Col([
                dcc.Graph(figure=borough_maps['Richmond'], style={'height': '600px'}, config={'scrollZoom': False})
            ], md=4),
            dbc.Col(md=2)
        ]),
        
        # Footer
        html.Hr(),
        html.P(
            "Data: NYC Board of Elections | Hover over districts for details",
            className="text-center text-muted small"
        )
        
    ], fluid=True)


def create_app_layout():
    """Create and return the complete app layout."""
    # Load data once
    gdf = load_and_merge_data()
    
    # Create all borough maps
    borough_maps = {
        county: create_borough_map(gdf, county)
        for county in BOROUGH_CONFIG.keys()
    }
    
    # Create citywide comparison maps
    pres_comparison_map = create_citywide_comparison_map(gdf, 'presidential')
    mayor_comparison_map = create_citywide_comparison_map(gdf, 'mayoral')
    
    # Build tab contents
    citywide_tab = create_citywide_tab(pres_comparison_map, mayor_comparison_map)
    borough_tab = create_borough_tab(borough_maps)
    
    # Return full layout
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("Investigating NYC’s Ideological Paradox", 
                        className="text-center mt-4 mb-2", 
                        style={"fontWeight": "bold", "color": "#2c3e50"})
            ])
        ]),

        # NEW: Description Container
        dbc.Row([
            dbc.Col([
                html.P([
                    "Following Zohran Mamdani’s 2025 mayoral victory, post-election data revealed a striking trend: a notable portion of his winning coalition consisted of voters who had backed Donald Trump just one year prior. This dashboard visualizes the contrast between the two elections to identify the districts where this ideological crossover appears."
                ], 
                className="lead text-center mx-auto mb-4",
                style={"color": "#5a67d8", "lineHeight": "1.6"})
            ], width=12)
        ]),
        
        # Tabs - styled as prominent pill buttons
        dbc.Row([
            dbc.Col([
                dbc.Tabs([
                    dbc.Tab(citywide_tab, label="Overview", tab_id="citywide", 
                            tab_style={"fontSize": "18px", "fontWeight": "500", "color": "#2c3e50"},
                            active_tab_style={"fontSize": "18px", "fontWeight": "500", "color": "#2c3e50", "backgroundColor": "#e8e8e8", "borderRadius": "20px"}),
                    dbc.Tab(borough_tab, label="Borough Comparison", tab_id="borough",
                            tab_style={"fontSize": "18px", "fontWeight": "500", "color": "#2c3e50"},
                            active_tab_style={"fontSize": "18px", "fontWeight": "500", "color": "#2c3e50", "backgroundColor": "#e8e8e8", "borderRadius": "20px"}),
                ], id="tabs", active_tab="citywide", className="nav-pills justify-content-center"),
            ], width=12)
        ], className="bg-light py-3 mb-3 rounded"),
        
    ], fluid=True)
