"""
Configuration constants for NYC Election Dashboard.
"""

# Borough configuration with display names, map centers, and zoom levels
BOROUGH_CONFIG = {
    'New York': {'name': 'Manhattan', 'center': {'lat': 40.7881, 'lon': -73.9712}, 'zoom': 10.5},
    'Kings': {'name': 'Brooklyn', 'center': {'lat': 40.65, 'lon': -73.9442}, 'zoom': 10.5},
    'Queens': {'name': 'Queens', 'center': {'lat': 40.6725, 'lon': -73.83}, 'zoom': 10},
    'Bronx': {'name': 'Bronx', 'center': {'lat': 40.8568, 'lon': -73.8648}, 'zoom': 11},
    'Richmond': {'name': 'Staten Island', 'center': {'lat': 40.5787, 'lon': -74.1502}, 'zoom': 10.5}
}

# NYC center for citywide view
NYC_CENTER = {'lat': 40.628, 'lon': -73.80}
NYC_ZOOM = 9

# Candidate configurations
MAYORAL_CANDIDATES = ['Zohran Mamdani', 'Andrew Cuomo', 'Curtis Sliwa']
PRESIDENTIAL_CANDIDATES = ['Trump', 'Harris']

# Data file paths
MAYOR_DATA_PATH = 'data/citywide_mayor_citywide.csv'
PRESIDENT_DATA_PATH = 'data/citywide_president_citywide.csv'
SHAPEFILE_PATH = 'data/nyc_districts/nyed.shp'

