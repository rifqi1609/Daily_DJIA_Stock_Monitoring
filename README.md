# Stock Screening Dashboard

Nowadays, many traders face difficulties accessing customized information for their stock watchlists. This happens because every trader has their own unique technique for screening potential stocks. To address this, this dashboard provides traders with the flexibility to define and monitor the most pivotal metrics according to their specific trading approach.

---

## 🛠️ Technology Tools & Skills

| Category | Tools / Skills |
| :--- | :--- |
| **Language & Framework** | Python, SQL |
| **Databases & Storage** | PostgreSQL, Google BigQuery |
| **Machine Learning** | Scikit-Learn (Classification Model) |
| **Orchestration & DevOps**| Apache Airflow, Docker, Google Cloud Platform (GCP) Virtual Machine |
| **Data Transformation** | dbt (Data Build Tool) |
| **Data Sources** | Yahoo Finance API |
| **Business Intelligence** | Power BI, Metabase |
| **Core Skills** | Data Pipelining, Batch Processing, Machine Learning Building & Deployment, Data Visualization |

---

## 🔄 Project Flow

### 1. Prepare Data Management
* **PostgreSQL:** Used for saving and storing raw ingested data.
* **BigQuery:** Used as the data warehouse for storing processed and transformed data.

### 2. Build Stock Screening Model
* Developed a classification model to predict and classify potential stocks 5 days ahead.

### 3. Orchestrate Data Pipeline
An automated batch processing pipeline built to provide a daily-updated dashboard, configured via:
* **Virtual Machine Preparation:** Hosted on Google Cloud Platform.
* **Docker Preparation:** Containerizing the environment for consistency.
* **Airflow Orchestration:** Managing the daily workflow schedules:
  * **Daily Data Extraction:** Fetching latest market data from Yahoo Finance.
  * **Daily dbt Run:** Executing data transformation models inside BigQuery.
  * **Daily Stock Screening Prediction:** Running the ML model to generate new predictions.

### 4. Build Dashboard
* **Power BI:** Dedicated to DJIA (Dow Jones Industrial Average) stock monitoring.
* **Metabase:** Dedicated to tracking and visualizing potential stock monitoring based on ML predictions.

### 5. Monitor DJIA Stocks
* Observe the DJIA Stocks' Market Condition and Catch Potential Stocks. The dashboard is updated every trading days, 3 hours after market closed.