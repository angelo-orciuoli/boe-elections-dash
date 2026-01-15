# census_data_cleaner.py

import os
import requests
import pandas as pd
from typing import Optional

# Census API configuration
CENSUS_API_BASE = "https://api.census.gov/data"
ACS_YEAR = 2023  # Most recent 5-year ACS data
ACS_DATASET = "acs/acs5"
NY_STATE_FIPS = "36"  # New York State

# NYC County FIPS codes
NYC_COUNTIES = {
    'New York': '061',  # Manhattan
    'Kings': '047',     # Brooklyn
    'Queens': '081',    # Queens
    'Bronx': '005',     # Bronx
    'Richmond': '085'   # Staten Island
}

# Census variable definitions
CENSUS_VARIABLES = {
    # Median Household Income
    'median_household_income': 'B19013_001E',
    
    # Education Attainment (Population 25 years and over)
    'total_pop_25_plus': 'B15003_001E',  # Total population 25+
    'edu_002': 'B15003_002E',  # No schooling completed
    'edu_003': 'B15003_003E',  # Nursery to 4th grade
    'edu_004': 'B15003_004E',  # 5th and 6th grade
    'edu_005': 'B15003_005E',  # 7th and 8th grade
    'edu_006': 'B15003_006E',  # 9th grade
    'edu_007': 'B15003_007E',  # 10th grade
    'edu_008': 'B15003_008E',  # 11th grade
    'edu_009': 'B15003_009E',  # 12th grade, no diploma
    'edu_010': 'B15003_010E',  # Regular high school diploma
    'edu_011': 'B15003_011E',  # GED or alternative credential
    'edu_012': 'B15003_012E',  # Some college, less than 1 year
    'edu_013': 'B15003_013E',  # Some college, 1 or more years, no degree
    'edu_014': 'B15003_014E',  # Associate's degree
    'edu_015': 'B15003_015E',  # Bachelor's degree
    'edu_016': 'B15003_016E',  # Master's degree
    'hs_graduate': 'B15003_017E',  # Professional degree
    'some_college': 'B15003_018E',  # Doctorate degree
    'associates': 'B15003_020E',  # Associate's degree
    'bachelors': 'B15003_022E',  # Bachelor's degree
    'masters': 'B15003_023E',  # Master's degree
    'professional': 'B15003_024E',  # Professional degree
    'doctorate': 'B15003_025E',  # Doctorate degree
    
    # Race and Ethnicity
    'total_pop': 'B03002_001E',  # Total population
    'white_alone': 'B03002_003E',  # White alone
    'black_alone': 'B03002_004E',  # Black or African American alone
    'native_alone': 'B03002_005E',  # American Indian and Alaska Native alone
    'asian_alone': 'B03002_006E',  # Asian alone
    'pacific_alone': 'B03002_007E',  # Native Hawaiian and Other Pacific Islander alone
    'other_alone': 'B03002_008E',  # Some other race alone
    'two_or_more': 'B03002_009E',  # Two or more races
    'hispanic': 'B03002_012E',  # Hispanic or Latino (of any race)
}


