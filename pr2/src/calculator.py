"""Вычисление арифметических выражений."""

import argparse
import ast
import json
import math
import operator
import sys
from pathlib import Path

BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
MAX_LENGTH = 200
MAX_NODES = 50
MAX_POWER = 10


class CalculationError(ValueError):
    """Ошибка вычисления."""


def calculate(expression):
    if not expression or len(expression) > MAX_LENGTH:
        raise CalculationError("неверная длина выражения")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise CalculationError("неверное выражение") from error
    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise CalculationError("выражение слишком сложное")
    result = _evaluate(tree.body)
    if not math.isfinite(float(result)):
        raise CalculationError("результат не является конечным числом")
    return result


def _evaluate(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
        return UNARY[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_POWER:
            raise CalculationError("слишком большая степень")
        try:
            return BINARY[type(node.op)](left, right)
        except (ArithmeticError, OverflowError) as error:
            raise CalculationError(str(error)) from error
    raise CalculationError("операция не поддерживается")


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
