{{
    config(
        materialized='incremental',
        unique_key=['Ticker', 'extraction_date']
    )
}}

SELECT 
    f.*,
    
    -- Categorizing Market Cap
    CASE 
        WHEN f.market_cap >= 200000000000 THEN 'Mega Cap'
        WHEN f.market_cap >= 10000000000 THEN 'Large Cap'
        WHEN f.market_cap >= 2000000000 THEN 'Mid Cap'
        ELSE 'Small Cap'
    END AS market_cap_category,

    -- Categorizing Trailing P/E
    CASE 
        WHEN f.trailing_pe < 0 THEN 'Negative Earnings'
        WHEN f.trailing_pe > 0 AND f.trailing_pe <= 15 THEN 'Value'
        WHEN f.trailing_pe > 15 AND f.trailing_pe <= 25 THEN 'Fair'
        WHEN f.trailing_pe > 25 THEN 'Growth/Overvalued'
        ELSE 'Unknown'
    END AS valuation_category,

    -- Categorizing Liquidity
    CASE 
        WHEN f.current_ratio >= 1.5 THEN 'Healthy'
        WHEN f.current_ratio >= 1.0 AND f.current_ratio < 1.5 THEN 'Adequate'
        WHEN f.current_ratio < 1.0 THEN 'High Risk'
        ELSE 'Unknown'
    END AS liquidity_health

FROM {{ source('sumber_data_saham', 'clean_fundamental_data') }} AS f

-- Incremental Processing
{% if is_incremental() %}
  WHERE f.extraction_date > (SELECT MAX(extraction_date) FROM {{ this }})
{% endif %}