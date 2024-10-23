{{ config(
    materialized='incremental',
    unique_key='symbol',
    on_schema_change='sync_all_columns'
) }}

WITH extracted_data AS (
    SELECT * FROM {{ ref('bronze_fundamentals') }}
)

SELECT
    symbol,
    assets,
    debt,
    invested_capital,
    shares_issued,
    CAST(assets AS Float64) AS assets_float,
    CAST(debt AS Float64) AS debt_float,
    CAST(invested_capital AS Float64) AS invested_capital_float,
    CAST(shares_issued AS Int64) AS shares_issued_int
FROM extracted_data