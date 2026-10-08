SELECT lsoa_name, SUM((m_202501 + m_202502 + m_202503 + m_202504 + m_202505 + m_202506 +
m_202507 + m_202508 + m_202509 + m_202510 + m_202511 + m_202512)/12) AS year_2025 
FROM staging_crime_lsoa
Group by lsoa_name
ORDER BY year_2025 DESC
 