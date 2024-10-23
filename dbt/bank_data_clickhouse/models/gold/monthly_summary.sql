{{ config(
    materialized='table',
    unique_key='(symbol, month)',
    on_schema_change='sync_all_columns'
) }}

WITH monthly_data AS (
    SELECT
        toStartOfMonth(CAST(date AS Date)) AS month,  -- Agrupar por mes
        round(AVG(open_price), 2) AS avg_open_price,  -- Precio promedio de apertura redondeado a 2 decimales
        round(AVG(close_price), 2) AS avg_close_price,  -- Precio promedio de cierre redondeado a 2 decimales
        round(AVG(volume), 2) AS avg_volume  -- Volumen promedio redondeado a 2 decimales
    FROM {{ ref('silver_price_data') }}  -- Usamos la tabla silver como fuente
    GROUP BY
        month  -- Agrupamos por símbolo y mes
)

SELECT * FROM monthly_data