class CensusDataCleaner:
    """Cleans and processes NYC Census demographic data."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the cleaner with a Census API key.
        
        Args:
            api_key: Census API key. If None, reads from CENSUS_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('CENSUS_API_KEY')
        if not self.api_key:
            raise ValueError("Census API key not found. Set CENSUS_API_KEY environment variable or pass api_key parameter.")
        
        self._df_demographics = None

    def load_and_clean(self) -> pd.DataFrame:
        """
        Fetch Census data from API and perform all cleaning steps.
        
        Returns:
            DataFrame with cleaned demographic data by county
        """
        # Fetch raw data from Census API
        df = self._fetch_all_nyc_data()
        
        if df.empty:
            raise ValueError("Failed to fetch Census data from API")
        
        # Clean and process the data
        df = self._clean_data(df)
        
        # Process education percentages
        df = self._process_education_data(df)
        
        # Process race percentages
        df = self._process_race_data(df)
        
        # Select final columns
        df = self._select_final_columns(df)
        
        self._df_demographics = df
        return df

    def _fetch_all_nyc_data(self) -> pd.DataFrame:
        """Fetch Census data for all NYC counties."""
        all_vars = list(CENSUS_VARIABLES.values())
        all_data = []
        
        for county_name, county_fips in NYC_COUNTIES.items():
            print(f"Fetching Census data for {county_name} (county FIPS: {county_fips})...")
            df = self._fetch_county_data(county_fips, all_vars)
            if not df.empty:
                df['county'] = county_name
                all_data.append(df)
        
        if not all_data:
            return pd.DataFrame()
        
        combined = pd.concat(all_data, ignore_index=True)
        return combined

    def _fetch_county_data(self, county_fips: str, variables: list) -> pd.DataFrame:
        """Fetch Census data for all tracts in a county."""
        vars_str = ','.join(variables + ['NAME'])
        url = (
            f"{CENSUS_API_BASE}/{ACS_YEAR}/{ACS_DATASET}"
            f"?get={vars_str}"
            f"&for=tract:*"
            f"&in=state:{NY_STATE_FIPS}&in=county:{county_fips}"
            f"&key={self.api_key}"
        )
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2:
                return pd.DataFrame()
            
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Create GEOID for merging (state + county + tract)
            df['GEOID'] = df['state'] + df['county'] + df['tract']
            
            # Convert numeric columns
            for var in variables:
                if var in df.columns:
                    df[var] = pd.to_numeric(df[var], errors='coerce')
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Census data for county {county_fips}: {e}")
            return pd.DataFrame()

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the raw Census data.
        
        Args:
            df: Raw DataFrame from Census API
        
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Remove rows with missing key data
        df = df[df['B03002_001E'].notna()]  # Must have total population
        df = df[df['B03002_001E'] > 0]  # Must have positive population
        
        # Fill missing numeric values with 0
        numeric_cols = df.select_dtypes(include=['number']).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
        
        return df.reset_index(drop=True)

    def _process_education_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process education data to calculate percentages.
        
        Args:
            df: DataFrame with raw Census education variables
        
        Returns:
            DataFrame with education percentages added
        """
        df = df.copy()
        
        total_25_plus = df['B15003_001E'].fillna(0).replace(0, 1)  # Avoid division by zero
        
        # Less than high school (B15003_002E to B15003_009E)
        less_than_hs_cols = [f'B15003_{i:03d}E' for i in range(2, 10)]
        less_than_hs = pd.Series(0, index=df.index)
        for col in less_than_hs_cols:
            if col in df.columns:
                less_than_hs += df[col].fillna(0)
        df['pct_less_than_hs'] = (less_than_hs / total_25_plus * 100).fillna(0)
        
        # High school only
        if 'B15003_017E' in df.columns:
            df['pct_hs_only'] = (df['B15003_017E'].fillna(0) / total_25_plus * 100).fillna(0)
        else:
            df['pct_hs_only'] = 0
        
        # Some college (no degree)
        if 'B15003_018E' in df.columns:
            df['pct_some_college'] = (df['B15003_018E'].fillna(0) / total_25_plus * 100).fillna(0)
        else:
            df['pct_some_college'] = 0
        
        # Associate's degree
        if 'B15003_020E' in df.columns:
            df['pct_associates'] = (df['B15003_020E'].fillna(0) / total_25_plus * 100).fillna(0)
        else:
            df['pct_associates'] = 0
        
        # Bachelor's degree or higher
        bach_plus_cols = ['B15003_022E', 'B15003_023E', 'B15003_024E', 'B15003_025E']
        bach_plus = pd.Series(0, index=df.index)
        for col in bach_plus_cols:
            if col in df.columns:
                bach_plus += df[col].fillna(0)
        df['pct_bachelors_plus'] = (bach_plus / total_25_plus * 100).fillna(0)
        
        return df

    def _process_race_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process race data to calculate percentages.
        
        Args:
            df: DataFrame with raw Census race variables
        
        Returns:
            DataFrame with race percentages added
        """
        df = df.copy()
        
        total_pop = df['B03002_001E'].fillna(0).replace(0, 1)  # Avoid division by zero
        
        # Calculate percentages for each race category
        if 'B03002_003E' in df.columns:
            df['pct_white'] = (df['B03002_003E'].fillna(0) / total_pop * 100).fillna(0)
        else:
            df['pct_white'] = 0
            
        if 'B03002_004E' in df.columns:
            df['pct_black'] = (df['B03002_004E'].fillna(0) / total_pop * 100).fillna(0)
        else:
            df['pct_black'] = 0
            
        if 'B03002_006E' in df.columns:
            df['pct_asian'] = (df['B03002_006E'].fillna(0) / total_pop * 100).fillna(0)
        else:
            df['pct_asian'] = 0
            
        if 'B03002_012E' in df.columns:
            df['pct_hispanic'] = (df['B03002_012E'].fillna(0) / total_pop * 100).fillna(0)
        else:
            df['pct_hispanic'] = 0
        
        # Other races
        other_cols = ['B03002_005E', 'B03002_007E', 'B03002_008E', 'B03002_009E']
        other_race = pd.Series(0, index=df.index)
        for col in other_cols:
            if col in df.columns:
                other_race += df[col].fillna(0)
        df['pct_other'] = (other_race / total_pop * 100).fillna(0)
        
        # Find majority race
        race_cols = ['pct_white', 'pct_black', 'pct_asian', 'pct_hispanic', 'pct_other']
        available_race_cols = [col for col in race_cols if col in df.columns]
        if available_race_cols:
            df['majority_race'] = df[available_race_cols].idxmax(axis=1).str.replace('pct_', '')
        else:
            df['majority_race'] = 'unknown'
        
        return df

    def _select_final_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Select and rename final columns for output.
        
        Args:
            df: Processed DataFrame
        
        Returns:
            DataFrame with selected columns
        """
        # Rename income column
        df['median_income'] = df['B19013_001E']
        
        # Select key columns
        output_cols = [
            'GEOID', 'county', 'NAME', 'state', 'county_code', 'tract',
            'median_income',
            'pct_less_than_hs', 'pct_hs_only', 'pct_some_college', 
            'pct_associates', 'pct_bachelors_plus',
            'pct_white', 'pct_black', 'pct_asian', 'pct_hispanic', 'pct_other',
            'majority_race'
        ]
        
        # Only include columns that exist
        available_cols = [col for col in output_cols if col in df.columns]
        return df[available_cols].copy()

    @property
    def df_demographics(self) -> pd.DataFrame:
        """Get demographic DataFrame."""
        if self._df_demographics is None:
            self.load_and_clean()
        return self._df_demographics


if __name__ == '__main__':
    # Example usage
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv('.env.local')
    
    # Create cleaner and load data
    cleaner = CensusDataCleaner()
    df = cleaner.load_and_clean()
    
    # Display summary
    print("\n=== Census Data Summary ===")
    print(f"Total tracts: {len(df)}")
    print(f"\nBy County:")
    print(df['county'].value_counts())
    print(f"\nSample data:")
    print(df.head())
    print(f"\nColumns: {list(df.columns)}")
