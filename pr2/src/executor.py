"""Запуск вычислительной утилиты."""

import json
import subprocess
import sys
from pathlib import Path


def execute(command, directory, testing=False):
    if testing:
        return {"result": "test", "state": "done", "exception": ""}
    output = Path(directory) / f"command-{command['identifier']}.json"
    process = subprocess.run(
        [sys.executable, "-m", "pr2.src.calculator",
         "--output", str(output)],
        input=command["content"], text=True, capture_output=True, check=False)
    data = json.loads(output.read_text(encoding="utf-8"))
    if process.returncode == 0:
        return {"result": str(data["result"]),
                "state": "done", "exception": ""}
    return {"result": "", "state": "failed",
            "exception": data["error"]}
