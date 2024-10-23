{{ config(materialized='view') }}

WITH extracted_data AS (
    SELECT
        JSONExtractString(_airbyte_data, 'symbol') AS symbol,
        JSONExtractString(_airbyte_data, 'firm') AS firm,
        JSONExtractString(_airbyte_data, 'to_grade') AS to_grade,
        JSONExtractString(_airbyte_data, 'from_grade') AS from_grade,
        JSONExtractString(_airbyte_data, 'action') AS action,
        JSONExtractString(_airbyte_data, 'date') AS date
    FROM {{ source('bank_data_olap', 'public_raw__stream_upgrades_downgrades') }}
)
SELECT * FROM extracted_data