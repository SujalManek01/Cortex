"""Structured JSON Lines logger for Cortex.

Engineering Rule 9: Centralized logging.

Log format: JSON Lines (one JSON object per line) written to logs/cortex.log.
Each line includes a UTC timestamp. Lifecycle events match the spec fields:
plan_id, step_id, action, parameters, timestamps, duration, status, error_code.

Refinement 4: StructuredLogger is instantiated once and injected via constructor.
No module-level singletons.
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class StructuredLogger:
    """Writes structured JSON Lines log entries to a file.

    Optionally mirrors entries to stdout for development convenience.
    Thread-safe for sequential use within an asyncio event loop (file writes
    are atomic at the OS level for lines within the buffer size limit).
    """

    def __init__(self, log_path: Path, *, echo_stdout: bool = True) -> None:
        """
        Args:
            log_path:    Absolute path to the .log file. Parent dirs are created.
            echo_stdout: If True, each entry is also printed to stdout.
        """
        self._log_path = log_path
        self._echo_stdout = echo_stdout
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Internal write ─────────────────────────────────────────────────────────

    def _write(self, entry: dict[str, Any]) -> None:
        """Serialize entry to JSON and append it as one line to the log file."""
        entry["timestamp"] = datetime.now(tz=UTC).isoformat()
        line = json.dumps(entry, default=str)
        with self._log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        if self._echo_stdout:
            print(line, file=sys.stdout, flush=True)

    # ── Plan lifecycle events ──────────────────────────────────────────────────

    def plan_start(self, plan_id: str, goal: str, step_count: int) -> None:
        """Emitted when the engine begins executing a plan."""
        self._write({
            "event": "plan_start",
            "plan_id": plan_id,
            "goal": goal,
            "step_count": step_count,
        })

    def plan_complete(
        self,
        plan_id: str,
        status: str,
        duration_ms: float,
    ) -> None:
        """Emitted when a plan finishes (completed or failed)."""
        self._write({
            "event": "plan_complete",
            "plan_id": plan_id,
            "status": status,
            "duration_ms": round(duration_ms, 2),
        })

    # ── Step lifecycle events ──────────────────────────────────────────────────

    def step_start(
        self,
        plan_id: str,
        step_id: str,
        action: str,
        parameters: dict[str, Any],
    ) -> None:
        """Emitted immediately before a step executor is invoked."""
        self._write({
            "event": "step_start",
            "plan_id": plan_id,
            "step_id": step_id,
            "action": action,
            "parameters": parameters,
        })

    def step_complete(
        self,
        plan_id: str,
        step_id: str,
        action: str,
        status: str,
        duration_ms: float,
        error_code: str | None = None,
    ) -> None:
        """Emitted after a step executor returns, whether success or failure."""
        entry: dict[str, Any] = {
            "event": "step_complete",
            "plan_id": plan_id,
            "step_id": step_id,
            "action": action,
            "status": status,
            "duration_ms": round(duration_ms, 2),
        }
        if error_code is not None:
            entry["error_code"] = error_code
        self._write(entry)

    # ── General-purpose log levels ─────────────────────────────────────────────

    def info(self, message: str, **fields: Any) -> None:
        self._write({"level": "INFO", "message": message, **fields})

    def warning(self, message: str, **fields: Any) -> None:
        self._write({"level": "WARNING", "message": message, **fields})

    def error(self, message: str, **fields: Any) -> None:
        self._write({"level": "ERROR", "message": message, **fields})
