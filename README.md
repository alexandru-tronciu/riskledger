# riskledger

A data engineering pipeline built around a synthetic bank: transaction
volume at a scale that actually stresses the database, an Airflow
scheduler that runs on its own instead of being triggered by hand, and a
dbt layer that turns raw operational tables into something a compliance
analyst could actually query. The end goal is a system that flags
suspicious activity automatically — duplicate approvals, unusual volume
on an account, that kind of thing — but that part isn't built yet. This
README describes what's actually running today, not the full plan.

## Status: in progress

I'm building this in layers, and I'd rather commit each layer once it
works than sit on everything until the whole thing is "done." Right now:

- **Data generation** — done. 10k accounts, 2M transactions, partitioned
  by year.
- **Orchestration (Airflow)** — done for the basic case. One working DAG.
- **Transformation (dbt)** — the core star schema exists and runs, but
  there are no dbt tests yet and the audit-log integration (see below)
  isn't wired in.
- **Anomaly detection** — not started.
- **Dashboards / access control** — not started.

## Why it's structured this way

The raw `transactions` table is fine for an application writing one row
at a time, but it's the wrong shape for the questions a risk team
actually asks — "how many transactions did this employee process this
month," "what's the daily volume trend." Answering those directly
against `transactions` means rewriting the same joins and date logic
every time. dbt exists here to do that reshaping once: `stg_transactions`
and `stg_accounts` are thin pass-throughs over the raw tables, and
`fact_transactions` / `dim_account` / `dim_employee` / `dim_date` are the
star-schema layer built on top of them. Once that layer exists, a
question like "top 5 employees by transaction count this month" is a
two-table join instead of a wall of `EXTRACT()` calls.

Airflow's job here is narrower than it sounds — right now it runs one
DAG (`check_data_freshness`) that just confirms the transaction count
looks sane. That's intentionally the smallest useful thing: prove the
scheduler can talk to Postgres across the Docker network before building
anything that depends on it. The next DAG will actually call `dbt run`
on a schedule instead of me running it by hand, which is the point where
Airflow starts pulling its weight.

## Two things that went wrong and why they're worth mentioning

**Airflow's webserver and scheduler need the same secret key.** Each
container generates its own random one by default, which means the
webserver can start, the scheduler can start, both look healthy in
`docker ps` — and then clicking into a task's log in the UI throws a 403
because the two components can't authenticate to each other. Nothing in
the scheduler logs pointed at this; the fix was setting
`AIRFLOW__WEBSERVER__SECRET_KEY` to the same literal string across all
three Airflow services in the compose file.

**Port 8081 silently refused connections on this machine** — no
firewall error, no useful message, just `ERR_EMPTY_RESPONSE` in the
browser even though `docker ps` showed the port mapped and the
container's own logs showed Gunicorn listening fine. Moved the webserver
to 8090 and it worked immediately. I never found the actual cause (some
other local service probably has a soft claim on 8081); noting it here
in case it happens again.

## Running it

```
docker compose up -d
```

Brings up Postgres, Airflow (init/webserver/scheduler), on ports 5435
and 8090.

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt   # psycopg2-binary, faker, dbt-postgres
python scripts/generate_transactions.py
```

Generates the accounts and partitioned transactions table. Takes a
couple of minutes for 2M rows.

```
cd dbt_project
dbt run
```

Builds the staging and mart models. Everything is a view for now — no
reason to materialize as tables yet at this volume.

Airflow UI: `http://127.0.0.1:8090`, admin/admin (set in compose, no
manual signup).

## A query the star schema was built for

```sql
SELECT e.employee_name, count(*) AS total
FROM fact_transactions f
JOIN dim_employee e ON f.employee_id = e.employee_id
GROUP BY e.employee_name
ORDER BY total DESC;
```

Against raw `transactions` this needs a `GROUP BY` on a text column with
no index backing it. Against the mart it's instant.

## What's next, roughly in order

1. dbt tests on the mart layer — no negative amounts without a flag, no
   orphaned `account_id` values, that kind of thing.
2. Pull in `dbaudit`'s `audit_history` table as a second fact table
   (`fact_audit_events`) so schema changes and data changes live in the
   same model, not just transaction volume.
3. An anomaly job — segregation-of-duties checks (same employee
   creating and approving) and basic volume outliers — run as an Airflow
   task on a schedule, writing into a `fact_risk_flags` table.
4. Grafana on top of the mart, plus a thin access layer so not everyone
   sees everything.

## Layout

```
riskledger/
├── docker-compose.yml       # Postgres + Airflow
├── scripts/
│   └── generate_transactions.py
├── airflow/dags/
│   └── check_data_freshness.py
└── dbt_project/
    └── models/
        ├── staging/          # stg_transactions, stg_accounts
        └── marts/            # dim_account, dim_date, dim_employee, fact_transactions
```
