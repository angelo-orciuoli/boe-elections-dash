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
        # Hero Section - Two-column layout with subtle background container
        html.Div([
            dbc.Row([
                # Left Column: Title and Description
                dbc.Col([
                    html.H3(
                        "Side-by-Side Election Comparison",
                        className="fw-bold mb-4",
                        style={'color': '#2c3e50'}
                    ),
                    dcc.Markdown('''
                        - **The Goal:** Visualize vote share differences across NYC's election districts for two major elections.
                        - **The Data:** **2024 Presidential** (Harris vs Trump) and **2025 Mayoral** (Mamdani vs Cuomo).
                        - **The Method:** Diverging color scale — **Blue** indicates higher support for the Democratic/Progressive candidate, **Red** indicates higher support for the opposing candidate.
                    ''', style={'fontSize': '16px', 'lineHeight': '1.8', 'color': '#444'})
                ], width=7, className="d-flex flex-column justify-content-center pe-5"),
                
                # Right Column: Intro / Abstract / Essential Questions Placeholder
                dbc.Col([
                    html.Div([
                        html.P(
                            "[ Your intro, abstract, or essential questions go here ]",
                            style={
                                'fontSize': '16px', 
                                'color': '#666', 
                                'fontStyle': 'italic',
                                'textAlign': 'center',
                                'margin': '0'
                            }
                        )
                    ], style={
                        'padding': '30px', 
                        'backgroundColor': 'white', 
                        'borderRadius': '8px', 
                        'border': '2px dashed #ccc',
                        'minHeight': '120px',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center'
                    })
                ], width=5, className="d-flex flex-column align-items-center justify-content-center")
            ], align='center')
        ], style={
            'backgroundColor': '#f8f9fa', 
            'padding': '35px 40px', 
            'borderRadius': '12px',
            'marginBottom': '30px',
            'border': '1px solid #e9ecef'
        }),
        
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
        # Hero Section - Two-column layout with subtle background container
        html.Div([
            dbc.Row([
                # Left Column: Title and Description
                dbc.Col([
                    html.H3(
                        "Bivariate Analysis: Mamdani vs Trump Vote Share",
                        className="fw-bold mb-4",
                        style={'color': '#2c3e50'}
                    ),
                    dcc.Markdown('''
                        - **The Goal:** Identify "anti-establishment" corridors where voters support both populist alternatives.
                        - **The Data:** Comparing **Zohran Mamdani** (2025 Mayor) vs. **Donald Trump** (2024 President).
                        - **The Method:** Using NYC Reality thresholds — **Trump High** (35%+), **Mamdani High** (55%+).
                    ''', style={'fontSize': '16px', 'lineHeight': '1.8', 'color': '#444'})
                ], width=7, className="d-flex flex-column justify-content-center pe-5"),
                
                # Right Column: Legend Image
                dbc.Col([
                    html.Img(
                        src='/assets/bivariate-legend.png',
                        style={'maxWidth': '100%', 'height': 'auto'}
                    ),
                    html.P(
                        "This is a bivariate key that maps the complex political dynamics of NYC districts "
                        "by simultaneously comparing two metrics. The nine distinct color cells represent specific "
                        "intersections of District Vote Share for Mamdani and Trump. Each cell defines a percent range, "
                        "classifying the district support level of the candidates.",
                        className="text-muted small mt-3",
                        style={'fontSize': '16px', 'textAlign': 'left', 'lineHeight': '1.5'}
                    )
                ], width=5, className="d-flex flex-column align-items-center justify-content-center")
            ], align='center')
        ], style={
            'backgroundColor': '#f8f9fa', 
            'padding': '35px 40px', 
            'borderRadius': '12px',
            'marginBottom': '30px',
            'border': '1px solid #e9ecef'
        }),
        
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
                html.H1("Political Landscape of New York City", className="text-center mt-3 mb-2"),
                html.H4("Exploring distribution of political groups and differences in voter behavior across New York City in recent elections", className="text-center text-muted fst-italic mb-3"),
            ])
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
            ], width="auto", className="mx-auto")
        ], className="bg-light py-3 mb-3 rounded"),
        
    ], fluid=True)
