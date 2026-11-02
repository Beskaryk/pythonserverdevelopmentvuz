"""Вычисление арифметических выражений."""

import argparse
import json
import math
import sys
from pathlib import Path

from simpleeval import InvalidExpression, simple_eval

MAX_LENGTH = 200


class CalculationError(ValueError):
    """Ошибка вычисления."""


def calculate(expression):
    if not expression or len(expression) > MAX_LENGTH:
        raise CalculationError("неверная длина выражения")
    try:
        result = simple_eval(expression, functions={}, names={})
    except (ArithmeticError, InvalidExpression, OverflowError,
            SyntaxError, ValueError) as error:
        raise CalculationError(str(error)) from error
    if isinstance(result, bool) or not isinstance(result, (int, float)):
        raise CalculationError("ожидается числовой результат")
    if not math.isfinite(result):
        raise CalculationError("результат не является конечным числом")
    return result


def save_result(path, expression, result=None, error=None):
    data = {"expression": expression, "result": result, "error": error}
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                      encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    options = parser.parse_args()
    expression = sys.stdin.read().strip()
    try:
        result = calculate(expression)
        save_result(options.output, expression, result=result)
        print(result)
    except CalculationError as error:
        save_result(options.output, expression, error=str(error))
        print(error, file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
