{{ config(
    materialized='incremental',
    unique_key='(date, symbol, firm)',
    on_schema_change='sync_all_columns'
) }}

WITH extracted_data AS (
    SELECT * FROM {{ ref('bronze_upgrades_downgrades') }}
)

SELECT
    symbol,
    firm,
    from_grade,
    to_grade,
    action,
    CAST(date AS Date) AS date
FROM extracted_data
WHERE EXTRACT(YEAR FROM date) IN (2023, 2024)c