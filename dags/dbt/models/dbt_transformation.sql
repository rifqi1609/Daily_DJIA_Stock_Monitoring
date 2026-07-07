{{
    config(
        materialized='incremental',
        incremental_strategy='insert_overwrite',
        partition_by={
            "field": "Extraction_Date",
            "data_type": "date",
            "granularity": "day"
        },
        alias='transformed_stock_dashboard'
    )
}}

SELECT DISTINCT
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
    END AS Liquidity_Health,

-- Fundamental Score
    CASE 
        WHEN f.ROE IS NULL 
          OR f.Gross_Margin IS NULL 
          OR f.Profit_Margin IS NULL 
          OR f.Forward_PE IS NULL 
          OR f.Current_Ratio IS NULL 
        THEN NULL
        
        ELSE ROUND(
            LEAST(
                -- Growth & Profitability
                LEAST(COALESCE(f.ROE, 0) / 40.0 * 15.0, 15.0) +
                LEAST(COALESCE(f.Gross_Margin, 0) / 75.0 * 10.0, 10.0) +
                LEAST(COALESCE(f.Profit_Margin, 0) / 35.0 * 10.0, 10.0) +
                LEAST(COALESCE(f.Earnings_Growth, 0) / 45.0 * 5.0, 5.0) +
                
                -- Valuation
                GREATEST(0.0, (40.0 - COALESCE(f.Forward_PE, 30.0)) / 40.0 * 15.0) +
                GREATEST(0.0, (15.0 - COALESCE(f.Price_to_Book, 5.0)) / 15.0 * 10.0) +
                GREATEST(0.0, (4.0 - COALESCE(f.PEG_Ratio, 2.0)) / 4.0 * 5.0) +
                
                -- Financial Condition
                LEAST(COALESCE(f.Current_Ratio, 1.0) / 4.0 * 10.0, 10.0) +
                GREATEST(0.0, (3.0 - COALESCE(f.Debt_to_Equity, 1.0)) / 3.0 * 10.0) +
                
                -- Momentum (52 Week Change)
                LEAST(GREATEST(COALESCE(f.Fifty_Two_Week_Change, 0.0), 0.0) / 60.0 * 10.0, 10.0)
            , 100.0)
        , 1) 
    END AS Fundamental_Score

FROM {{ source('data_source', 'stock_dashboard') }} AS f

{% if is_incremental() %}
  WHERE f.Extraction_Date >= (
      SELECT COALESCE(MAX(Extraction_Date), CAST('1970-01-01' AS DATE)) 
      FROM {{ this }}
  )
{% endif %}