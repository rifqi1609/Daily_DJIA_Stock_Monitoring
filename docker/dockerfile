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

# Cara menjalankannya
# docker-compose build
# docker-compose up -d