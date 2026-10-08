UPDATE properties_crime
SET crime_category = CASE
    WHEN z_log < -0.5 THEN 'Low'
    WHEN z_log BETWEEN -0.5 AND 0.5 THEN 'Medium'
	WHEN z_log BETWEEN 0.5 AND 1.5 THEN 'High'
    ELSE 'Very high'
END;