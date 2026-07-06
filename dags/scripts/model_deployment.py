import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import os
from google.oauth2 import service_account
from google.cloud import bigquery
from dotenv import load_dotenv

# Price & Return Characteristics
def add_price_features(df):
    df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    g = df.groupby("Ticker")["Close"]

    # Return
    df["return_1d"]  = g.pct_change(1)
    df["return_5d"]  = g.pct_change(5)
    df["return_20d"] = g.pct_change(20)

    # Candle Body & Shadow
    df["body_size"]    = (df["Close"] - df["Open"]).abs() / df["Open"]
    df["upper_shadow"]  = (df["High"] - df[["Close","Open"]].max(axis=1)) / df["Open"]
    df["hl_range"]     = (df["High"] - df["Low"]) / df["Open"]   # intraday range
    return df

# Moving Averanges & Trend Characteristics
def add_ma_features(df):
    # SMA and EMA Calculation
    g_close = df.groupby("Ticker")["Close"]
    
    windows = [5, 10, 20, 50, 200]
    for w in windows:
        df[f"temp_sma_{w}"] = g_close.transform(lambda x: x.rolling(w).mean())
        df[f"temp_ema_{w}"] = g_close.transform(lambda x: x.ewm(span=w, adjust=False).mean())
        
    # SMA Distance
    for w in windows:
        df[f"dist_sma_10"] = (df["Close"] - df[f"temp_sma_10"]) / df[f"temp_sma_10"]
        df[f"dist_ema_10"] = (df["Close"] - df[f"temp_ema_10"]) / df[f"temp_ema_10"]

    # Micro Trend
    df["crossover_ema_5_20"] = df["temp_ema_5"] / df["temp_ema_20"]
    
    # Macro Trend
    df["crossover_sma_50_200"] = df["temp_sma_50"] / df["temp_sma_200"]

    # SMA Slope
    g_sma20 = df.groupby("Ticker")["temp_sma_20"]
    df["sma20_slope_5d"] = g_sma20.diff(5) / g_sma20.shift(5)
    
    # Cleaning
    cols_to_drop = [col for col in df.columns if col.startswith('temp_')]
    df = df.drop(columns=cols_to_drop)
    
    return df

# Volatility Characteristics
def add_volatility_features(df):
    # Rolling std return
    for w in [5, 10, 20]:
        df[f"volatility_{w}d"] = df.groupby("Ticker")["return_1d"].transform(lambda x: x.rolling(w).std())
        
    # ATR (Average True Range)
    prev_close = df.groupby("Ticker")["Close"].shift(1)
    
    high_low = df["High"] - df["Low"]
    high_prev_close = (df["High"] - prev_close).abs()
    low_prev_close = (df["Low"] - prev_close).abs()
    
    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
    
    df["atr_14"] = tr.groupby(df["Ticker"]).transform(lambda x: x.ewm(alpha=1/14, adjust=False).mean())
    df["atr_pct"] = df["atr_14"] / df["Close"]

    df = df.drop(columns="atr_14")
    return df

