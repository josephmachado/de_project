from datetime import datetime
from pathlib import Path

from cosmos import DbtDag, ProjectConfig, ProfileConfig, ExecutionConfig
from cosmos.profiles import SparkThriftProfileMapping  # not used for session; see note

DBT_PROJECT_PATH = Path("/home/airflow/airflow/dbt/my_project")
DBT_EXECUTABLE = "/home/airflow/.venv/bin/dbt"

profile_config = ProfileConfig(
    profile_name="my_project",
    target_name="dev",
    profiles_yml_filepath=DBT_PROJECT_PATH / "profiles.yml",
)

execution_config = ExecutionConfig(
    dbt_executable_path=DBT_EXECUTABLE,
)

dbt_cosmos_dag = DbtDag(
    project_config=ProjectConfig(DBT_PROJECT_PATH),
    profile_config=profile_config,
    execution_config=execution_config,
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    dag_id="dbt_cosmos_dag",
    tags=["dbt", "cosmos", "spark"],
)
