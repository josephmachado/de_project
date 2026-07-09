"""
Filesystem sink — writes one CSV file per table into an output folder.
"""

import csv
import shutil
from pathlib import Path
from typing import Any

from datagen.core.schema import get_columns
from datagen.sinks.base import BaseSink


class FilesystemSink(BaseSink):
    def __init__(self, folder: str):
        self.folder = Path(folder)
        self._handles: dict[str, Any] = {}  # table → file handle
        self._writers: dict[str, Any] = {}  # table → csv.DictWriter
        self._written: dict[str, bool] = {}  # table → header written?
        self._counts: dict[str, int] = {}  # table → row count

    def initialize(self) -> None:
        # Clear existing CSVs if folder exists
        if self.folder.exists():
            for f in self.folder.glob("*.csv"):
                f.unlink()
        else:
            self.folder.mkdir(parents=True, exist_ok=True)

    def write(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return

        if table_name not in self._handles:
            path = self.folder / f"{table_name}.csv"
            fh = open(path, "w", newline="", encoding="utf-8")
            cols = get_columns(table_name)
            writer = csv.DictWriter(
                fh,
                fieldnames=cols,
                extrasaction="ignore",
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writeheader()
            self._handles[table_name] = fh
            self._writers[table_name] = writer
            self._written[table_name] = True
            self._counts[table_name] = 0

        self._writers[table_name].writerows(rows)
        self._counts[table_name] += len(rows)

    def finalize(self) -> None:
        self._close_all()

    def cleanup(self) -> None:
        self._close_all()
        # Delete all CSV files written so far
        for table in list(self._counts.keys()):
            path = self.folder / f"{table}.csv"
            if path.exists():
                path.unlink()
        self._counts.clear()

    def _close_all(self) -> None:
        for fh in self._handles.values():
            try:
                fh.close()
            except Exception:
                pass
        self._handles.clear()
        self._writers.clear()

    def row_counts(self) -> dict[str, int]:
        return dict(self._counts)

    def file_sizes(self) -> dict[str, str]:
        """Return human-readable file sizes for the summary."""
        sizes = {}
        for table in self._counts:
            path = self.folder / f"{table}.csv"
            if path.exists():
                sz = path.stat().st_size
                if sz < 1024:
                    sizes[table] = f"{sz} B"
                elif sz < 1024**2:
                    sizes[table] = f"{sz / 1024:.1f} KB"
                else:
                    sizes[table] = f"{sz / 1024**2:.1f} MB"
        return sizes
