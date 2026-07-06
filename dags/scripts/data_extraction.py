import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from yahooquery import Ticker
import time

# ---------------------------------------------------------
# 1. Setup & Configuration
# ---------------------------------------------------------
djia_tickers = [
    'AAPL', 'AMGN', 'AXP', 'BA', 'CAT', 'CRM', 'CSCO', 'CVX', 'DIS', 'DOW', 
    'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 
    'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'V', 'VZ', 'WMT', 'AMZN'
]
index_ticker = '^DJI'

# ---------------------------------------------------------
# 2. Extraction Functions
# ---------------------------------------------------------
def get_proxies(proxy_url):
    """Mengembalikan dictionary proxy jika URL tersedia."""
    if proxy_url:
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    return None

def extract_fundamentals(tickers, proxies=None):
    """Menarik data fundamental lengkap menggunakan yahooquery batching."""
    # Inisiasi ticker dengan proksi
    tickers_obj = Ticker(tickers, proxies=proxies)
    
    # Menarik modul secara batch
    summary = tickers_obj.summary_detail
    key_stats = tickers_obj.key_stats
    financials = tickers_obj.financial_data
    prices = tickers_obj.price
    profiles = tickers_obj.summary_profile
    
    fundamental_data = []
    
    for ticker in tickers:
        try:
            # Cek jika data tidak ditemukan (mengembalikan string error)
            if isinstance(summary.get(ticker), str): 
                print(f"  [-] Data tidak lengkap untuk {ticker}")
                continue
                
            sum_data = summary.get(ticker, {})
            stats_data = key_stats.get(ticker, {})
            fin_data = financials.get(ticker, {})
            
            fundamental_data.append({
                'Ticker': ticker,
                'Company_Name': prices.get(ticker, {}).get('shortName', None),
                'Sector': profiles.get(ticker, {}).get('sector', None),
                'Extraction_Date': datetime.now().date(),
                
                # Valuation
                'Market_Cap': sum_data.get('marketCap', None),
                'Trailing_PE': sum_data.get('trailingPE', None),
                'Forward_PE': sum_data.get('forwardPE', None),
                'Price_to_Book': sum_data.get('priceToBook', None),
                'PEG_Ratio': stats_data.get('pegRatio', None),
                'EV_to_EBITDA': stats_data.get('enterpriseToEbitda', None),
                
                # Profitability
                'ROE': fin_data.get('returnOnEquity', None),
                'ROA': fin_data.get('returnOnAssets', None),
                'Gross_Margin': fin_data.get('grossMargins', None),
                'Operating_Margin': fin_data.get('operatingMargins', None),
                'Profit_Margin': fin_data.get('profitMargins', None),
                
                # Liquidity & Solvency
                'Current_Ratio': fin_data.get('currentRatio', None),
                'Quick_Ratio': fin_data.get('quickRatio', None),
                'Debt_to_Equity': fin_data.get('debtToEquity', None),
                'Cash_per_Share': fin_data.get('totalCashPerShare', None),
                
                # Growth & Risk
                'Revenue_Growth': fin_data.get('revenueGrowth', None),
                'Earnings_Growth': fin_data.get('earningsGrowth', None),
                'Beta': sum_data.get('beta', None),
                'Short_Ratio': stats_data.get('shortRatio', None),
                'Fifty_Two_Week_Change': sum_data.get('fiftyTwoWeekChange', None)
            })
        except Exception as e:
             print(f"  [!] Error fundamental {ticker}: {e}")
             
    return pd.DataFrame(fundamental_data)

def extract_market_index(ticker, proxies=None):
    """Menarik data historis index."""
    try:
        t = Ticker(ticker, proxies=proxies)
        df = t.history(period="5d")
        
        if isinstance(df, pd.DataFrame) and not df.empty:
            df = df.reset_index()
            # Ambil baris terakhir (hari perdagangan paling baru)
            df = df.tail(1).copy()
            df = df[['date', 'close']]
            df.columns = ['Date', 'DJIA_Close']
            
            # Format tanggal (menghapus zona waktu jika ada)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            return df
    except Exception as e:
        print(f" [!] Error Market Index: {e}")
        
    return pd.DataFrame()

