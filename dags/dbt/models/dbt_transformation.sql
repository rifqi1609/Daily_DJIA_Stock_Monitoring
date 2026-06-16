{{
    config(
        materialized='incremental',
        unique_key=['Ticker', 'Extraction_Date'],
        alias='transformed_stock_dashboard'
    )
}}

SELECT 
    f.*,
    
    -- Categorizing Market Cap
    CASE 
        WHEN f.Market_Cap >= 200000000000 THEN 'Mega Cap'
        WHEN f.Market_Cap >= 10000000000  THEN 'Large Cap'
        WHEN f.Market_Cap >= 2000000000   THEN 'Mid Cap'
        ELSE 'Small Cap'
    END AS Market_Cap_Category,

    -- Categorizing Trailing P/E
    CASE 
        WHEN f.Trailing_PE < 0                              THEN 'Negative Earnings'
        WHEN f.Trailing_PE > 0 AND f.Trailing_PE <= 15     THEN 'Value'
        WHEN f.Trailing_PE > 15 AND f.Trailing_PE <= 25    THEN 'Fair'
        WHEN f.Trailing_PE > 25                            THEN 'Growth/Overvalued'
        ELSE 'Unknown'
    END AS Valuation_Category,

    -- Categorizing Liquidity
    CASE 
        WHEN f.Current_Ratio >= 1.5                         THEN 'Healthy'
        WHEN f.Current_Ratio >= 1.0 AND f.Current_Ratio < 1.5 THEN 'Adequate'
        WHEN f.Current_Ratio < 1.0                         THEN 'High Risk'
        ELSE 'Unknown'
    END AS Liquidity_Health

FROM {{ source('data_source', 'stock_dashboard') }} AS f

{% if is_incremental() %}
  WHERE f.Extraction_Date > (SELECT MAX(Extraction_Date) FROM {{ this }})
{% endif %}