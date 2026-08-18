SELECT
    account_id,
    owner_name,
    iban,
    account_type,
    opened_at,
    balance
FROM {{ source('riskledger', 'accounts') }}