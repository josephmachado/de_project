FROM python:3.13-bookworm

WORKDIR /home/airflow

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    openjdk-17-jdk \
    wget \
    make \
    procps \
    gcc \
    g++ \
    cmake \
    pkg-config \
    libssl-dev \
    libzstd-dev \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Works with both arm and amd
RUN ln -s $(ls -d /usr/lib/jvm/java-17-openjdk-* | grep -v current | head -1) \
    /usr/lib/jvm/java-17-openjdk-current

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-current
ENV PATH=$JAVA_HOME/bin:$PATH

# Install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Airflow environment variables
ENV AIRFLOW_HOME=/home/airflow/airflow
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false
ENV AIRFLOW__CORE__FERNET_KEY=''
ENV AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS=true
ENV AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL=3

ENV AIRFLOW_VERSION=3.3.0
ENV PYTHON_VERSION=3.13
ENV CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-no-providers-${PYTHON_VERSION}.txt"

ENV PYTHONPATH="/home/airflow:${PYTHONPATH}"

ADD ${CONSTRAINT_URL} /tmp/constraints.txt
RUN uv init --bare --python 3.13
RUN uv add "apache-airflow==${AIRFLOW_VERSION}" --constraints /tmp/constraints.txt
RUN uv add jupyterlab dbt-core dbt-spark astronomer-cosmos pyspark pyspark[sql]

# Switch off cosmos telemetry
ENV DO_NOT_TRACK=1
ENV PATH="/home/airflow/.venv/bin:$PATH"

# command to start airflow and jupyter lab
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

CMD ["/startup.sh"]