# Momentum & Oscillator Characteristics
def add_momentum_features(df):
    close = df["Close"]
    
    # RSI (Wilder's Smoothing)
    delta = df.groupby("Ticker")["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    ema_gain = gain.groupby(df["Ticker"]).transform(lambda x: x.ewm(alpha=1/14, adjust=False).mean())
    ema_loss = loss.groupby(df["Ticker"]).transform(lambda x: x.ewm(alpha=1/14, adjust=False).mean())
    
    rs = ema_gain / ema_loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    
    # Stochastic %K & %D
    low14 = df.groupby("Ticker")["Low"].transform(lambda x: x.rolling(14).min())
    high14 = df.groupby("Ticker")["High"].transform(lambda x: x.rolling(14).max())
    
    # Williams %R
    df["williams_r"] = -100 * (high14 - close) / (high14 - low14).replace(0, np.nan)
    
    # CCI (Commodity Channel Index)
    tp = (df["High"] + df["Low"] + close) / 3
    sma_tp = tp.groupby(df["Ticker"]).transform(lambda x: x.rolling(20).mean())
    
    mad = tp.groupby(df["Ticker"]).transform(lambda x: x.rolling(20).apply(lambda y: np.mean(np.abs(y - np.mean(y))), raw=True))
    df["cci_20"] = (tp - sma_tp) / (0.015 * mad.replace(0, np.nan))
    return df

# Volume Characteristics
def add_volume_features(df):
    g_vol = df.groupby("Ticker")["Volume"]
    
    # Volume Characteristics
    df["vol_sma20"] = g_vol.transform(lambda x: x.rolling(20).mean())
    df["vol_ratio"] = df["Volume"] / df["vol_sma20"].replace(0, np.nan)
    df["vol_change_1d"] = g_vol.pct_change(1)
    
    # On-Balance Volume (OBV)
    price_sign = np.sign(df.groupby("Ticker")["Close"].diff())
    df["obv"] = (price_sign * df["Volume"]).groupby(df["Ticker"]).cumsum()
    
    # Volume Price Trend (VPT)
    ret = df.groupby("Ticker")["Close"].pct_change()
    df["vpt"] = (ret * df["Volume"]).groupby(df["Ticker"]).cumsum()
    
    # Accumulation/Distribution Line (ADL)
    hl = df["High"] - df["Low"]
    clv = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / hl.replace(0, np.nan)
    clv_vol = clv * df["Volume"]
    
    df["adl"] = clv_vol.groupby(df["Ticker"]).cumsum()
    
    # Chaikin Money Flow (20-period)
    sum_clv_vol = clv_vol.groupby(df["Ticker"]).transform(lambda x: x.rolling(20).sum())
    sum_vol = g_vol.transform(lambda x: x.rolling(20).sum())
    
    df["cmf_20"] = sum_clv_vol / sum_vol.replace(0, np.nan) 
    df = df.drop(columns="vol_sma20")
    return df

# DJIA Index Characteristics
def add_market_features(df, df_market):
    # Market Index Characteristics
    mkt = df_market.copy().sort_values("Date")
    mkt["mkt_return_1d"]  = mkt["DJIA_Close"].pct_change(1)
    mkt["mkt_sma200"]     = mkt["DJIA_Close"].rolling(200).mean()
    mkt["mkt_above_sma200"] = (mkt["DJIA_Close"] > mkt["mkt_sma200"]).astype(int)
    mkt["mkt_vol_20d"]    = mkt["mkt_return_1d"].rolling(20).std()
    mkt_cols = ["Date", "mkt_above_sma200", "mkt_vol_20d", "mkt_return_1d"]
    df = df.merge(mkt[mkt_cols], on="Date", how="left")

    # Backup for Data Delayed
    cols_to_fill = ["mkt_above_sma200", "mkt_vol_20d", "mkt_return_1d"]
    df[cols_to_fill] = df.groupby("Ticker")[cols_to_fill].ffill()
    
    # Rolling Covariance
    def calc_cov(group):
        return group["return_1d"].rolling(60).cov(group["mkt_return_1d"])
    
    var_mkt = df.groupby("Ticker")["mkt_return_1d"].transform(lambda x: x.rolling(60).var())
    cov_rm = df.groupby("Ticker").apply(calc_cov).reset_index(level=0, drop=True)

    df = df.drop(columns=["mkt_return_1d","return_1d"])
    
    # Beta, Alpha, dan Relative Strength
    df["beta_60d"] = cov_rm / var_mkt.replace(0, np.nan)
    return df

# Resistance Characteristics
def add_pivot_features(df):
    g = df.groupby("Ticker")
    high_prev = g["High"].shift(1)
    low_prev = g["Low"].shift(1)
    close_prev = g["Close"].shift(1)
    
    # Pivot Point
    pivot = (high_prev + low_prev + close_prev) / 3
    r1 = (2 * pivot) - low_prev
    s1 = (2 * pivot) - high_prev
    r2 = pivot + (high_prev - low_prev)
    
    # Resistance Characteristics
    cur_close = df["Close"]
    df["dist_pivot"] = (cur_close - pivot) / pivot.replace(0, np.nan)
    df["dist_r1"] = (r1 - cur_close) / cur_close.replace(0, np.nan)
    df["dist_s1"] = (cur_close - s1) / cur_close.replace(0, np.nan)
    df["dist_r2"] = (r2 - cur_close) / cur_close.replace(0, np.nan)
    return df

# Remove Unused Columns
def cleaning(df):
    df = df.drop(columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Date', 'Ticker'])
    df = df.dropna()
    return df

# Predict Data
def model_deployment(df, model):
    y_pred_train = model.predict(df)
    return y_pred_train

# Connection with .env
load_dotenv(override=True)

# Connection to PostgreSQL
def extract_from_postgres():
    # Mengambil kredensial dari .env
    DB_USER = os.getenv('STOCK_DB_USER')
    DB_PASSWORD = os.getenv('STOCK_DB_PASS')
    DB_HOST = os.getenv('STOCK_DB_HOST')
    DB_PORT = os.getenv('STOCK_DB_PORT')
    DB_NAME = os.getenv('STOCK_DB_DB')
    
    db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(db_url)
    
    try:
        query_tech = """
            SELECT * FROM technical_data 
            WHERE "Date" >= CURRENT_DATE - INTERVAL '2 years'
        """
        df_technicals = pd.read_sql(query_tech, con=engine)
        
        query_market = """
            SELECT * FROM market_data 
            WHERE "Date" >= CURRENT_DATE - INTERVAL '2 years'
        """
        df_market = pd.read_sql(query_market, con=engine)
        
        return df_technicals, df_market
        
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()
        
    finally:
        engine.dispose()

# # Connection to BigQuery
# def load_to_bigquery(df):
#     if df.empty:
#         return
    
#     key_path = "/opt/airflow/dags/credentials/bq_key.json"
#     credentials = service_account.Credentials.from_service_account_file(key_path)
#     GCP_PROJECT = os.getenv('GCP_PROJECT_ID')
#     destination = 'clean_stock_data.stock_screening'
    
#     try:
#         df.to_gbq(
#             destination_table=destination,
#             project_id=GCP_PROJECT,
#             if_exists='append',
#             credentials=credentials
#         )

#     except Exception as e:
#         raise e

# Connection to BigQuery
def load_to_bigquery(df):
    if df.empty:
        return
        
    key_path = "/opt/airflow/dags/credentials/bq_key.json"
    credentials = service_account.Credentials.from_service_account_file(key_path)
    GCP_PROJECT = os.getenv('GCP_PROJECT_ID')
    destination = 'clean_stock_data.stock_screening'
    
    try:
        # Inisialisasi client BigQuery API
        client = bigquery.Client(credentials=credentials, project=GCP_PROJECT)
        
        # 1. Ekstrak tanggal unik dari DataFrame untuk mendeteksi batch yang masuk
        dates = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d').unique()
        dates_str = "', '".join(dates)
        
        # 2. Query untuk menghapus data lama di hari yang sama (agar digantikan yang baru)
        delete_query = f"""
            DELETE FROM `{GCP_PROJECT}.{destination}`
            WHERE CAST(Date AS STRING) IN ('{dates_str}')
        """
        
        # Kita bungkus dengan try-except agar skrip tidak gagal (crash) 
        # jika ini adalah eksekusi hari pertama dan tabel di BigQuery belum ada.
        try:
            delete_job = client.query(delete_query)
            delete_job.result() # Menunggu eksekusi DELETE selesai
            print(f"Data lama untuk tanggal {dates_str} berhasil dihapus (jika ada).")
        except Exception as e:
            print(f"Melewati proses DELETE (Tabel mungkin belum dibuat): {e}")

        # 3. Masukkan data (Prediksi model) yang baru
        df.to_gbq(
            destination_table=destination,
            project_id=GCP_PROJECT,
            if_exists='append',  # Karena yang lama sudah dihapus, append akan aman dari duplikat
            credentials=credentials
        )
        print("Data baru berhasil di-append ke BigQuery.")
        
    except Exception as e:
        raise e

# Stock Screening Model Execution
def execute_predictions(df_technicals):
    df_today = df_technicals.groupby('Ticker').tail(1).copy()
    X_today = cleaning(df_today)
    
    # Model Prediction
    model_path = '/opt/airflow/dags/ml_models/final_model.pkl'
    final_model = joblib.load(model_path)
    predictions = model_deployment(X_today, final_model)
    probabilities = final_model.predict_proba(X_today)[:, 1]
    
    # Format Output
    df_today['Prediction'] = predictions
    df_today['Probability'] = probabilities
    
    # Final Output
    df_final_output = df_today[['Date', 'Ticker', 'Prediction', 'Probability']].copy()
    
    # Load to BigQuery
    load_to_bigquery(df_final_output)
    
    return df_final_output

# Execute Functions
if __name__ == "__main__":
    df_technicals, df_market = extract_from_postgres()
    df_technicals = add_price_features(df_technicals)
    df_technicals = add_ma_features(df_technicals)
    df_technicals = add_volatility_features(df_technicals)
    df_technicals = add_momentum_features(df_technicals)
    df_technicals = add_volume_features(df_technicals)
    df_technicals = add_market_features(df_technicals, df_market)
    df_technicals = add_pivot_features(df_technicals)
    execute_predictions(df_technicals)