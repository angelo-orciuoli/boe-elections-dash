"""
NYC Demographic Analysis Dashboard
Displays demographic maps (Income, Education, Race) for Mamdani and Trump voters.

Run with: python demographic_dash_app.py
Then open: http://127.0.0.1:8051
"""

import os
from dotenv import load_dotenv
import dash
import dash_bootstrap_components as dbc
from demographic_layouts import create_demographic_app_layout

# Load environment variables from .env.local
load_dotenv('.env.local')

# Initialize app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "NYC Demographic Analysis - Mamdani & Trump Voters"

# Set layout
app.layout = create_demographic_app_layout()


if __name__ == '__main__':
    app.run(debug=True, port=8051)
