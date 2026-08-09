-- "what's the most recent ARR figure we have for each company
create or replace view vw_company_latest as 
with ranked as (
    select 
        company_key, observed_date, arr_used,
        count(*) over (partition by company_key, observed_date ) AS observation_count_on_date,
        DENSE_RANK()  OVER (PARTITION BY company_key ORDER BY observed_date DESC) AS most_recent_date
    from
        fact_arr_observation
)
SELECT company_key, observed_date,
       MEDIAN(arr_usd) AS arr_usd,
       MAX(observation_count_on_date) AS observation_count_on_date
FROM ranked WHERE most_recent_date = 1
GROUP BY company_key, observed_date;