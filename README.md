# log-analyzer

Скрипт парсит nginx логи и генерирует отчет в виде html странички с информацией о времени выполнения запросов.
На вход принимает логи в формате файла или архива gz.

### Конфигурирование

Через параметр командной строки --config скрпиту можно передать путь до файла с конфигурацией.
Конфигурация выглядит следующим образом:
```
{
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ANALYZER_LOG": ""
}
```
REPORT_SIZE - размер отчета в количестве запросов

REPORT_DIR - путь до папки, в которую будут сохраняться отчеты

LOG_DIR - папка с логами

ANALYZER_LOG - путь до файла куда сохраняется лог самого скрипта, если передать пустую строку, тогда анализатор
будет писать в stdout.

## Запуск

python3 log_analyzer.py
