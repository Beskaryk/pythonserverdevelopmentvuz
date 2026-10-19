# Практическая работа №2, вариант 5

## Этап 1. Преобразование данных

Утилита читает арифметическое выражение из стандартного ввода,
вычисляет его и записывает результат в JSON-файл.

Один пример:

```powershell
"2 + 3 * 4" | python -m pr2.src.calculator --output pr2/data/result.json
```

Три примера из демонстрации:

```powershell
python -m pr2.src.demo
```

Результаты сохраняются в `pr2/data/examples`.

## Этап 2. HTTP API

Установка зависимостей:

```powershell
python -m pip install -r pr2/requirements.txt
```

Запуск сервера:

```powershell
python -m pr2.src.server
```

Тестовый режим не запускает вычислительную утилиту через `subprocess`:

```powershell
python -m pr2.src.server --test
```

Запуск MBT и отчёта о покрытии:

```powershell
python -m coverage run --branch --source=pr2/src -m pytest pr2/tests
python -m coverage report -m
```
