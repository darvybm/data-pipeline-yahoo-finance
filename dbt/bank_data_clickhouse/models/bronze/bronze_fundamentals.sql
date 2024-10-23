{{ config(materialized='view') }}

WITH extracted_data AS (
    SELECT
        JSONExtractString(_airbyte_data, 'symbol') AS symbol,
        JSONExtractFloat(_airbyte_data, 'assets') AS assets,
        JSONExtractFloat(_airbyte_data, 'debt') AS debt,
        JSONExtractFloat(_airbyte_data, 'invested_capital') AS invested_capital,
        JSONExtractInt(_airbyte_data, 'shares_issued') AS shares_issued
    FROM {{ source('bank_data_olap', 'public_raw__stream_fundamentals') }}
)
SELECT * FROM extracted_data