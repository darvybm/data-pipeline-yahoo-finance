{{ config(
    materialized='incremental',
    unique_key='(date, symbol)',
    on_schema_change='sync_all_columns'
) }}

WITH extracted_data AS (
    SELECT * FROM {{ ref('bronze_price_data') }}  -- Ya tienes los nombres correctos en la etapa bronze
)

SELECT
    symbol,
    CAST(date AS Date) AS date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
FROM extracted_data
WHERE EXTRACT(YEAR FROM date) IN (2023, 2024)