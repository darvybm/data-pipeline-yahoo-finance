import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.bash import BashOperator
from scripts.airbyte_sync import AirbyteSync
from scripts.data_api_extractor import extract_data
from scripts.data_api_loader import insert_data
from dotenv import load_dotenv

load_dotenv()

# Función para activar la sincronización de datos desde Airbyte
def trigger_sync():
    airbyteSync = AirbyteSync(
        airbyte_host=os.getenv("AIRBYTE_HOST"),  # Variable de entorno
        connection_id=os.getenv("AIRBYTE_CONNECTION_ID"),  # Variable de entorno
        username=os.getenv("AIRBYTE_USERNAME"),  # Variable de entorno
        password=os.getenv("AIRBYTE_PASSWORD")  # Variable de entorno
    )
    airbyteSync.trigger_sync() # Inicia la sincronización

# Configuración de argumentos por defecto para las tareas del DAG
default_args = {
    'owner': 'Darvy Betances',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'start_date': datetime(2024, 10, 20),
    'catchup': False,
}

# Definición del DAG para el pipeline de datos de Yahoo Finance
dag = DAG(
    'yahoo_finance_data_pipeline',
    default_args=default_args,
    schedule_interval='0 * * * *',  # Ejecuta cada hora
    catchup=False,
    max_active_runs=1,
    tags=['finance', 'etl', 'yahoo'],
)

# Tarea para crear las tablas en PostgreSQL
create_tables_task = PostgresOperator(
    task_id='create_tables',
    postgres_conn_id='postgres-landing-zone',
    sql='/scripts/create_tables.sql',
    dag=dag
)

# Tarea para extraer datos de la API
extract_api_data_task = PythonOperator(
    task_id='extract_api_data',
    python_callable=extract_data,
    provide_context=True,
    dag=dag
)

# Tarea para insertar datos en la zona de aterrizaje
insert_data_landing_zone_task = PythonOperator(
    task_id='insert_data_landing_zone',
    python_callable=insert_data,
    provide_context=True,
    dag=dag
)

# Tarea para sincronizar datos desde Airbyte a ClickHouse
trigger_airbyte_sync_task = PythonOperator(
    task_id='sync_airbyte_to_clickhouse',
    python_callable=trigger_sync,
    dag=dag
)

# Tarea para limpiar la caché de dbt
run_dbt = BashOperator(
    task_id='run_dbt',
    bash_command='cd /opt/airflow/dbt/bank_data_clickhouse/ && dbt run --profiles-dir /opt/airflow/dbt/.dbt/',
    dag=dag
)

# Tarea para ejecutar las pruebas de dbt
run_dbt_tests_task = BashOperator(
    task_id='run_dbt_tests',
    bash_command='cd /opt/airflow/dbt/bank_data_clickhouse/ && dbt test --profiles-dir /opt/airflow/dbt/.dbt/',
    dag=dag
)

# Definición del flujo del pipeline
with dag:
    create_tables_task >> extract_api_data_task >> insert_data_landing_zone_task
    insert_data_landing_zone_task >> trigger_airbyte_sync_task
    trigger_airbyte_sync_task >> run_dbt >> run_dbt_tests_task