"""
NYC Election Comparison Dashboard
Compares Mamdani (2025 Mayor) vs Trump (2024 President) vote shares by borough.

Run with: python dash_app.py
Then open: http://127.0.0.1:8050
"""

import dash
import dash_bootstrap_components as dbc
from layouts import create_app_layout

# Initialize app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "NYC Election Comparison"

# Set layout
app.layout = create_app_layout()


if __name__ == '__main__':
    app.run(debug=True)
