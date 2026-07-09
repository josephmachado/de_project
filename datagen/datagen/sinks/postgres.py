"""
PostgreSQL sink — drops and recreates the public schema, then bulk-inserts
all rows using psycopg2's execute_values for performance.
"""

from typing import Any
import psycopg2
import psycopg2.extras

from datagen.core.schema import DDL, TABLE_REGISTRY, get_columns
from datagen.sinks.base import BaseSink


class PostgresSink(BaseSink):
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._conn = None
        self._cur = None
        self._counts: dict[str, int] = {}

    def initialize(self) -> None:
        self._conn = psycopg2.connect(self.dsn)
        self._conn.autocommit = False
        self._cur = self._conn.cursor()

        # Drop and recreate the public schema (clean slate)
        self._cur.execute("DROP SCHEMA public CASCADE")
        self._cur.execute("CREATE SCHEMA public")
        self._cur.execute("GRANT ALL ON SCHEMA public TO public")

        # Create all tables in FK-safe order
        for table_name, ddl in DDL.items():
            self._cur.execute(ddl)

        self._conn.commit()

    def write(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return

        cols = get_columns(table_name)
        # Use quoted table name to handle reserved words (order, return)
        qtable = f'"{table_name}"'
        col_str = ", ".join(f'"{c}"' for c in cols)
        sql = f"INSERT INTO {qtable} ({col_str}) VALUES %s"

        # Build value tuples in column order
        values = [tuple(row.get(c) for c in cols) for row in rows]

        psycopg2.extras.execute_values(self._cur, sql, values, page_size=1000)

        self._counts[table_name] = self._counts.get(table_name, 0) + len(rows)

    def finalize(self) -> None:
        if self._conn:
            self._conn.commit()
        self._close()

    def cleanup(self) -> None:
        """On error: rollback, then reset schema to clean state."""
        if self._conn:
            try:
                self._conn.rollback()
            except Exception:
                pass
            try:
                self._conn.autocommit = True
                cur = self._conn.cursor()
                cur.execute("DROP SCHEMA public CASCADE")
                cur.execute("CREATE SCHEMA public")
                cur.execute("GRANT ALL ON SCHEMA public TO public")
                cur.close()
            except Exception:
                pass
        self._close()
        self._counts.clear()

    def _close(self) -> None:
        if self._cur:
            try:
                self._cur.close()
            except Exception:
                pass
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
        self._cur = None
        self._conn = None

    def row_counts(self) -> dict[str, int]:
        return dict(self._counts)
