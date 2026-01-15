"""
Layout components for NYC Demographic Analysis Dashboard.
Displays demographic maps for Mamdani and Trump voters.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from create_demographic_maps import (
    load_election_and_demographic_data,
    create_income_map,
    create_education_map,
    create_race_map
)


def create_income_tab():
    """Create the Income Analysis tab content."""
    try:
        gdf = load_election_and_demographic_data()
        fig_mamdani, fig_trump = create_income_map(gdf)
        
        return dbc.Container([
            html.H3("Median Household Income: Mamdani vs Trump Districts", className="text-center mb-4"),
            html.P(
                "Compare median household income in districts where Mamdani and Trump received votes.",
                className="text-center text-muted mb-4"
            ),
            dbc.Row([
                dbc.Col([
                    html.H5("Mamdani Districts", className="text-center mb-2"),
                    dcc.Graph(figure=fig_mamdani, style={'height': '800px'}, config={'scrollZoom': False})
                ], md=6),
                dbc.Col([
                    html.H5("Trump Districts", className="text-center mb-2"),
                    dcc.Graph(figure=fig_trump, style={'height': '800px'}, config={'scrollZoom': False})
                ], md=6)
            ]),
            html.Hr(),
            html.P(
                "Data: US Census Bureau ACS 5-Year Estimates (2023) | NYC Board of Elections",
                className="text-center text-muted small mt-4"
            )
        ], fluid=True)
    except Exception as e:
        return dbc.Container([
            dbc.Alert(
                [
                    html.H4("Error Loading Income Maps", className="alert-heading"),
                    html.P(f"Could not load income maps: {str(e)}"),
                    html.P("Please ensure Census API key is set and data is available."),
                ],
                color="danger"
            )
        ], fluid=True)


def create_education_tab():
    """Create the Education Analysis tab content."""
    try:
        gdf = load_election_and_demographic_data()
        fig_mamdani, fig_trump = create_education_map(gdf)
        
        return dbc.Container([
            html.H3("Education Level (% Bachelor's Degree or Higher): Mamdani vs Trump Districts", 
                   className="text-center mb-4"),
            html.P(
                "Compare education levels in districts where Mamdani and Trump received votes.",
                className="text-center text-muted mb-4"
            ),
            dbc.Row([
                dbc.Col([
                    html.H5("Mamdani Districts", className="text-center mb-2"),
                    dcc.Graph(figure=fig_mamdani, style={'height': '800px'}, config={'scrollZoom': False})
                ], md=6),
                dbc.Col([
                    html.H5("Trump Districts", className="text-center mb-2"),
                    dcc.Graph(figure=fig_trump, style={'height': '800px'}, config={'scrollZoom': False})
                ], md=6)
            ]),
            html.Hr(),
            html.P(
                "Data: US Census Bureau ACS 5-Year Estimates (2023) | NYC Board of Elections",
                className="text-center text-muted small mt-4"
            )
        ], fluid=True)
    except Exception as e:
        return dbc.Container([
            dbc.Alert(
                [
                    html.H4("Error Loading Education Maps", className="alert-heading"),
                    html.P(f"Could not load education maps: {str(e)}"),
                    html.P("Please ensure Census API key is set and data is available."),
                ],
                color="danger"
            )
        ], fluid=True)


def create_race_tab():
    """Create the Race Analysis tab content."""
    try:
        gdf = load_election_and_demographic_data()
        fig_mamdani, fig_trump = create_race_map(gdf)
        
        return dbc.Container([
            html.H3("Majority Race: Mamdani vs Trump Districts", className="text-center mb-4"),
            html.P(
                "Compare racial demographics in districts where Mamdani and Trump received votes.",
                className="text-center text-muted mb-4"
            ),
            dbc.Row([
                dbc.Col([
                    html.H5("Mamdani Districts", className="text-center mb-2"),
                    dcc.Graph(figure=fig_mamdani, style={'height': '800px'}, config={'scrollZoom': False})
                ], md=6),
                dbc.Col([
                    html.H5("Trump Districts", className="text-center mb-2"),
                    dcc.Graph(figure=fig_trump, style={'height': '800px'}, config={'scrollZoom': False})
                ], md=6)
            ]),
            html.Hr(),
            html.P(
                "Data: US Census Bureau ACS 5-Year Estimates (2023) | NYC Board of Elections",
                className="text-center text-muted small mt-4"
            )
        ], fluid=True)
    except Exception as e:
        return dbc.Container([
            dbc.Alert(
                [
                    html.H4("Error Loading Race Maps", className="alert-heading"),
                    html.P(f"Could not load race maps: {str(e)}"),
                    html.P("Please ensure Census API key is set and data is available."),
                ],
                color="danger"
            )
        ], fluid=True)


def create_demographic_app_layout():
    """Create and return the complete demographic app layout."""
    # Build tab contents
    income_tab = create_income_tab()
    education_tab = create_education_tab()
    race_tab = create_race_tab()
    
    # Return full layout
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("🗽 NYC Demographic Analysis: Mamdani & Trump Voters", className="text-center my-3"),
                html.P(
                    "Exploring income, education, and race demographics in districts where each candidate received votes",
                    className="text-center text-muted mb-4"
                )
            ])
        ]),
        
        # Tabs
        dbc.Tabs([
            dbc.Tab(income_tab, label="Income", tab_id="income"),
            dbc.Tab(education_tab, label="Education", tab_id="education"),
            dbc.Tab(race_tab, label="Race", tab_id="race"),
        ], id="tabs", active_tab="income"),
        
    ], fluid=True)
