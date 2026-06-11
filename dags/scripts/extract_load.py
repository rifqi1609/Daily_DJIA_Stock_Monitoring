import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def extract_and_load_raw():
    load_dotenv(override=True)
    
    # Credential
    DB_USER = os.getenv('STOCK_DB_USER')
    DB_PASSWORD = os.getenv('STOCK_DB_PASS')
    DB_HOST = os.getenv('STOCK_DB_HOST')
    DB_PORT = os.getenv('STOCK_DB_PORT')
    DB_NAME = os.getenv('STOCK_DB_DB')
    
    GCP_PROJECT = os.getenv('GCP_PROJECT_ID')
    
    # Query Data
    sql_query = """
        SELECT * FROM technical_data
        WHERE date >= CURRENT_DATE - INTERVAL '1 day';
    """
    
    # Extract Data from PostgreSQL
    engine_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    pg_engine = create_engine(engine_url)
    
    try:
        df_raw = pd.read_sql(sql_query, pg_engine)
        
        if df_raw.empty:
            return
        
        # Load to BigQuery
        df_raw.to_gbq(
            destination_table='clean_stock_data.stock_dashboard', 
            project_id=GCP_PROJECT,
            if_exists='append'
        )
        
    except Exception as e:
        raise e
        
    finally:
        pg_engine.dispose()

# Execution
if __name__ == '__main__':
    extract_and_load_raw()