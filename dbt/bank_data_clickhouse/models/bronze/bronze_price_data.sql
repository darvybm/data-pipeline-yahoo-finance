{{ config(materialized='view') }}

WITH extracted_data AS (
    SELECT
        JSONExtractString(_airbyte_data, 'symbol') AS symbol,
        JSONExtractString(_airbyte_data, 'date') AS date,
        JSONExtractFloat(_airbyte_data, 'open') AS open_price,
        JSONExtractFloat(_airbyte_data, 'high') AS high_price,
        JSONExtractFloat(_airbyte_data, 'low') AS low_price,
        JSONExtractFloat(_airbyte_data, 'close') AS close_price,
        JSONExtractInt(_airbyte_data, 'volume') AS volume
    FROM {{ source('bank_data_olap', 'public_raw__stream_price_data') }}
)
SELECT * FROM extracted_data