{{
    config(materialized='incremental', unique_key=['symbol'], on_schema_change='sync_all_columns')
}}

WITH extracted_data AS (
    SELECT * FROM {{ ref('bronze_basic_info') }}
)

SELECT
    symbol,
    industry,
    sector,
    employee_count,
    city,
    phone,
    state,
    country,
    website,
    address
FROM extracted_data