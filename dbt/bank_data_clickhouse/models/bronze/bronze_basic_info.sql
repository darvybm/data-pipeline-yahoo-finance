{{ config(materialized='view') }}

WITH extracted_data AS (
    SELECT
        JSONExtractString(_airbyte_data, 'symbol') AS symbol,
        JSONExtractString(_airbyte_data, 'industry') AS industry,
        JSONExtractString(_airbyte_data, 'sector') AS sector,
        JSONExtractInt(_airbyte_data, 'employee_count') AS employee_count,
        JSONExtractString(_airbyte_data, 'city') AS city,
        JSONExtractString(_airbyte_data, 'phone') AS phone,
        JSONExtractString(_airbyte_data, 'state') AS state,
        JSONExtractString(_airbyte_data, 'country') AS country,
        JSONExtractString(_airbyte_data, 'website') AS website,
        JSONExtractString(_airbyte_data, 'address') AS address
    FROM {{ source('bank_data_olap', 'public_raw__stream_basic_info') }}
)

SELECT * FROM extracted_data