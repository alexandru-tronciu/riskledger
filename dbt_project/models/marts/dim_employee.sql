SELECT DISTINCT
    processed_by AS employee_id,
    processed_by AS employee_name
FROM {{ ref('stg_transactions') }}
WHERE processed_by IS NOT NULL