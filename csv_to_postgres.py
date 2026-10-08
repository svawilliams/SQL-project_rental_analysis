import pandas as pd
from sqlalchemy import create_engine

# 1. Load the CSV
df = pd.read_csv("crime_lsoa_12monthavg.csv")

# 2. Clean column names: lowercase, spaces to underscores
def clean_column(col):
    col = col.strip().lower().replace(" ", "_")
    return col

df.columns = [clean_column(col) for col in df.columns]

# 3. Create connection to Postgres
engine = create_engine("postgresql://postgres:2679@localhost:5432/rental_analysis")

# 4. Write to staging table (auto-creates table, infers column types)
df.to_sql("crime_lsoa_2025avg", engine, if_exists="replace", index=False)

print("Import complete.")
print(f"Rows imported: {len(df)}")
print(f"Columns: {list(df.columns)}")