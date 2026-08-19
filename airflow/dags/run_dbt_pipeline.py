from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta


default_args = {
    "owner": "riskledger",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="run_dbt_pipeline",
    default_args=default_args,
    description="Rulează transformările dbt (staging + marts) și testele de calitate",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["riskledger", "dbt"],
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir /opt/airflow/.dbt",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_project && dbt test --profiles-dir /opt/airflow/.dbt",
    )

    dbt_run >> dbt_test