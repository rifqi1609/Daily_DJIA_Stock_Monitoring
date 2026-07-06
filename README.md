# 📈 Daily Stock Monitoring Dashboard

> A fully automated, end-to-end stock monitoring system — combining machine learning, cloud infrastructure, and real-time data pipelines to give traders a personalized, daily-updated edge.

---

## 🧩 The Problem

Every trader has their own unique approach to screening stocks. Off-the-shelf tools force you into rigid, one-size-fits-all metrics that rarely match your strategy. This project solves that by giving you a **fully customizable dashboard** — built on your own criteria, updated automatically every trading day.

---

## ✨ Key Features

- **ML-powered stock screening** — predicts potential stock picks 5 days ahead using a trained classification model
- **Daily automation** — pipeline runs 3 hours after market close on every trading day
- **Dual dashboards** — one for DJIA market overview (Power BI), one for ML-based opportunities (Metabase)
- **Cloud-native infrastructure** — hosted on GCP, containerized with Docker, orchestrated via Airflow

---

## 🛠️ Tech Stack

| Category | Tools |
| :--- | :--- |
| **Language & Framework** | Python, SQL |
| **Databases & Storage** | PostgreSQL (raw data), Google BigQuery (data warehouse) |
| **Machine Learning** | Scikit-Learn (Classification Model) |
| **Orchestration & DevOps** | Apache Airflow, Docker, GCP Virtual Machine |
| **Data Transformation** | dbt (Data Build Tool) |
| **Data Sources** | Yahoo Finance API |
| **Business Intelligence** | Power BI, Metabase |

---

## 🔄 How It Works

### 1. 🗄️ Data Management
Raw market data ingested daily is stored in **PostgreSQL**, then loaded into **Google BigQuery** as the central data warehouse for downstream transformations and modeling.

### 2. 🤖 Stock Screening Model
A **Scikit-Learn classification model** was trained to predict whether a stock is worth watching — generating a buy/no-buy signal for each ticker 5 days in advance.

### 3. ⚙️ Automated Pipeline
The entire workflow is orchestrated via **Apache Airflow** on a GCP VM, running three core daily tasks:

| Task | Description |
| :--- | :--- |
| **Data Extraction** | Pulls the latest market data from Yahoo Finance |
| **Data Migration** | Pulls the data from PostgreSQL to BigQuery |
| **dbt Transformation** | Cleans and transforms raw data inside BigQuery |
| **ML Prediction** | Runs the screening model and writes results back |

### 4. 📊 Dashboards
Two dedicated dashboards serve different monitoring needs:

- **Power BI** — Macro-level view of DJIA stocks and overall market health
- **Metabase** — Granular view of ML-flagged stocks with prediction scores and metrics

### 5. 🔔 Daily Updates
The pipeline triggers **every trading day, 3 hours after market close**, ensuring you always have fresh, actionable data waiting for you the next morning.

---

## 📁 Project Structure

```
.
├── dags/                          # Airflow orchestration
│   ├── credentials/
│   │   └── bq_key.json            # GCP service account credentials
│   ├── dbt/                       # dbt data transformation
│   │   ├── models/
│   │   │   ├── dbt_transformation.sql   # SQL transformation logic
│   │   │   └── sources.yml              # Raw source definitions
│   │   ├── dbt_project.yml        # dbt project config
│   │   └── profiles.yml           # BigQuery connection settings
│   ├── ml_models/
│   │   └── final_model.pkl        # Trained, deployment-ready ML model
│   ├── scripts/
│   │   ├── data_extraction.py     # Fetches daily data from Yahoo Finance
│   │   ├── extract_load.py        # EL pipeline: PostgreSQL → BigQuery
│   │   └── model_deployment.py    # Runs daily inference / predictions
│   └── dag.py                     # Main Airflow DAG (schedules & dependencies)
│
├── database/                      # DDL schemas for database initialization
│   ├── bigquery_ddl.txt           # BigQuery table schemas
│   └── postgre_ddl.txt            # PostgreSQL table schemas
│
├── ml_model/                      # Model research & experimentation
│   ├── eda/                       # Auto-generated EDA reports
│   │   ├── Processed Data EDA.html
│   │   ├── Raw Market Data EDA.html
│   │   └── Raw Technical Data EDA.html
│   ├── model_building.ipynb       # Final model construction notebook
│   ├── model_research.ipynb       # EDA, feature engineering, tuning & evaluation
│   └── logs.log                   # Experiment activity log
│
├── .dockerignore / .gitignore     # Excludes credentials and cache from tracking
├── .env                           # Sensitive environment variables
├── docker-compose.yml             # Multi-container setup (Airflow, PostgreSQL, Metabase)
├── dockerfile                     # Docker image build instructions
├── logs.log                       # Main application log
├── requirement.txt                # Python dependencies
└── README.md                      # You are here
```

---

## 📽️ Documentation & Demo

### 🎥 Videos

| Resource | Description | Link |
| :--- | :--- | :--- |
| 🎬 **Project Presentation** | Walkthrough of the system architecture, data pipeline design, and overall project overview | [Watch Video](www.google.com) |
| 🖥️ **Dashboard Demo** | Live demo of the Power BI and Metabase dashboards in action | [Watch Video](www.google.com) |

### 📊 Live Dashboards

| Dashboard | Link |
| :--- | :--- |
| 📉 **Streamlit** (Web-based) | [Open Dashboard](www.google.com) |
| 📉 **Power BI** | [Open Dashboard](www.google.com) |
| 📉 **Metabase** | [Open Dashboard](www.google.com) |

---

*Help Trades to Understand Market*
