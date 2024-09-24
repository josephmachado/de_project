
* [Build a data engineering project, with step-by-step instructions](#build-a-data-engineering-project-with-step-by-step-instructions)
     * [Setup](#setup)
          * [Option 1: Github codespaces (Recommended)](#option-1-github-codespaces-recommended)
          * [Option 2: Run locally](#option-2-run-locally)

# Build a data engineering project, with step-by-step instructions

* Code for the blog: **[Build data engineering projects with step-by-step instruction](https://www.startdataengineering.com/post/de-proj-step-by-step/)**
* Live workshop at: **[Youtube live link](https://www.youtube.com/live/bfiOLwp1aWM?feature=share)**

## Architecture

Most data teams have their version of the 3-hop architecture. For example, dbt has its own version (stage, intermediate, mart), and Spark has medallion (bronze, silver, gold) architecture.

![Data Flow](./assets/images/dep-arch.png)

**Tools used:**

[<img src="https://raw.githubusercontent.com/pola-rs/polars-static/master/banner/polars_github_banner.svg" height="50" alt="Polars logo" />](https://pola.rs/)
[<img src="./assets/images/docker.png" height="50" alt="Docker logo" />](https://www.docker.com/)
[<img src="./assets/images/airflow.png" height="50" alt="logo" />](https://airflow.apache.org/)
[<img src="./assets/images/pytest.png" height="50" alt="Pytest logo" />](https://docs.pytest.org/en/stable/)
[<img src="./assets/images/duckdb.png" height="50" alt="DuckDB logo" />](https://duckdb.org/)

## Setup

You have two options to run the exercises in this repo

### Option 1: Github codespaces (Recommended)

Steps:

1. Create [Github codespaces with this link](https://github.com/codespaces/new?skip_quickstart=true&machine=basicLinux32gb&repo=858828036&ref=main&devcontainer_path=.devcontainer%2Fdevcontainer.json&geo=UsWest).
2. Wait for Github to install the [requirements.txt](./requirements.txt). This step can take about 5minutes.
        ![installation](./assets/images/inst.png)
3. Now open the `setup-data-project.ipynb` and it will open in a Jupyter notebook interface. You will be asked for your kernel choice, choose `Python Environments` and then `python3.12.00 Global`.
        ![Jupyter notebook in VScode](./assets/images/vsjupy.png)
4. The **[setup-data-project](./setup-data-project.ipynb)** notebook that goes over how to create a data pipeline.
5. In the terminal run the following commands to setup input data, run etl and run tests.

```bash
# setup input data
python ./setup/create_input_data.py
# run pipeline
python de_project/run_pipeline.py
# run tests
python -m pytest de_project/tests/unit/test_dim_customer.py
```

### Option 2: Run locally

Steps:

1. Clone this repo, cd into the cloned repo
2. Start a virtual env and install requirements.
3. Start Jupyter lab and run the `setup-data-project.ipynb` notebook that goes over how to create a data pipeline.
```bash
git clone https://github.com/josephmachado/de_project.git
cd de_project 
python -m venv ./env # create a virtual env
source env/bin/activate # use virtual environment
pip install -r requirements.txt
jupyter lab
```
4. In the terminal run the following commands to setup input data, run etl and run tests.

```bash
# setup input data
python ./setup/create_input_data.py
# run pipeline
python de_project/run_pipeline.py
# run tests
python -m pytest de_project/tests/unit/test_dim_customer.py
```

