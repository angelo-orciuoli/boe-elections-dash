# Data Documentation

## Data Preprocessing Summary

Source of Original Datasets: 

[NYC Board of Elections: 2025 Mayoral Election Data](https://vote.nyc/sites/default/files/pdf/election_results/2025/20251104General%20Election/00000100000Citywide%20Mayor%20Citywide%20EDLevel.csv)  | *renamed to <small>`citywide_mayor_citywide.csv`</small> in this repo*

[NYC Board of Elections: 2024 Presidental Election Data](https://www.vote.nyc/sites/default/files/pdf/election_results/2024/20241105General%20Election/00000100000Citywide%20President%20Vice%20President%20Citywide%20EDLevel.csv) | *renamed to <small>`citywide_president_citywide.csv`</small> in this repo*

---

### ElectionDataCleaner Usage

```python
from data_cleaner import ElectionDataCleaner

# Mayoral election
cleaner = ElectionDataCleaner("data/citywide_mayor_citywide.csv", election_type='mayor')
df_candidate, df_ballot_type, merged_districts = cleaner.load_and_clean()

# Presidential election
cleaner = ElectionDataCleaner("data/citywide_president_citywide.csv", election_type='president')
df_candidate, df_ballot_type, merged_districts = cleaner.load_and_clean()
```

---

### Processing Steps

Both datasets share the same raw CSV structure (22 columns). The cleaner performs:

1. **Column reduction** — 18 of 22 columns contain single values and are dropped
2. **Merged district extraction** — Districts marked "COMBINED INTO" are saved to `merged_districts`
3. **Party suffix removal** — Regex removes party affiliations (e.g., "(Republican)")
4. **Vote aggregation** — Multi-party candidates are consolidated by summing votes
5. **Split into DataFrames:**
   - `df_ballot_type`: Ballot method counts
   - `df_candidate`: Candidate vote totals

---

### Election Configurations

| Election | Candidates | Ballot Types |
|----------|------------|--------------|
| **Mayor** | Andrew Cuomo, Curtis Sliwa, Eric Adams, Irene Estrada, Jim Walden, Joseph Hernandez, Zohran Mamdani, Scattered | Public Counter, Absentee/Military, Affidavit, Manually Counted Emergency |
| **President** | Trump, Harris, Scattered | Public Counter, Absentee/Military, Affidavit, Manually Counted Emergency, Federal |

---

### Processed Dataframe Schemas

#### `df_candidate` & `df_ballot_type` schema

| Column                | Description                       |
| --------------------- | --------------------------------- |
| `assembly_district`   | NY State Assembly district number |
| `election_district`   | Polling subdivision within an assembly district |
| `county`   | Borough (New York=Manhattan, Kings=Brooklyn, Richmond=Staten Island) |
| `vote_choice` | Candidate name or ballot method |
| `vote_count` | Number of votes |
| `ElectDist` | Unique district ID: (assembly_district × 1000) + election_district |

---
<br>



#### `merged_districts` schema

| Column        | Description                                                   |
| ------------- | ------------------------------------------------------------- |
| `source_ad`   | Assembly District of the **non-reporting** Election District. |
| `source_ed`   | Election District that did **not** report independently.      |
| `county`      | County (borough) where the non-reporting district is located. |
| `reported_ad` | Assembly District that officially reported the votes.         |
| `reported_ed` | Election District that officially reported the votes.         |
---

<br>

<br>

### NYC District Geospatial Data

[Source: NYC Dept. of City Planning 2025 Election Districts](https://s-media.nyc.gov/agencies/dcp/assets/files/zip/data-tools/bytes/election-districts/nyed_25d.zip)

#### `nyc_districts/` folder contents

| File | Description |
| :--- | :--- |
| `nyed.shp` | Main shapefile containing the election district polygon geometries |
| `nyed.shx` | Shape index file for fast access to geometry records |
| `nyed.dbf` | Attribute table (dBASE format) with district metadata like `ElectDist`, `BoroCode` |
| `nyed.prj` | Projection file defining the coordinate reference system (CRS) |
| `nyed.shp.xml` | XML metadata describing the dataset's source, date, and schema |
---
> **Note:** All five files must remain together in the same folder for GeoPandas to read the shapefile correctly. Only reference `nyed.shp` in code—the other files are loaded automatically.

---

<br>

<br>

### Assembly Districts by County

| County | Assembly Districts |
| :--- | :--- |
| New York | 37, 61, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76 |
| Bronx | 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87 |
| Kings | 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 64 |
| Queens | 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40 |
| Richmond | 61, 62, 63, 64 |