def extract_OHLCV(tickers, proxies=None):
    """Menarik data historis teknikal (OHLCV) untuk semua ticker."""
    try:
        t = Ticker(tickers, proxies=proxies)
        # Menarik data secara batch langsung untuk semua saham
        df = t.history(period="5d")
        
        if isinstance(df, pd.DataFrame) and not df.empty:
            df = df.reset_index()
            
            # Mengambil data hari terakhir untuk masing-masing saham
            df_latest = df.groupby('symbol').tail(1).copy()
            
            # Menyesuaikan nama kolom sesuai skema database
            df_latest = df_latest[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
            df_latest.columns = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
            
            # Format tanggal
            df_latest['Date'] = pd.to_datetime(df_latest['Date']).dt.date
            return df_latest
            
    except Exception as e:
        print(f" [!] Error OHLCV: {e}")

    return pd.DataFrame()

# ---------------------------------------------------------
# 3. Execution & Database Loading
# ---------------------------------------------------------
if __name__ == "__main__":
    # Load Environment
    load_dotenv(override=True)
    
    # Setup Proxy
    PROXY_URL = os.getenv('PROXY_URL')
    proxies = get_proxies(PROXY_URL)
    
    if proxies:
        print("Mengeksekusi dengan konfigurasi Proxy...")
    else:
        print("Mengeksekusi TANPA Proxy (Risiko blokir IP tinggi)...")
    
    # DB Config
    DB_USER = os.getenv('STOCK_DB_USER')
    DB_PASSWORD = os.getenv('STOCK_DB_PASS')
    DB_HOST = os.getenv('STOCK_DB_HOST')
    DB_PORT = os.getenv('STOCK_DB_PORT')
    DB_NAME = os.getenv('STOCK_DB_DB')
    
    SCHEMA_NAME = 'public'
    TABLE_FUNDAMENTAL = 'fundamental_data'
    TABLE_MARKET = 'market_data'
    TABLE_TECHNICAL = 'technical_data'

    connection_string = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(connection_string)

    # Eksekusi Ekstraksi Data
    print("Mulai menarik data fundamental...")
    df_fundamentals = extract_fundamentals(djia_tickers, proxies=proxies)
    print(f"-> {len(df_fundamentals)} data fundamental ditarik.")
    
    print("Mulai menarik data market index...")
    df_market = extract_market_index(index_ticker, proxies=proxies)
    
    print("Mulai menarik data teknikal (OHLCV)...")
    df_technicals = extract_OHLCV(djia_tickers, proxies=proxies)
    print(f"-> {len(df_technicals)} baris data teknikal ditarik.")

    # Load ke PostgreSQL (Menggunakan logika idempotensi Anda yang sudah ada)
    try:
        with engine.begin() as connection:
            # 1. Fundamental Data
            if not df_fundamentals.empty:
                extraction_date = df_fundamentals['Extraction_Date'].iloc[0].strftime('%Y-%m-%d')
                connection.execute(text(f"DELETE FROM {SCHEMA_NAME}.{TABLE_FUNDAMENTAL} WHERE \"Extraction_Date\" = '{extraction_date}'"))
                df_fundamentals.to_sql(TABLE_FUNDAMENTAL, engine, schema=SCHEMA_NAME, if_exists='append', index=False)
                print("[OK] Data Fundamental berhasil disimpan.")

            # 2. Market Data
            if not df_market.empty:
                market_dates = pd.to_datetime(df_market['Date']).dt.strftime('%Y-%m-%d').unique()
                market_dates_str = "', '".join(market_dates)
                connection.execute(text(f"DELETE FROM {SCHEMA_NAME}.{TABLE_MARKET} WHERE DATE(\"Date\") IN ('{market_dates_str}')"))
                df_market.to_sql(TABLE_MARKET, engine, schema=SCHEMA_NAME, if_exists='append', index=False)
                print("[OK] Data Index berhasil disimpan.")

            # 3. Technical Data
            if not df_technicals.empty:
                tech_dates = pd.to_datetime(df_technicals['Date']).dt.strftime('%Y-%m-%d').unique()
                tech_dates_str = "', '".join(tech_dates)
                connection.execute(text(f"DELETE FROM {SCHEMA_NAME}.{TABLE_TECHNICAL} WHERE DATE(\"Date\") IN ('{tech_dates_str}')"))
                df_technicals.to_sql(TABLE_TECHNICAL, engine, schema=SCHEMA_NAME, if_exists='append', index=False)
                print("[OK] Data Teknikal berhasil disimpan.")

    except Exception as e:
        print(f"Gagal memuat data ke database: {e}")
        
    finally:
        engine.dispose()
        print("Proses selesai.")