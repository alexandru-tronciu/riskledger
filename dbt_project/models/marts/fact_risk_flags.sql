WITH daily_activity AS (
    SELECT
        employee_id,
        date_key,
        count(*) AS transactions_per_day
    FROM {{ ref('fact_transactions') }}
    GROUP BY employee_id, date_key
),

employee_avg AS (
    SELECT
        employee_id,
        avg(transactions_per_day) AS avg_daily,
        stddev(transactions_per_day) AS stddev_daily
    FROM daily_activity
    GROUP BY employee_id
)

SELECT
    d.employee_id,
    d.date_key,
    d.transactions_per_day,
    e.avg_daily,
    'HIGH_VOLUME_ANOMALY' AS risk_type,
    now() AS flagged_at
FROM daily_activity d
JOIN employee_avg e ON d.employee_id = e.employee_id
WHERE d.transactions_per_day > e.avg_daily + (3 * COALESCE(e.stddev_daily, 0))