SELECT
    transaction_id,
    account_id,
    transaction_type,
    amount,
    currency,
    created_at,
    processed_by
FROM {{ source('riskledger', 'transactions') }}