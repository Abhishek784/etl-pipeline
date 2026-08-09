-- "what's the most recent ARR figure we have for each company
CREATE OR REPLACE VIEW vw_company_arr_latest AS
WITH ranked AS (
    SELECT company_key, observed_date, arr_usd,          -- was arr_used
           COUNT(*)     OVER (PARTITION BY company_key, observed_date) AS observation_count_on_date,
           DENSE_RANK() OVER (PARTITION BY company_key ORDER BY observed_date DESC) AS recency
    FROM fact_arr_observation
)
SELECT company_key, observed_date,
       MEDIAN(arr_usd) AS arr_usd,
       MAX(observation_count_on_date) AS observation_count_on_date
FROM ranked WHERE recency = 1
GROUP BY company_key, observed_date;