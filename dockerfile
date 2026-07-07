# Menggunakan base image Airflow resmi terbaru
FROM apache/airflow:2.8.1

# Berpindah ke user root sementara untuk update OS jika perlu (opsional)
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Kembali ke user airflow untuk install paket Python
USER airflow

# Menyalin file requirements dan menginstalnya
COPY requirement.txt /
RUN pip install --no-cache-dir -r /requirement.txt

# Membuat virtual environment untuk dbt
RUN python -m venv /opt/airflow/dbt_venv

# Menginstal dbt-core dan dbt-bigquery ke dalam virtual environment tersebut
RUN PIP_USER=false /opt/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-core dbt-bigquery