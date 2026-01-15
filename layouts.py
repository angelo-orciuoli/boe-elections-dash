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
        dbc.Row([
            dbc.Col([
                dcc.Graph(figure=pres_map, style={'height': '950px'}, config={'scrollZoom': False})
            ], md=6),
            dbc.Col([
                dcc.Graph(figure=mayor_map, style={'height': '950px'}, config={'scrollZoom': False})
            ], md=6)
        ]),
        html.Hr(),
        html.P(
            "Red = Higher support for first candidate | Blue = Higher support for second candidate",
            className="text-center text-muted small"
        )
    ], fluid=True)


def create_borough_tab(borough_maps):
    """Create the Borough Comparison tab content with bivariate choropleth maps."""
    return dbc.Container([
        # Header explaining bivariate scheme
        dbc.Row([
            dbc.Col([
                html.P(
                    "Mamdani (2025 Mayor) vs Trump (2024 President) — Bivariate Analysis",
                    className="text-center text-muted mb-1"
                ),
                html.Div([
                    html.Span("🟣 High Both ", style={'color': '#984ea3', 'fontWeight': 'bold'}),
                    html.Span("🔵 High Mamdani ", style={'color': '#377eb8', 'fontWeight': 'bold'}),
                    html.Span("🔴 High Trump ", style={'color': '#e41a1c', 'fontWeight': 'bold'}),
                    html.Span("⬜ Low Both", style={'color': '#888', 'fontWeight': 'bold'})
                ], className="text-center small")
            ])
        ]),
        
        html.Hr(),
        
        # Row 1: Manhattan and Brooklyn (taller, narrower maps)
        dbc.Row([
            dbc.Col(md=1),
            dbc.Col([
                dcc.Graph(figure=borough_maps['New York'], style={'height': '550px'}, config={'scrollZoom': False})
            ], md=5),
            dbc.Col([
                dcc.Graph(figure=borough_maps['Kings'], style={'height': '550px'}, config={'scrollZoom': False})
            ], md=5),
            dbc.Col(md=1)
        ], className="mb-2"),
        
        # Row 2: Queens and Bronx
        dbc.Row([
            dbc.Col(md=1),
            dbc.Col([
                dcc.Graph(figure=borough_maps['Queens'], style={'height': '550px'}, config={'scrollZoom': False})
            ], md=5),
            dbc.Col([
                dcc.Graph(figure=borough_maps['Bronx'], style={'height': '550px'}, config={'scrollZoom': False})
            ], md=5),
            dbc.Col(md=1)
        ], className="mb-2"),
        
        # Row 3: Staten Island (centered, slightly smaller)
        dbc.Row([
            dbc.Col(md=4),
            dbc.Col([
                dcc.Graph(figure=borough_maps['Richmond'], style={'height': '500px'}, config={'scrollZoom': False})
            ], md=4),
            dbc.Col(md=4)
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
                html.H1("🗽 NYC Election Comparison Dashboard", className="text-center my-3"),
            ])
        ]),
        
        # Tabs
        dbc.Tabs([
            dbc.Tab(citywide_tab, label="Citywide Overview", tab_id="citywide"),
            dbc.Tab(borough_tab, label="Borough Comparison", tab_id="borough"),
        ], id="tabs", active_tab="citywide"),
        
    ], fluid=True)
