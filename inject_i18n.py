import re

with open("phage_atb_native.py", "r", encoding="utf-8") as f:
    content = f.read()

# Define the methods string with exactly 4 spaces indentation
methods_str = """
    def _init_translations(self):
        self.current_lang = "RU"
        self.i18n_dict = {
            "Профессиональная нативная система подбора фаготерапии v9": "Professional Native Phage Therapy Matching System v9",
            "Статей": "Articles",
            "Экспериментов": "Experiments",
            "Терапий": "Therapies",
            "Измерений": "Measurements",
            "Интерпретаций": "Interpretations",
            "Подбор (Ranking)": "Ranking",
            "Аудит": "Audit",
            "Консенсус": "Consensus",
            "Аналитика": "Analytics",
            "Калькулятор": "Calculator",
            "Ввод данных": "Data Input",
            "Импорт / Миграция": "Import / Migration",
            "О программе": "About",
            "Справка": "Help",
            "Возбудитель:": "Pathogen:",
            "Growth state:": "Growth state:",
            "Топ-N:": "Top-N:",
            "Sensitive АТБ:": "Sensitive ATB:",
            "Resistant АТБ:": "Resistant ATB:",
            "Только validated/curated": "Only validated/curated",
            "Приоритет MDR": "MDR Priority",
            "Только активные пары": "Active pairs only",
            "РАССЧИТАТЬ RANKING v9": "CALCULATE RANKING v9",
            "ЭКСПОРТ EXCEL": "EXPORT EXCEL",
            "Фаг": "Phage",
            "Антибиотик": "Antibiotic",
            "Итог": "Score",
            "Релев.": "Relevance",
            "Эффект": "Effect",
            "Доказ.": "Evidence",
            "Доверие": "Confidence",
            "Тип": "Type",
            "Возбудитель": "Pathogen",
            "Сред. Синергия": "Mean Synergy",
            "Макс. Доказ.": "Max Evidence",
            "Статус": "Status",
            "Управление данными": "Data Management",
            "Fetch DOI": "Fetch DOI",
            "Сохранить запись": "Save Record",
            "Обновить таблицу аудита": "Refresh Audit",
            "Источник": "Source",
            "Обновить аналитику": "Refresh Analytics",
            "Нажмите кнопку для генерации графиков": "Click to generate charts",
            "Нет данных для отображения": "No data to display",
            "Калькулятор Бактериофагов": "Phage Calculator",
            "Рассчитать фаг": "Calculate Phage",
            "Нужный объем фага: ---": "Required phage vol: ---",
            "Калькулятор Антибиотиков": "Antibiotic Calculator",
            "Рассчитать АТБ": "Calculate ATB",
            "Нужный объем АТБ: ---": "Required ATB vol: ---",
            "Импорт CSV (Legacy)": "Import CSV (Legacy)",
            "Миграция из старых БД (v6-v8)": "Migrate old DBs (v6-v8)",
            "Выберите CSV": "Select CSV",
            "Выберите SQLite БД": "Select SQLite DB",
            "Поиск (DOI, Патоген, АТБ):": "Search (DOI, Pathogen, ATB):",
            "DOI / PMID:": "DOI / PMID:",
            "Заметки:": "Notes:",
            "Год:": "Year:",
            "Ссылка:": "Reference:",
            "Титр фага (PFU/ml):": "Phage titer (PFU/ml):",
            "Бактериальная нагрузка (CFU/ml):": "Bacterial load (CFU/ml):",
            "Объем (ml):": "Volume (ml):",
            "Целевой MOI:": "Target MOI:",
            "Исходная концентрация (C1):": "Initial concentration (C1):",
            "Целевая концентрация (C2):": "Target concentration (C2):",
            "Целевой объем (V2, ml):": "Target volume (V2, ml):",
            "Получить данные": "Get Data",
            "Сделать бэкап БД": "Backup DB",
            "Статус бэкапа:": "Backup Status:",
            "Результат:": "Result:",
            "Расчет дозировки фагов (MOI)": "Phage dosage calculation (MOI)",
            "Расчет разведения антибиотика (C1V1 = C2V2)": "Antibiotic dilution calculation (C1V1 = C2V2)",
            "Добавить запись (PubMed)": "Add record (PubMed)",
            "Найти": "Search",
            "Поиск": "Search"
        }
        self.reverse_dict = {v: k for k, v in self.i18n_dict.items()}

    def tr(self, text):
        if not isinstance(text, str):
            return text
            
        # Убираем пробелы по краям для безопасного поиска, но сохраняем их при возврате
        clean_text = text.strip()
        
        if self.current_lang == "EN":
            translated = self.i18n_dict.get(clean_text, clean_text)
        else:
            translated = self.reverse_dict.get(clean_text, clean_text)
            
        # Восстанавливаем пробелы, если они были (чтобы не сломать отступы в UI)
        if text.startswith(" "): translated = " " + translated
        if text.endswith(" "): translated = translated + " "
        return translated

    def change_language(self, new_lang):
        if new_lang == self.current_lang:
            return
        self.current_lang = new_lang
        self.update_ui_texts()

    def update_ui_texts(self):
        # 1. Update Tabview labels
        if hasattr(self, "tabview"):
            for tab_name in self.tabview._name_list:
                try:
                    btn = self.tabview._segmented_button._buttons_dict[tab_name]
                    current_text = btn.cget("text")
                    btn.configure(text=self.tr(current_text))
                except Exception as e:
                    pass
                    
        # 2. Recursive UI update for texts
        def walk_and_translate(widget):
            # Translate text attributes
            try:
                if hasattr(widget, "cget"):
                    # For labels, buttons, checkboxes
                    if isinstance(widget, (ctk.CTkLabel, ctk.CTkButton, ctk.CTkCheckBox)):
                        current_text = widget.cget("text")
                        if current_text:
                            widget.configure(text=self.tr(current_text))
            except Exception:
                pass
            
            # Recursive call
            try:
                for child in widget.winfo_children():
                    walk_and_translate(child)
            except Exception:
                pass
                
        walk_and_translate(self)
        
        # 3. Update Treeview headings explicitly
        trees = []
        if hasattr(self, "tree"): trees.append(self.tree)
        if hasattr(self, "audit_tree"): trees.append(self.audit_tree)
        if hasattr(self, "consensus_tree"): trees.append(self.consensus_tree)
        
        for tree in trees:
            try:
                for col in tree["columns"]:
                    current_text = tree.heading(col)["text"]
                    if current_text:
                        tree.heading(col, text=self.tr(current_text))
            except Exception:
                pass
"""

if "def _init_translations(self):" not in content:
    # Insert methods right after class declaration
    content = content.replace("class PhageATBApp(ctk.CTk):", "class PhageATBApp(ctk.CTk):\n" + methods_str)
    
    # Initialize translations at the start of __init__
    content = content.replace("super().__init__()\n\n        # Initialize core", "super().__init__()\n        self._init_translations()\n\n        # Initialize core")

    # Add language toggle button in setup_header
    toggle_code = """
        self.lang_var = ctk.StringVar(value="RU")
        self.lang_toggle = ctk.CTkSegmentedButton(self.hero_frame, values=["RU", "EN"], 
                                                  variable=self.lang_var, command=self.change_language,
                                                  corner_radius=8, width=100)
        self.lang_toggle.place(relx=1.0, rely=0.0, x=-20, y=20, anchor="ne")
"""
    content = content.replace('self.subtitle_label.pack(pady=(0, 20))', 'self.subtitle_label.pack(pady=(0, 20))' + toggle_code)

    with open("phage_atb_native.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected successfully!")
else:
    print("Already injected.")
