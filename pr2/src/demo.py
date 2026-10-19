"""Три примера запуска утилиты."""

import subprocess
import sys
from pathlib import Path

EXAMPLES = ("2 + 3 * 4", "(18 - 6) / 3", "2 ** 5 + 7")


def main():
    directory = Path(__file__).parents[1] / "data" / "examples"
    for number, expression in enumerate(EXAMPLES, start=1):
        output = directory / f"result-{number}.json"
        command = [sys.executable, "-m", "pr2.src.calculator",
                   "--output", str(output)]
        result = subprocess.run(command, input=expression, text=True,
                                capture_output=True, check=False)
        answer = result.stdout.strip() or result.stderr.strip()
        print(f"{expression} = {answer}; файл: {output}")


if __name__ == "__main__":
    main()
