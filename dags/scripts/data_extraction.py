# Library Preparation
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from sqlalchemy import text
import time
import random

# 1. Setup Session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# DJIA Stocks
djia_tickers = [
    'AAPL', 'AMGN', 'AXP', 'BA', 'CAT', 'CRM', 'CSCO', 'CVX', 'DIS', 'DOW', 
    'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 
    'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'V', 'VZ', 'WMT', 'AMZN'
]
index_ticker = '^DJI'

# 2. Extract Fundamental
def extract_top_20_fundamentals(tickers):
    fundamental_data = []
    
    for idx, ticker in enumerate(tickers, start=1):
        try:
            time.sleep(random.uniform(3, 7)) 
            
            stock = yf.Ticker(ticker, session=session)
            info = stock.info
            
            # Debugging
            if not info or len(info) < 5:
                print(f"DEBUG: Data uncomplete for {ticker}")
            else:
                print(f"DEBUG: {idx}/{len(tickers)} Data complete for {ticker}")
            
            fundamental_data.append({
                'Ticker': ticker,
                'Company_Name': info.get('shortName', None),
                'Sector': info.get('sector', None),
                'Extraction_Date': datetime.now().date(),
                
                # Valuation
                'Market_Cap': info.get('marketCap', None),
                'Trailing_PE': info.get('trailingPE', None),
                'Forward_PE': info.get('forwardPE', None),
                'Price_to_Book': info.get('priceToBook', None),
                'PEG_Ratio': info.get('pegRatio', None),
                'EV_to_EBITDA': info.get('enterpriseToEbitda', None),
                
                # Profitability
                'ROE': info.get('returnOnEquity', None),
                'ROA': info.get('returnOnAssets', None),
                'Gross_Margin': info.get('grossMargins', None),
                'Operating_Margin': info.get('operatingMargins', None),
                'Profit_Margin': info.get('profitMargins', None),
                
                # Liquidity & Solvency
                'Current_Ratio': info.get('currentRatio', None),
                'Quick_Ratio': info.get('quickRatio', None),
                'Debt_to_Equity': info.get('debtToEquity', None),
                'Cash_per_Share': info.get('totalCashPerShare', None),
                
                # Growth & Risk
                'Revenue_Growth': info.get('revenueGrowth', None),
                'Earnings_Growth': info.get('earningsGrowth', None),
                'Beta': info.get('beta', None),
                'Short_Ratio': info.get('shortRatio', None),
                'Fifty_Two_Week_Change': info.get('52WeekChange', None)
            })
        except Exception as e:
            print(f"  [!] Error {ticker}: {e}")
            
    return pd.DataFrame(fundamental_data)

# 3. Extract Index Data
def extract_market_index(): 
    start_str = datetime.now() - timedelta(days=1)
    start_str = start_str.strftime('%Y-%m-%d')
    end_str = datetime.now().strftime('%Y-%m-%d')

    market_data = yf.download(
        index_ticker, 
        start=start_str,
        end=end_str,
        progress=False,
        session=session 
    )
    
    market_df = market_data[['Close']].copy()
    market_df.columns = ['DJIA_Close']
    
    market_df.reset_index(inplace=True)
    return market_df

# 4. Extract OHLCV
def extract_OHLCV(tickers):
    start_str = datetime.now() - timedelta(days=1)
    start_str = start_str.strftime('%Y-%m-%d')
    end_str = datetime.now().strftime('%Y-%m-%d')

    data = yf.download(
        tickers,
        start=start_str,
        end=end_str,
        group_by='ticker',
        progress=False,
        session=session
    )

    technical_data = []
    for ticker in tickers:
        try:
            time.sleep(random.uniform(3, 7))
            if ticker in data and not data[ticker].dropna(how='all').empty:
                df_ticker = data[ticker].copy()
                df_ticker.reset_index(inplace=True)
                df_ticker['Ticker'] = ticker
                df_ticker = df_ticker[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
                technical_data.append(df_ticker)
        except Exception as e:
            print(f" [!] Error {ticker}: {e}")

    if technical_data:
        return pd.concat(technical_data, ignore_index=True)
    return pd.DataFrame()

# 5. Execution & Database Loading
if __name__ == "__main__":
    # 1. Load Environment Variables
    load_dotenv(override=True)
    
    # 2. Database Configuration
    DB_USER = os.getenv('STOCK_DB_USER')
    DB_PASSWORD = os.getenv('STOCK_DB_PASS')
    DB_HOST = os.getenv('STOCK_DB_HOST')
    DB_PORT = os.getenv('STOCK_DB_PORT')
    DB_NAME = os.getenv('STOCK_DB_DB')
    
    SCHEMA_NAME = 'public'
    TABLE_FUNDAMENTAL = 'fundamental_data'
    TABLE_MARKET = 'market_data'
    TABLE_TECHNICAL = 'technical_data'

    # 3. Engine Connection
    connection_string = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(connection_string)

    # 4. Execute Daily Data Extraction
    df_fundamentals = extract_top_20_fundamentals(djia_tickers)
    df_market = extract_market_index()
    df_technicals = extract_OHLCV(djia_tickers)

    # 5. Load to PostgreSQL
    try:
        with engine.begin() as connection:
            
            # Fundamental Data
            if not df_fundamentals.empty:
                extraction_date = df_fundamentals['Extraction_Date'].iloc[0].strftime('%Y-%m-%d')
                connection.execute(text(f"DELETE FROM {SCHEMA_NAME}.{TABLE_FUNDAMENTAL} WHERE \"Extraction_Date\" = '{extraction_date}'"))
                df_fundamentals.to_sql(TABLE_FUNDAMENTAL, engine, schema=SCHEMA_NAME, if_exists='append', index=False)

            # Market Data
            if not df_market.empty:
                market_dates = pd.to_datetime(df_market['Date']).dt.strftime('%Y-%m-%d').unique()
                market_dates_str = "', '".join(market_dates)
                connection.execute(text(f"DELETE FROM {SCHEMA_NAME}.{TABLE_MARKET} WHERE DATE(\"Date\") IN ('{market_dates_str}')"))
                df_market.to_sql(TABLE_MARKET, engine, schema=SCHEMA_NAME, if_exists='append', index=False)

            # Technical Data
            if not df_technicals.empty:
                tech_dates = pd.to_datetime(df_technicals['Date']).dt.strftime('%Y-%m-%d').unique()
                tech_dates_str = "', '".join(tech_dates)
                connection.execute(text(f"DELETE FROM {SCHEMA_NAME}.{TABLE_TECHNICAL} WHERE DATE(\"Date\") IN ('{tech_dates_str}')"))
                df_technicals.to_sql(TABLE_TECHNICAL, engine, schema=SCHEMA_NAME, if_exists='append', index=False)

    except Exception as e:
        raise e
        
    finally:
        engine.dispose()