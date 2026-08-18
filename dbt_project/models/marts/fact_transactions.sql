SELECT
    transaction_id,
    account_id,
    processed_by AS employee_id,
    created_at::date AS date_key,
    transaction_type,
    amount,
    currency
FROM {{ ref('stg_transactions') }}