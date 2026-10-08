# London Rental Market Analysis

A PostgreSQL + Python + Power BI project that answers one question: **which London areas and property types offer the best rental value, given a budget and a set of priorities?**

The project was built as a portfolio piece to demonstrate SQL, data modelling and data engineering skills. It combines about 100 manually collected rental listings with external transport and crime datasets, enriches them in Python and SQL, and exposes the results through SQL views to a Power BI dashboard.

> **Status:** In progress. See [Project status](#project-status) for what is complete and what is still to do.

---

## Table of contents

1. [Project overview](#project-overview)
2. [Tech stack](#tech-stack)
3. [Data sources](#data-sources)
4. [Database design](#database-design)
5. [Methodology](#methodology)
6. [Design decisions](#design-decisions)
7. [Findings](#findings)
8. [Project status](#project-status)
9. [Limitations](#limitations)
10. [Setup](#setup)
11. [Repository notes](#repository-notes)

---

## Project overview

- **Dataset:** 103 rental listings, entered manually into PostgreSQL (the `properties` fact table).
- **Enrichment:** Each property is joined to public transport accessibility (PTAL) scores and neighbourhood-level crime data, and to council tax and utilities costs.
- **Output:** SQL views that feed a Power BI dashboard (Import mode, native PostgreSQL connector). The dashboard reads from views rather than raw tables.

### Project buckets

| Bucket | Scope | Status |
|---|---|---|
| 1 | Data foundation and cleaning | Complete |
| 2 | External data sourcing and enrichment | PTAL scores complete. Greenery enrichment was explored but dropped as too complex for the project scope |
| 3 | Data integration (crime z-scores, percentile ranks, log transforms, surrogate key design) | Substantially complete |
| 4 | SQL analysis layer | In progress, using view-based enrichment |
| 5 | Power BI dashboard | Upcoming |

---

## Tech stack

- **Database:** PostgreSQL, managed through pgAdmin 4
- **Python:** pandas, geopandas, shapely, requests, pyproj, pyogrio (VS Code, virtual environment)
- **Visualisation:** Power BI, connected directly to PostgreSQL via the native connector (Import mode)
- **Version control of queries:** SQL queries saved as `.sql` files

---

## Data sources

| Source | Used for |
|---|---|
| London Datastore: PTAL GeoJSON grid | Public transport accessibility scores per property |
| London Datastore: crime data | LSOA-level crime figures |
| ONS LSOA population-weighted centroids (EPSG:4326, reprojected to EPSG:27700 for buffering) | Spatial linking of properties to LSOAs |
| postcodes.io geocoding API | Geocoding property postcodes |
| Manually collected listings | The 103 `properties` rows |

---

## Database design

The schema follows standard dimensional modelling. `properties` is the fact table, reference tables act as dimensions, and `property_crime_metrics` is a derived fact table at the same grain as `properties`.

### Key tables

| Table | Role |
|---|---|
| `properties` | Fact table, 103 rows |
| `crime_lsoa` / `crime_lsoa_2025avg` | Crime data at LSOA level, including per-outcode averages |
| `crime_scores` / `property_crime_metrics` | Derived crime metrics per property |
| `council_tax_lookup` | Council tax by band/area |
| `utilities` | Monthly utilities costs |
| `lookup_ptal` | PTAL scores |
| `london_outcodes` | Outcode reference data |
| `station_lines` | Station and line reference data |

### Key view

`vw_effective_rent` calculates the true monthly cost of each property:

```sql
ROUND(monthly_rent + COALESCE(council_tax / 12, 0) + COALESCE(monthly_utilities, 0), 2)
```

It uses LEFT JOINs to the council tax and utilities tables. `COALESCE(..., 0)` handles properties where bills are included in the rent. Six `council_tax_id` NULLs were checked and confirmed as expected.

---

## Methodology

### 1. Data import

Raw data lands in permissive **staging tables** first, then is normalised and loaded into the final tables. Surrogate integer keys are used in place of text-based foreign keys for stability.

### 2. Spatial enrichment (Python)

Python scripts (pandas, geopandas, shapely, pyproj, pyogrio) geocode properties via postcodes.io and link them to spatial datasets. Coordinates are reprojected from EPSG:4326 to EPSG:27700 so that buffering can be done in metres.

### 3. Transport accessibility

Each property is matched to a PTAL score from the London Datastore grid.

### 4. Crime scoring

Crime is measured per property and compared against the whole of London:

- **Log transform:** `LN()` is applied because crime counts are heavily right-skewed.
- **Baseline:** The citywide mean and standard deviation (`AVG(LN(...))`, `STDDEV(LN(...))`) come from the **full LSOA distribution**, not from the 103-property sample. This avoids a circular comparison.
- **Z-value:** Each property's log-transformed crime is standardised against that citywide baseline.
- **Percentile rank:** Calculated with a correlated subquery against the full LSOA distribution. This was chosen over `PERCENT_RANK() OVER()` because the window function would only rank within the property sample.
- **Crime category:** A derived tier (an apparent four-tier scheme based on percentile cutoffs).
- **Reusable statistics:** Aggregate statistics such as citywide mean and standard deviation are computed once as named values using CTEs (`WITH` clauses) with `CROSS JOIN`, and reused across queries.

### 5. Effective rent

Rent is combined with council tax and utilities (see `vw_effective_rent` above) so that listings with and without bills included can be compared fairly.

### 6. Analysis layer (in progress)

From Bucket 4 onward, enrichment is done through **views** rather than by altering base tables. One planned piece of logic is an interaction effect between PTAL and the safety factor (a multiplicative relationship), which is parked until both datasets are ready.

---

## Design decisions

| Decision | Rationale |
|---|---|
| Log-transform crime data | Corrects heavy right-skew in crime counts |
| Citywide baseline from the full LSOA distribution | Avoids comparing the sample against itself |
| Correlated subquery for percentile rank | References the full LSOA distribution rather than only the property sample |
| Surrogate integer keys | More stable than text-based foreign keys |
| Staging-then-transform import | Raw data is loaded permissively, then cleaned and normalised |
| `COALESCE(..., 0)` for bills-included properties | Prevents NULLs from breaking effective rent |
| View-based enrichment from Bucket 4 onward | Cleaner and non-destructive. Earlier buckets mutated base tables directly. This is documented as an intentional shift and was not reworked retroactively |
| Greenery enrichment dropped | Too complex for the project scope |
| Dashboard reads from views, not raw tables | Keeps the reporting layer stable as the underlying tables evolve |

---

## Findings

> Results are still being finalised. Add the headline findings here once the analysis layer and dashboard are complete.

- **Crime skews high in the sample.** The properties skew towards higher crime. This is a genuine finding rather than a data error: the listings cluster in denser, more central parts of London.
- _TODO: best value-for-money areas_
- _TODO: relationship between PTAL and rent_
- _TODO: effect of council tax and utilities on effective rent_
- _TODO: relationship between crime and effective rent_
- _TODO: any maps produced from the spatial data_

---

## Project status

### Complete

- Data foundation and cleaning (Bucket 1)
- PTAL enrichment (Bucket 2)
- Most of the data integration work (Bucket 3)

### In progress

- Extending the `crime_scores` table with a z-value, a percentile rank benchmarked against all London outcodes, and a derived crime category. Open questions still to settle:
  - the exact column in `crime_lsoa_2025avg` that holds per-outcode averages
  - whether to apply the `LN()` log transform as in earlier work
  - the percentile cutoffs and labels for the four-tier category scheme
  - whether `crime_scores` is a new table or a rebuild of `property_crime_metrics`
  - whether to use `SELECT` for validation or `ALTER TABLE` / `UPDATE` to persist the results
- Correcting a data error in the `utilities` table, where monthly cost values were assigned in the wrong direction. A `CASE WHEN` update has been started but the exact values are not finalised.

### Still to do

- Finish the crime scoring extension
- Complete the utilities correction
- Build out the SQL analysis layer using views, including the PTAL × safety interaction logic
- Build the Power BI dashboard (Bucket 5)
- Write `data_dictionary.md` for portfolio documentation
- Add the findings section above

---

## Limitations

- **Small, manually collected sample.** 103 listings is enough to demonstrate the method but is not statistically representative of the London rental market.
- **Greenery not included.** It was explored and dropped for scope reasons.
- **Sample skews central.** Properties lean towards denser, higher-crime areas, so conclusions about outer London should be treated with caution.

---

## Setup

1. Install PostgreSQL and pgAdmin 4, and create the project database.
2. Create and activate a Python virtual environment, then install the dependencies:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install pandas geopandas shapely requests pyproj pyogrio
   ```

3. Download the source datasets listed in [Data sources](#data-sources).
4. Run the Python enrichment scripts, then the saved `.sql` files in order (staging, normalisation, enrichment, views).
5. Connect Power BI to PostgreSQL using the native connector in Import mode, and point it at the views.

---

## Repository notes

- SQL queries are saved as `.sql` files.
- A `data_dictionary.md` is planned to document every table, column and view.
- The Python-first enrichment pipeline sits alongside a conventional dimensional model in the database: the SQL enrichment logic is genuine analytical work, not just plumbing.
