SELECT
    account_id,
    owner_name,
    iban,
    account_type,
    opened_at
FROM {{ ref('stg_accounts') }}