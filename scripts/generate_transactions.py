import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

conn = psycopg2.connect(
    host="localhost",
    port=5435,
    user="riskledger",
    password="riskledger",
    dbname="riskledger_demo"
)
conn.autocommit = True
cur = conn.cursor()

print("Conectat la PostgreSQL cu succes.")

cur.execute("""
    DROP TABLE IF EXISTS transactions;
    DROP TABLE IF EXISTS accounts;

    CREATE TABLE accounts (
        account_id SERIAL PRIMARY KEY,
        owner_name VARCHAR(100),
        iban VARCHAR(34) UNIQUE,
        account_type VARCHAR(20),
        opened_at TIMESTAMP,
        balance NUMERIC(14, 2)
    );

    CREATE TABLE transactions (
        transaction_id BIGSERIAL,
        account_id INT REFERENCES accounts(account_id),
        transaction_type VARCHAR(20),
        amount NUMERIC(14, 2),
        currency VARCHAR(3),
        created_at TIMESTAMP NOT NULL,
        processed_by VARCHAR(50),
        PRIMARY KEY (transaction_id, created_at)
    ) PARTITION BY RANGE (created_at);

    CREATE TABLE transactions_2025 PARTITION OF transactions
        FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
    CREATE TABLE transactions_2026 PARTITION OF transactions
        FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
""")
print("Tabelele 'accounts' și 'transactions' (partiționat) au fost create.")

account_types = ["personal", "business", "savings"]

print("Generez 10.000 de conturi...")
accounts_batch = []
for i in range(10_000):
    accounts_batch.append((
        fake.name(),
        fake.iban(),
        random.choice(account_types),
        fake.date_time_between(start_date="-5y", end_date="-1y"),
        round(random.uniform(100, 50000), 2)
    ))

cur.executemany(
    "INSERT INTO accounts (owner_name, iban, account_type, opened_at, balance) VALUES (%s, %s, %s, %s, %s)",
    accounts_batch
)
print("Conturi generate.")

transaction_types = ["deposit", "withdrawal", "transfer", "payment"]
currencies = ["MDL", "EUR", "USD"]
employees = ["op_ana", "op_ion", "op_maria", "admin_serviciu", "op_vlad"]

TOTAL = 2_000_000
BATCH_SIZE = 20_000

print(f"Generez {TOTAL} de tranzacții...")

batch = []
for i in range(TOTAL):
    batch.append((
        random.randint(1, 10_000),
        random.choice(transaction_types),
        round(random.uniform(5, 15000), 2),
        random.choice(currencies),
        fake.date_time_between(start_date="-1y", end_date="now"),
        random.choice(employees)
    ))

    if len(batch) == BATCH_SIZE:
        cur.executemany(
            "INSERT INTO transactions (account_id, transaction_type, amount, currency, created_at, processed_by) VALUES (%s, %s, %s, %s, %s, %s)",
            batch
        )
        batch = []
        print(f"  ... {i + 1} tranzacții inserate")

if batch:
    cur.executemany(
        "INSERT INTO transactions (account_id, transaction_type, amount, currency, created_at, processed_by) VALUES (%s, %s, %s, %s, %s, %s)",
        batch
    )

print("Generare completă.")

cur.close()
conn.close()
print("Gata! Conexiune închisă.")