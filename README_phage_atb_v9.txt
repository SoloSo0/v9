Фаг + АТБ подбор v9

Папка версии:
C:\Users\ruby\Desktop\BF\v9

Что меняется в v9:
- база больше не держится на одной таблице outcomes
- отдельные таблицы для measurements и interpretations
- отдельные статусы зрелости записи
- отдельные validation issues
- ranking работает уже поверх новой модели данных
- есть импорт из legacy CSV и миграция из предыдущих версий

Основные таблицы:
- articles
- experiments
- therapies
- effect_measurements
- outcome_interpretations
- record_statuses
- validation_issues

Запуск:
1. Открой PowerShell
2. Перейди в папку:
   cd C:\Users\ruby\Desktop\BF\v9
3. Запусти:
   streamlit run phage_atb_app_v9.py

Если база v9 пустая:
- программа предложит перенос данных из v8
- затем из v7
- затем из v6

Примечание:
v9 остаётся исследовательским инструментом и не заменяет клиническое решение.
