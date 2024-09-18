import os
import duckdb
import sqlite3


def clean_up(file):
    # Remove the file if it exists
    if os.path.exists(file):
        os.remove(file)
    else:
        print(f"The file {file} does not exist.")


def create_tpch_data():
    con = duckdb.connect(
        "tpch.db"
    )  # Define a .db file to persist the generated tpch data
    con.sql(
        "INSTALL tpch;LOAD tpch;CALL dbgen(sf = 0.01);"
    )  # generate a 100MB TPCH dataset
    con.commit()
    con.close()  # close connection, since duckdb only allows one connection to tpch.db


def create_metadata_table(db="metadata.db"):
    # Connect to SQLite database (or create it)
    conn = sqlite3.connect("metadata.db")
    # Create a cursor object
    cursor = conn.cursor()

    # Create the run_metadata table
    cursor.execute(
        """
        CREATE TABLE run_metadata (
            run_id TEXT PRIMARY KEY,
            metadata TEXT
        )
    """
    )

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("Cleaning up tpch and metadata db files")
    clean_up("tpch.db")
    clean_up("metadata.db")
    print("Creating TPCH input data")
    create_tpch_data()
    print("Creating metadata table")
    create_metadata_table()
