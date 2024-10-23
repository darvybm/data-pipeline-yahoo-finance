{{ config(materialized='view') }}

WITH extracted_data AS (
    SELECT
        JSONExtractString(_airbyte_data, 'symbol') AS symbol,
        JSONExtractString(_airbyte_data, 'holder') AS holder,
        JSONExtractInt(_airbyte_data, 'shares') AS shares,
        JSONExtractFloat(_airbyte_data, 'value') AS value,
        JSONExtractString(_airbyte_data, 'date') AS date
    FROM {{ source('bank_data_olap', 'public_raw__stream_holders') }}
)
SELECT * FROM extracted_data