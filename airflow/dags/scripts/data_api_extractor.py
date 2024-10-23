import time
from airflow.providers.postgres.hooks.postgres import PostgresHook
import yfinance as yf
import time

# Lista de símbolos de bancos que cotizan en la bolsa de EE. UU.
bank_symbols = [
    'JPM', 'BAC', 'WFC', 'MS', 'RY', 'GS', 'HSBC', 'HDB', 'SCHW', 'MUFG',
    'C', 'IBN', 'UBS', 'TD', 'SMFG', 'SAN', 'USB', 'PNC', 'UNCRY', 'NU',
    'BMO', 'IBKR', 'TFC', 'BBVA', 'ITUB', 'BK', 'ING', 'BCS', 'NWG'
]

# Función para extraer la información básica de cada banco
def extract_basic_info(ticker_obj):
    """
    Extrae información básica de un objeto ticker.

    Args:
        ticker_obj: Objeto ticker de yfinance.

    Returns:
        dict: Información básica del banco.
    """
    info = ticker_obj.info
    basic_info = {
        "symbol": ticker_obj.ticker,
        "industry": info.get("industry"),
        "sector": info.get("sector"),
        "employee_count": info.get("fullTimeEmployees"),
        "city": info.get("city"),
        "phone": info.get("phone"),
        "state": info.get("state"),
        "country": info.get("country"),
        "website": info.get("website"),
        "address": info.get("address1")
    }
    return basic_info

# Función para extraer los datos de precios de cada banco
def extract_price_data(ticker_obj):
    """
    Extrae datos de precios históricos de un objeto ticker.

    Args:
        ticker_obj: Objeto ticker de yfinance.

    Returns:
        list: Datos de precios históricos del banco.
    """
    start_date = '2023-01-01'
    end_date = '2024-12-31'
    hist = ticker_obj.history(start=start_date, end=end_date)
    hist['symbol'] = ticker_obj.ticker
    hist.reset_index(inplace=True)
    hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
    hist.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
        'Date': 'date'
    }, inplace=True)
    price_data = hist[['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']].to_dict(orient='records')
    return price_data

# Función para extraer los fundamentos financieros de cada banco
def extract_fundamentals(ticker_obj):
    """
    Extrae fundamentos financieros de un objeto ticker.

    Args:
        ticker_obj: Objeto ticker de yfinance.

    Returns:
        dict: Fundamentos financieros del banco.
    """
    info = ticker_obj.info
    fundamentals = {
        "symbol": ticker_obj.ticker,
        "assets": info.get("totalAssets"),
        "debt": info.get("totalDebt"),
        "invested_capital": info.get("capitalExpenditures"),
        "shares_issued": info.get("sharesOutstanding")
    }
    return fundamentals

# Función para extraer los accionistas institucionales de cada banco
def extract_holders(ticker_obj):
    """
    Extrae la información de accionistas institucionales de un objeto ticker.

    Args:
        ticker_obj: Objeto ticker de yfinance.

    Returns:
        list: Información sobre accionistas institucionales del banco.
    """
    try:
        holders = ticker_obj.institutional_holders
        if holders is not None:
            holders['symbol'] = ticker_obj.ticker
            holders.rename(columns={
                'Date Reported': 'date',
                'Holder': 'holder',
                'Shares': 'shares',
                'Value': 'value'
            }, inplace=True)
            holders['date'] = holders['date'].dt.strftime('%Y-%m-%d')
            return holders[['date', 'holder', 'shares', 'value', 'symbol']].to_dict(orient='records')
    except Exception as e:
        print(f"Error extracting holders for {ticker_obj.ticker}: {e}")
    return []

# Función para extraer upgrades y downgrades de cada banco
def extract_upgrades_downgrades(ticker_obj):
    """
    Extrae información sobre upgrades y downgrades de un objeto ticker.

    Args:
        ticker_obj: Objeto ticker de yfinance.

    Returns:
        list: Información sobre upgrades y downgrades del banco.
    """
    try:
        upgrades_downgrades = ticker_obj.upgrades_downgrades
        upgrades_downgrades.reset_index(inplace=True)
        upgrades_downgrades['GradeDate'] = upgrades_downgrades['GradeDate'].dt.strftime('%Y-%m-%d') 
        upgrades_downgrades.rename(columns={
            'GradeDate': 'date',
            'Firm': 'firm',
            'ToGrade': 'to_grade',
            'FromGrade': 'from_grade',
            'Action': 'action'
        }, inplace=True)
        upgrades_downgrades['symbol'] = ticker_obj.ticker
        return upgrades_downgrades[['date', 'firm', 'to_grade', 'from_grade', 'action', 'symbol']].to_dict(orient='records')
    except Exception as e:
        print(f"Error extracting upgrades/downgrades for {ticker_obj.ticker}: {e}")
    return []

# Función principal para extraer todos los datos de cada banco
def extract_data(**kwargs):
    """
    Función principal para extraer datos de los bancos y almacenarlos en XCom.

    Args:
        **kwargs: Argumentos adicionales, incluyendo la instancia de Airflow Task Instance (ti).
    """
    all_basic_info = []
    all_price_data = []
    all_fundamentals = []
    all_holders = []
    all_upgrades_downgrades = []

    for symbol in bank_symbols:
        ticker_obj = yf.Ticker(symbol)

        all_basic_info.append(extract_basic_info(ticker_obj))
        all_price_data.extend(extract_price_data(ticker_obj))
        all_fundamentals.append(extract_fundamentals(ticker_obj))
        all_holders.extend(extract_holders(ticker_obj))
        all_upgrades_downgrades.extend(extract_upgrades_downgrades(ticker_obj))

        time.sleep(1)

    # Almacenar los resultados en XCom
    kwargs['ti'].xcom_push(key='basic_info', value=all_basic_info)
    kwargs['ti'].xcom_push(key='price_data', value=all_price_data)
    kwargs['ti'].xcom_push(key='fundamentals', value=all_fundamentals)
    kwargs['ti'].xcom_push(key='holders', value=all_holders)
    kwargs['ti'].xcom_push(key='upgrades_downgrades', value=all_upgrades_downgrades)