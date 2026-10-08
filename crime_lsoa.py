import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# 1. Load properties lat/long CSV
props_df = pd.read_csv("properties_latlong.csv")

# 2. Build geometry column and GeoDataFrame for properties
props_df["geometry"] = props_df.apply(lambda row: Point(row["longitude"], row["latitude"]), axis=1)
properties_gdf = gpd.GeoDataFrame(props_df, geometry="geometry", crs="EPSG:4326")

# 3. Load LSOA population-weighted centroids
lsoa_gdf = gpd.read_file("LSOA_PopCentroids_EW_2021_V4.geojson")

# 4. Reproject both to British National Grid (EPSG:27700) so distances are in metres
properties_gdf = properties_gdf.to_crs(epsg=27700)
lsoa_gdf = lsoa_gdf.to_crs(epsg=27700)

# 5. Create buffer column (5km radius circle) around each property, keep original point geometry intact
properties_gdf["buffer_geometry"] = properties_gdf.geometry.buffer(5000)

# 6. Create a separate GeoDataFrame using the buffer as the active geometry for the join
buffer_gdf = properties_gdf.set_geometry("buffer_geometry")

# 7. Spatial join: find which LSOA centroids fall within each property's buffer
# Each row in the result = one (property, LSOA) pair that's within 5km
joined = gpd.sjoin(lsoa_gdf, buffer_gdf, how="inner", predicate="within")

# 8. Load the aggregated 2025 crime data
crime_df = pd.read_csv("crime_lsoa_12monthavg.csv")

# 9. Join crime data onto the (property, LSOA) matches from the spatial join
merged = joined.merge(crime_df, left_on="LSOA21CD", right_on="lsoa_code", how="left")

# 10. Aggregate: mean crime score per property, across all LSOAs captured in its 5km radius
property_crime_scores = merged.groupby("property_id")["average"].mean().reset_index()
property_crime_scores.columns = ["property_id", "crime_score"]

# 11. Export final result
property_crime_scores.to_csv("crime_scores.csv", index=False)

