{{ config(
    materialized='incremental',
    unique_key='(date, holder, symbol)',
    on_schema_change='sync_all_columns'
) }}

WITH extracted_data AS (
    SELECT * FROM {{ ref('bronze_holders') }}
)

SELECT
    symbol,
    holder,
    shares,
    value,
    CAST(date AS Date) AS date
FROM extracted_data
WHERE EXTRACT(YEAR FROM date) IN (2023, 2024)