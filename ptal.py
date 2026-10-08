import pandas as pd
import requests
import geopandas as gpd
from shapely.geometry import Point

# 1. Read the CSV
df = pd.read_csv("full_postcode.csv")

# 2. Get unique postcodes for API call
unique_postcodes = df["full_postcode"].unique()

# 3. Get lat/long via postcodes.io
response = requests.post(
    "https://api.postcodes.io/postcodes",
    json={"postcodes": list(unique_postcodes)}
)
data = response.json()

results = []
for item in data["result"]:
    postcode = item["query"]
    result = item["result"]
    if result is not None:
        results.append({
            "full_postcode": postcode,
            "latitude": result["latitude"],
            "longitude": result["longitude"]
        })
    else:
        print(f"Failed: {postcode}")

geo_df = pd.DataFrame(results)

# 4. Merge coordinates back onto the full 103-row table
df = df.merge(geo_df, on="full_postcode", how="left")

# 5. Build geometry column and GeoDataFrame with geopanda
df["geometry"] = df.apply(lambda row: Point(row["longitude"], row["latitude"]), axis=1)
properties_gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

# 6. Load PTAL grid
ptal_gdf = gpd.read_file("PTAL_2023_Grid_100mx100m_Data.geojson")

# 7. Spatial join
joined = gpd.sjoin(properties_gdf, ptal_gdf, how="left", predicate="within")
print(joined["PTAL_2023"].isna().sum())

# 8. Export final result
export_df = joined[["property_id", "PTAL_2023"]]
export_df.to_csv("ptal_scores.csv", index=False)

# 9. Export lat/long for use in other scripts (e.g. crime radius analysis)
latlong_export_df = joined[["property_id", "latitude", "longitude"]]
latlong_export_df.to_csv("properties_latlong.csv", index=False)