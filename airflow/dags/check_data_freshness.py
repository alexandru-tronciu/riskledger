from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import psycopg2


def check_transaction_count():
    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        user="riskledger",
        password="riskledger",
        dbname="riskledger_demo"
    )
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM transactions;")
    count = cur.fetchone()[0]
    print(f"Numărul curent de tranzacții în baza de date: {count}")
    cur.close()
    conn.close()


default_args = {
    "owner": "riskledger",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="check_data_freshness",
    default_args=default_args,
    description="Verifică zilnic volumul de date din tabelul transactions",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["riskledger", "data-quality"],
) as dag:

    check_count = PythonOperator(
        task_id="check_transaction_count",
        python_callable=check_transaction_count,
    )