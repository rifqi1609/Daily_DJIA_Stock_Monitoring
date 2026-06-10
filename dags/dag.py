import datetime as dt
from datetime import timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# DAG Execution
default_args = {
    'owner': 'rifqi',
    'start_date': dt.datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=1),}

with DAG('Project',
         default_args=default_args,
         schedule_interval='0 6 * * 2-6', 
         catchup=False
         ) as dag:
    
    dataExtraction = BashOperator(
        task_id='run_data_extraction',
        bash_command='python /opt/airflow/dags/scripts/data_extraction.py'
    )
    
    dataMigration = BashOperator(
        task_id='migrate_data',
        bash_command='python /opt/airflow/dags/scripts/extract_load.py'
    )
    
    dbtTransformation = BashOperator(
        task_id='run_dbt_transformation',
        bash_command='cd /opt/airflow/dags/dbt && dbt run'
    )
    
    modelRunning = BashOperator(
        task_id='run_model_deployment_script',
        bash_command='python /opt/airflow/dags/scripts/model_deployment.py'
    )
    
dataExtraction >> dataMigration >> dbtTransformation >> modelRunning