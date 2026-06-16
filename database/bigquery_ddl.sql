CREATE TABLE clean_stock_data.stock_screening (
    Date DATE,
    Ticker STRING,
    Prediction INT,
    Probability FLOAT64
);

CREATE TABLE clean_stock_data.stock_dashboard (
    Ticker STRING,
    Company_Name STRING,
    Sector STRING,
    Extraction_Date DATE,
    Market_Cap NUMERIC,
    Trailing_PE FLOAT64,
    Forward_PE FLOAT64,
    Price_to_Book FLOAT64,
    PEG_Ratio FLOAT64,
    EV_to_EBITDA FLOAT64,
    ROE FLOAT64,
    ROA FLOAT64,
    Gross_Margin FLOAT64,
    Operating_Margin FLOAT64,
    Profit_Margin FLOAT64,
    Current_Ratio FLOAT64,
    Quick_Ratio FLOAT64,
    Debt_to_Equity FLOAT64,
    Cash_per_Share FLOAT64,
    Revenue_Growth FLOAT64,
    Earnings_Growth FLOAT64,
    Beta FLOAT64,
    Short_Ratio FLOAT64,
    Fifty_Two_Week_Change FLOAT64
);