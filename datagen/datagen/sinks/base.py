"""
Base sink interface. All sinks must implement these methods.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSink(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """
        Prepare the sink for writing.
        - PostgresSink: drop schema, recreate tables
        - FilesystemSink: clear output folder, create if missing
        """

    @abstractmethod
    def write(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        """
        Write a batch of rows for the given table.
        Called multiple times per table (once per batch of 1000).
        """

    @abstractmethod
    def finalize(self) -> None:
        """
        Called after all tables have been written successfully.
        - PostgresSink: commit transaction
        - FilesystemSink: close file handles, print file sizes
        """

    @abstractmethod
    def cleanup(self) -> None:
        """
        Called on error. Must leave the sink in a clean empty state.
        - PostgresSink: DROP SCHEMA public CASCADE → CREATE SCHEMA public
        - FilesystemSink: delete all CSV files written so far
        """

    @abstractmethod
    def row_counts(self) -> dict[str, int]:
        """Return a dict of table_name → rows written (for summary report)."""
