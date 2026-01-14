# data_cleaner.py

import pandas as pd

# Election-specific configurations
ELECTION_CONFIGS = {
    'mayor': {
        'candidates': ['Andrew M. Cuomo', 'Curtis A. Sliwa', 'Eric L. Adams', 'Irene Estrada', 'Jim Walden', 'Joseph Hernandez', 'Zohran Kwame Mamdani', 'Scattered'],
        'ballot_types': ['Public Counter', 'Absentee / Military', 'Affidavit', 'Manually Counted Emergency'],
        'name_map': {'Andrew M. Cuomo': 'Andrew Cuomo', 'Curtis A. Sliwa': 'Curtis Sliwa', 'Eric L. Adams': 'Eric Adams', 'Zohran Kwame Mamdani': 'Zohran Mamdani'}
    },
    'president': {
        'candidates': ['Donald J. Trump / JD Vance', 'Kamala D. Harris / Tim Walz', 'Scattered'],
        'ballot_types': ['Public Counter', 'Absentee / Military', 'Affidavit', 'Manually Counted Emergency', 'Federal'],
        'name_map': {'Donald J. Trump / JD Vance': 'Trump', 'Kamala D. Harris / Tim Walz': 'Harris'}
    }
}


class ElectionDataCleaner:
    """Cleans and processes NYC election data for any election type."""

    def __init__(self, filepath: str, election_type: str = 'mayor'):
        """
        Initialize the cleaner with a CSV file path and election type.
        
        Args:
            filepath: Path to the raw election CSV file.
            election_type: Type of election ('mayor' or 'president')
        """
        if election_type not in ELECTION_CONFIGS:
            raise ValueError(f"Unknown election type: {election_type}. Valid options: {list(ELECTION_CONFIGS.keys())}")
        
        self.filepath = filepath
        self.election_type = election_type
        self.config = ELECTION_CONFIGS[election_type]
        self._df_candidate = None
        self._df_ballot_type = None
        self._merged_districts = None

    def load_and_clean(self) -> tuple:
        """
        Load the CSV and perform all cleaning steps.
        
        Returns:
            Tuple of (df_candidate, df_ballot_type, merged_districts)
        """
        # Load raw data
        df = pd.read_csv(
            self.filepath, header=None, usecols=[11, 12, 13, 14, 20, 21], 
            names=['assembly_district', 'election_district', 'county', 'note', 'vote_choice', 'vote_count'])

        # Convert types
        df[['assembly_district', 'election_district']] = df[['assembly_district', 'election_district']].astype(int)
        df['vote_count'] = df['vote_count'].str.replace(',', '').astype(int)

        # Extract merged districts
        self._merged_districts = self._extract_merged_districts(df)

        # Clean main dataframe
        df = df[df['note'] == 'IN-PLAY'].drop(columns=['note']).reset_index(drop=True)
        df['vote_choice'] = df['vote_choice'].str.replace(r'\s*\(.*\)', '', regex=True)
        df = df.groupby(['assembly_district', 'election_district', 'county', 'vote_choice'], as_index=False)['vote_count'].sum()

        # Split into ballot type and candidate DataFrames
        self._df_ballot_type = df[df['vote_choice'].isin(self.config['ballot_types'])].reset_index(drop=True)
        self._df_candidate = df[df['vote_choice'].isin(self.config['candidates'])].reset_index(drop=True)

        # Shorten candidate names using config
        if self.config['name_map']:
            self._df_candidate['vote_choice'] = self._df_candidate['vote_choice'].replace(self.config['name_map'])

        # Add ElectDist column (AD * 1000 + ED)
        self._df_ballot_type['ElectDist'] = (self._df_ballot_type['assembly_district'] * 1000) + self._df_ballot_type['election_district']
        self._df_candidate['ElectDist'] = (self._df_candidate['assembly_district'] * 1000) + self._df_candidate['election_district']

        return self._df_candidate, self._df_ballot_type, self._merged_districts

    def _extract_merged_districts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and format merged district information."""
        merged = df[df['note'] != 'IN-PLAY']
        merged = merged[['assembly_district', 'election_district', 'county', 'note']].drop_duplicates().reset_index(drop=True)
        merged['reported_ed'] = merged['note'].str[-5:-3].astype(int)
        merged['reported_ad'] = merged['note'].str[-2:].astype(int)
        merged = merged.drop(columns=['note']).rename(columns={
            'assembly_district': 'source_ad', 
            'election_district': 'source_ed'
        })
        return merged

    @property
    def df_candidate(self) -> pd.DataFrame:
        """Get candidate vote DataFrame."""
        if self._df_candidate is None:
            self.load_and_clean()
        return self._df_candidate

    @property
    def df_ballot_type(self) -> pd.DataFrame:
        """Get ballot type DataFrame."""
        if self._df_ballot_type is None:
            self.load_and_clean()
        return self._df_ballot_type

    @property
    def merged_districts(self) -> pd.DataFrame:
        """Get merged districts DataFrame."""
        if self._merged_districts is None:
            self.load_and_clean()
        return self._merged_districts


def get_county_vote_tables(df_candidate: pd.DataFrame) -> dict:
    """
    Create pivot tables of vote counts by assembly district for each county.
    
    Args:
        df_candidate: DataFrame with columns ['county', 'assembly_district', 'vote_choice', 'vote_count']
    
    Returns:
        Dictionary mapping county names to DataFrames with assembly districts as rows and candidates as columns.
    """
    counties = ['New York', 'Kings', 'Queens', 'Bronx', 'Richmond']
    county_dfs = {}

    for county in counties:
        county_dfs[county] = df_candidate[df_candidate['county'] == county].pivot_table(
            index='assembly_district',
            columns='vote_choice',
            values='vote_count',
            aggfunc='sum'
        ).fillna(0).astype(int)

    return county_dfs
