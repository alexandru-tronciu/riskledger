SELECT DISTINCT
    created_at::date AS date_key,
    EXTRACT(YEAR FROM created_at) AS year,
    EXTRACT(MONTH FROM created_at) AS month,
    EXTRACT(DAY FROM created_at) AS day,
    EXTRACT(DOW FROM created_at) AS day_of_week
FROM {{ ref('stg_transactions') }}