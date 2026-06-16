CREATE TABLE fundamental_data (
    "Ticker" VARCHAR(10),
    "Company_Name" VARCHAR(255),
    "Sector" VARCHAR(100),
    "Extraction_Date" DATE,
    "Market_Cap" REAL,
    "Trailing_PE" REAL,
    "Forward_PE" REAL,
    "Price_to_Book" REAL,
    "PEG_Ratio" REAL,
    "EV_to_EBITDA" REAL,
    "ROE" REAL,
    "ROA" REAL,
    "Gross_Margin" REAL,
    "Operating_Margin" REAL,
    "Profit_Margin" REAL,
    "Current_Ratio" REAL,
    "Quick_Ratio" REAL,
    "Debt_to_Equity" REAL,
    "Cash_per_Share" REAL,
    "Revenue_Growth" REAL,
    "Earnings_Growth" REAL,
    "Beta" REAL,
    "Short_Ratio" REAL,
    "Fifty_Two_Week_Change" REAL,
    PRIMARY KEY ("Ticker", "Extraction_Date")
);

CREATE TABLE market_data (
    "Date" DATE,
    "DJIA_Close" REAL,
    PRIMARY KEY ("Date")
);

CREATE TABLE technical_data (
    "Date" DATE,
    "Ticker" VARCHAR(10),
    "Open" REAL,
    "High" REAL,
    "Low" REAL,
    "Close" REAL,
    "Volume" BIGINT,
    PRIMARY KEY ("Date", "Ticker")
);