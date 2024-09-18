import json

import sqlite3
from datetime import datetime

def get_latest_run_metrics():
    # Connect to SQLite database
    conn = sqlite3.connect("metadata.db")

    # Create a cursor object
    cursor = conn.cursor()

    # Fetch the most recent row based on run_id
    cursor.execute(
        """
        SELECT * FROM run_metadata
        ORDER BY run_id DESC
        LIMIT 1
    """
    )

    # Get the result
    most_recent_row = cursor.fetchone()

    # Close the connection
    conn.close()
    return (
        json.loads(most_recent_row[1])
        if most_recent_row and len(most_recent_row) > 0
        else None
    )


def insert_run_metrics(curr_metrics):
    # Connect to SQLite database
    conn = sqlite3.connect("metadata.db")

    # Create a cursor object
    cursor = conn.cursor()
    curr_metrics_json = json.dumps(curr_metrics)

    current_timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M')
    # Insert data into the run_metadata table
    cursor.execute(
        """
        INSERT INTO run_metadata (run_id, metadata)
        VALUES (?, ?)
    """,
        (current_timestamp, curr_metrics_json),
    )

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
