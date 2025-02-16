FROM apache/airflow:2.10.4-python3.12
ADD requirements/requirements.txt .
RUN pip install -r requirements.txt
RUN python -m venv .dbt-venv && source .dbt-venv/bin/activate &&\
    pip install --no-cache-dir dbt-duckdb==1.9.1 && deactivate