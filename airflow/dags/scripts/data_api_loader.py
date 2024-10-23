from airflow.providers.postgres.hooks.postgres import PostgresHook

def insert_data(**kwargs):
    """
    Inserta o actualiza datos en la base de datos PostgreSQL desde XCom.

    Args:
        **kwargs: Argumentos que se pasan a la función, incluyendo el contexto de Airflow.
    """
    # Recupera los datos de XCom
    basic_info = kwargs['ti'].xcom_pull(task_ids='extract_api_data', key='basic_info')
    price_data = kwargs['ti'].xcom_pull(task_ids='extract_api_data', key='price_data')
    fundamentals = kwargs['ti'].xcom_pull(task_ids='extract_api_data', key='fundamentals')
    holders = kwargs['ti'].xcom_pull(task_ids='extract_api_data', key='holders')
    upgrades_downgrades = kwargs['ti'].xcom_pull(task_ids='extract_api_data', key='upgrades_downgrades')

    # Conexión a la base de datos PostgreSQL
    conn = None
    try:
        # Obtiene la conexión de Airflow
        hook = PostgresHook(postgres_conn_id='postgres-landing-zone')
        conn = hook.get_conn()
        cursor = conn.cursor()

        # Insertar o actualizar datos básicos
        for info in basic_info:
            cursor.execute('''
                INSERT INTO basic_info (symbol, industry, sector, employee_count, city, phone, state, country, website, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET
                    industry = EXCLUDED.industry,
                    sector = EXCLUDED.sector,
                    employee_count = EXCLUDED.employee_count,
                    city = EXCLUDED.city,
                    phone = EXCLUDED.phone,
                    state = EXCLUDED.state,
                    country = EXCLUDED.country,
                    website = EXCLUDED.website,
                    address = EXCLUDED.address
            ''', (info['symbol'], info['industry'], info['sector'], info['employee_count'], 
                  info['city'], info['phone'], info['state'], info['country'], 
                  info['website'], info['address']))

        # Insertar o actualizar datos de precios
        for price in price_data:
            cursor.execute('''
                INSERT INTO price_data (symbol, date, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
            ''', (price['symbol'], price['date'], price['open'], price['high'], 
                  price['low'], price['close'], price['volume']))

        # Insertar o actualizar fundamentos
        for fund in fundamentals:
            cursor.execute('''
                INSERT INTO fundamentals (symbol, assets, debt, invested_capital, shares_issued)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET
                    assets = EXCLUDED.assets,
                    debt = EXCLUDED.debt,
                    invested_capital = EXCLUDED.invested_capital,
                    shares_issued = EXCLUDED.shares_issued
            ''', (fund['symbol'], fund['assets'], fund['debt'], fund['invested_capital'], 
                  fund['shares_issued']))

        # Insertar o actualizar accionistas
        for holder in holders:
            cursor.execute('''
                INSERT INTO holders (date, holder, shares, value, symbol)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date, holder) DO UPDATE SET
                    shares = EXCLUDED.shares,
                    value = EXCLUDED.value
            ''', (holder['date'], holder['holder'], holder['shares'], holder['value'], 
                  holder['symbol']))

        # Insertar o actualizar upgrades y downgrades
        for upgrade in upgrades_downgrades:
            cursor.execute('''
                INSERT INTO upgrades_downgrades (date, firm, to_grade, from_grade, action, symbol)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date, firm) DO UPDATE SET
                    to_grade = EXCLUDED.to_grade,
                    from_grade = EXCLUDED.from_grade,
                    action = EXCLUDED.action
            ''', (upgrade['date'], upgrade['firm'], upgrade['to_grade'], upgrade['from_grade'], 
                  upgrade['action'], upgrade['symbol']))

        # Confirmar los cambios
        conn.commit()

    except Exception as e:
        print(f"Error inserting data: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()