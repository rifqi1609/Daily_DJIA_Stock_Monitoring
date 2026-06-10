import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

def extract_and_load_raw():
    load_dotenv(override=True)
    
    # Credential
    PG_USER = os.getenv('POSTGRES_USER')
    PG_PASSWORD = os.getenv('POSTGRES_PASS')
    PG_HOST = os.getenv('POSTGRES_HOST')
    PG_PORT = os.getenv('POSTGRES_PORT')
    PG_DB = os.getenv('POSTGRES_DB')
    
    GCP_PROJECT = os.getenv('GCP_PROJECT_ID')
    
    # Query Data
    sql_query = """
        SELECT * FROM technical_data
        WHERE date >= CURRENT_DATE - INTERVAL '1 day';
    """
    
    # Extract Data from PostgreSQL
    engine_url = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'
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