# Vote Tables Documentation

## `get_county_vote_tables` Function

**Location:** `data_cleaner.py`

### Purpose
Creates pivot tables of vote counts grouped by assembly district for each NYC county (borough).

### Usage

```python
from data_cleaner import ElectionDataCleaner, get_county_vote_tables

cleaner = ElectionDataCleaner("citywide_mayor_citywide.csv")
df_candidate, df_ballot_type, merged_districts = cleaner.load_and_clean()

county_dfs = get_county_vote_tables(df_candidate)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `df_candidate` | `pd.DataFrame` | DataFrame with columns: `county`, `assembly_district`, `vote_choice`, `vote_count` |

### Returns

| Type | Description |
|------|-------------|
| `dict` | Dictionary mapping county names to DataFrames |

**Keys:** `'New York'`, `'Kings'`, `'Queens'`, `'Bronx'`, `'Richmond'`

**DataFrame structure:**
- **Index:** `assembly_district` (int)
- **Columns:** One per candidate (vote counts)

### Example Access

```python
# Get Brooklyn table
county_dfs['Kings']

# Get specific cell value
county_dfs['Kings'].loc[57, 'Zohran Mamdani']

# Get row for Assembly District 65 in Manhattan
county_dfs['New York'].loc[65]
```

---

## Summary Statistics Tab (Streamlit)

**Location:** `app.py` — Tab 3

### Features

1. **Borough Selector** — Dropdown to choose which borough to view
2. **Summary Metrics:**
   - Total Assembly Districts
   - Total Votes
   - Leading Candidate
3. **Interactive Table** — Vote counts by assembly district for main candidates

### Columns Displayed

| Column | Description |
|--------|-------------|
| `Zohran Mamdani` | Votes for Mamdani |
| `Andrew Cuomo` | Votes for Cuomo |
| `Curtis Sliwa` | Votes for Sliwa |
| `Total Votes` | Sum of all candidates |

### Borough Mapping

| County Code | Display Name |
|-------------|--------------|
| `New York` | Manhattan |
| `Kings` | Brooklyn |
| `Queens` | Queens |
| `Bronx` | Bronx |
| `Richmond` | Staten Island |
