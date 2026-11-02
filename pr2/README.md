# Практическая работа №2, вариант 5

Для вычисления выражений используется библиотека `simpleeval`.

## Этап 1. Преобразование данных

Установка зависимости:

```powershell
python -m pip install -r pr2/requirements.txt
```

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
