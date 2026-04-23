import customtkinter as ctk
import core_logic as core
import pandas as pd
from tkinter import ttk, messagebox, filedialog
import sys
import os

class PhageATBApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize core
        core.run_schema()

        self.title(core.APP_TITLE)
        self.geometry("1400x900")
        
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Define custom colors
        self.colors = {
            "bg_dark": "#0f172a",
            "bg_card": "#1e293b",
            "accent": "#3b82f6",
            "success": "#10b981",
            "text_main": "#f8fafc",
            "text_dim": "#94a3b8",
            "border": "#334155"
        }

        # Global styles for Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background=self.colors["bg_card"], 
                        foreground=self.colors["text_main"], 
                        fieldbackground=self.colors["bg_card"], 
                        borderwidth=0, 
                        font=("Segoe UI", 10),
                        rowheight=30)
        style.configure("Treeview.Heading", 
                        background="#334155", 
                        foreground="white", 
                        relief="flat", 
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", 
                  background=[('selected', self.colors["accent"])])
        
        # Add alternating row colors
        style.configure("Treeview", rowheight=35)
        self.tree_tag_colors = {"even": "#1e293b", "odd": "#162031"}

        # Main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Hero & KPI Section
        self.setup_header()

        # 2. Tabs Section
        self.tabview = ctk.CTkTabview(self, corner_radius=15)
        self.tabview.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")

        self.tab_ranking = self.tabview.add("Подбор (Ranking)")
        self.tab_audit = self.tabview.add("Аудит")
        self.tab_consensus = self.tabview.add("Консенсус")
        self.tab_input = self.tabview.add("Ввод данных")
        self.tab_import = self.tabview.add("Импорт / Миграция")
        self.tab_about = self.tabview.add("О программе")
        self.tab_help = self.tabview.add("Справка")

        self.setup_ranking_tab()
        self.setup_audit_tab()
        self.setup_consensus_tab()
        self.setup_input_tab()
        self.setup_import_tab()
        self.setup_about_tab()
        self.setup_help_tab()

    def setup_about_tab(self):
        self.tab_about.grid_columnconfigure(0, weight=1)
        self.about_frame = ctk.CTkFrame(self.tab_about, corner_radius=15)
        self.about_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(self.about_frame, text=f"Версия {core.VERSION}", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        changes_text = ctk.CTkTextbox(self.about_frame, width=600, height=300, font=ctk.CTkFont(size=13))
        changes_text.pack(padx=20, pady=10, fill="both", expand=True)
        changes_text.insert("1.0", f"Последние изменения:\n{core.LAST_CHANGES}")
        changes_text.configure(state="disabled")

    def setup_header(self):
        # Hero frame
        self.hero_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("#1e293b", "#0f172a"))
        self.hero_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        self.title_label = ctk.CTkLabel(self.hero_frame, text=core.APP_TITLE, font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=(15, 5))
        
        self.subtitle_label = ctk.CTkLabel(self.hero_frame, text="Профессиональная нативная система подбора фаготерапии v9", font=ctk.CTkFont(size=14))
        self.subtitle_label.pack(pady=(0, 15))

        # KPI frame
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        for i in range(5): self.kpi_frame.grid_columnconfigure(i, weight=1)

        self.kpi_labels = {}
        self.refresh_kpis()

    def refresh_kpis(self):
        metrics = [
            ("Статей", core.table_count("articles")),
            ("Экспериментов", core.table_count("experiments")),
            ("Терапий", core.table_count("therapies")),
            ("Измерений", core.table_count("effect_measurements")),
            ("Интерпретаций", core.table_count("outcome_interpretations"))
        ]
        
        for i, (label, value) in enumerate(metrics):
            if label not in self.kpi_labels:
                card = ctk.CTkFrame(self.kpi_frame, corner_radius=12, border_width=2, border_color=self.colors["border"], fg_color=self.colors["bg_card"])
                card.grid(row=0, column=i, padx=8, pady=10, sticky="nsew")
                ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dim"]).pack(pady=(12, 0))
                val_lbl = ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=24, weight="bold"), text_color=self.colors["accent"])
                val_lbl.pack(pady=(0, 12))
                self.kpi_labels[label] = val_lbl
            else:
                self.kpi_labels[label].configure(text=str(value))

    def setup_ranking_tab(self):
        self.tab_ranking.grid_columnconfigure(0, weight=1)
        self.tab_ranking.grid_rowconfigure(1, weight=1)

        # Filters frame
        self.filters_frame = ctk.CTkFrame(self.tab_ranking)
        self.filters_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Grid for filters
        # Row 0
        ctk.CTkLabel(self.filters_frame, text="Возбудитель:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.rank_pathogen = ctk.CTkEntry(self.filters_frame, width=200)
        self.rank_pathogen.insert(0, "Pseudomonas aeruginosa")
        self.rank_pathogen.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(self.filters_frame, text="Growth state:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.rank_growth = ctk.CTkComboBox(self.filters_frame, values=["Любой", "biofilm", "planktonic"])
        self.rank_growth.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(self.filters_frame, text="Top-N:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.rank_topn = ctk.CTkSlider(self.filters_frame, from_=3, to=20, number_of_steps=17)
        self.rank_topn.set(8)
        self.rank_topn.grid(row=0, column=5, padx=5, pady=5)

        # Row 1
        ctk.CTkLabel(self.filters_frame, text="Sensitive АТБ:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.rank_sensitive = ctk.CTkEntry(self.filters_frame, width=200)
        self.rank_sensitive.insert(0, "Ceftazidime")
        self.rank_sensitive.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(self.filters_frame, text="Resistant АТБ:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.rank_resistant = ctk.CTkEntry(self.filters_frame, width=200)
        self.rank_resistant.grid(row=1, column=3, padx=5, pady=5)

        self.rank_res_mode = ctk.CTkSegmentedButton(self.filters_frame, values=["strict", "soft"])
        self.rank_res_mode.set("strict")
        self.rank_res_mode.grid(row=1, column=4, columnspan=2, padx=5, pady=5)

        # Row 2
        self.rank_validated = ctk.CTkCheckBox(self.filters_frame, text="Только validated/curated")
        self.rank_validated.select()
        self.rank_validated.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        self.rank_mdr = ctk.CTkCheckBox(self.filters_frame, text="Приоритет MDR")
        self.rank_mdr.select()
        self.rank_mdr.grid(row=2, column=2, padx=5, pady=5)

        self.rank_active = ctk.CTkCheckBox(self.filters_frame, text="Только активные пары")
        self.rank_active.grid(row=2, column=3, padx=5, pady=5)

        self.run_btn = ctk.CTkButton(self.filters_frame, text="РАССЧИТАТЬ RANKING v9", command=self.run_ranking, fg_color="#2563eb", hover_color="#1d4ed8")
        self.run_btn.grid(row=2, column=4, columnspan=2, padx=5, pady=5, sticky="ew")

        # Table frame
        self.table_frame = ctk.CTkFrame(self.tab_ranking)
        self.table_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.tree = ttk.Treeview(self.table_frame, columns=("phage", "atb", "score", "relevance", "effect", "evidence", "confidence", "synergy"), show="headings")
        self.tree.heading("phage", text="Фаг")
        self.tree.heading("atb", text="Антибиотик")
        self.tree.heading("score", text="Итог")
        self.tree.heading("relevance", text="Релев.")
        self.tree.heading("effect", text="Эффект")
        self.tree.heading("evidence", text="Доказ.")
        self.tree.heading("confidence", text="Доверие")
        self.tree.heading("synergy", text="Тип")
        
        for col in self.tree["columns"]: self.tree.column(col, width=100, anchor="center")
        self.tree.column("phage", width=180)
        self.tree.column("atb", width=180)
        
        self.tree.pack(side="left", expand=True, fill="both")
        
        scrollbar = ctk.CTkScrollbar(self.table_frame, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def run_ranking(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        
        patient = {
            "pathogen": core.normalize_pathogen(self.rank_pathogen.get()),
            "growth_mode": self.rank_growth.get(),
            "sensitive": [core.norm(core.normalize_antibiotic(x)) for x in core.split_csv(self.rank_sensitive.get())],
            "resistant": [core.norm(core.normalize_antibiotic(x)) for x in core.split_csv(self.rank_resistant.get())],
            "resistant_mode": self.rank_res_mode.get(),
            "wants_mdr": self.rank_mdr.get(),
            "wants_xdr": False,
            "min_evidence": 1,
            "min_confidence": 45,
            "exclude_antagonism": True,
            "only_active_pairs": self.rank_active.get(),
            "only_validated": self.rank_validated.get(),
        }
        
        df = core.ranking_df(patient)
        if df.empty:
            messagebox.showinfo("Ranking", "Нет данных для отображения")
            return
            
        for i, row in df.head(int(self.rank_topn.get())).iterrows():
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=(
                row["phage"], row["atb"] if "atb" in row else row["antibiotic"], row["final_score"],
                row["relevance_score"], row["effect_score"], row["evidence_score"],
                row["confidence_score"], row["synergy_prediction"]
            ), tags=(tag,))
        
        self.tree.tag_configure("even", background=self.tree_tag_colors["even"])
        self.tree.tag_configure("odd", background=self.tree_tag_colors["odd"])

    def setup_audit_tab(self):
        self.tab_audit.grid_columnconfigure(0, weight=1)
        self.tab_audit.grid_rowconfigure(1, weight=1)

        self.audit_controls = ctk.CTkFrame(self.tab_audit)
        self.audit_controls.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkButton(self.audit_controls, text="Обновить таблицу аудита", command=self.refresh_audit).pack(side="left", padx=10, pady=5)

        self.audit_tree = ttk.Treeview(self.tab_audit, columns=("ref", "path", "phage", "atb", "conf", "status"), show="headings")
        self.audit_tree.heading("ref", text="Источник")
        self.audit_tree.heading("path", text="Возбудитель")
        self.audit_tree.heading("phage", text="Фаг")
        self.audit_tree.heading("atb", text="АТБ")
        self.audit_tree.heading("conf", text="Доверие")
        self.audit_tree.heading("status", text="Статус")
        
        self.audit_tree.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.refresh_audit()

    def refresh_audit(self):
        for item in self.audit_tree.get_children(): self.audit_tree.delete(item)
        df = core.audit_df()
        for _, row in df.iterrows():
            self.audit_tree.insert("", "end", values=(row["reference"], row["pathogen"], row["phage"], row["antibiotic"], row["confidence_score"], row["record_status"]))

    def setup_consensus_tab(self):
        self.tab_consensus.grid_columnconfigure(0, weight=1)
        self.tab_consensus.grid_rowconfigure(0, weight=1)
        self.cons_tree = ttk.Treeview(self.tab_consensus, columns=("path", "phage", "atb", "art", "syn"), show="headings")
        self.cons_tree.heading("path", text="Возбудитель")
        self.cons_tree.heading("phage", text="Фаг")
        self.cons_tree.heading("atb", text="АТБ")
        self.cons_tree.heading("art", text="Статей")
        self.cons_tree.heading("syn", text="Сред. Синергия")
        self.cons_tree.pack(expand=True, fill="both", padx=10, pady=10)
        self.refresh_consensus()

    def refresh_consensus(self):
        for item in self.cons_tree.get_children(): self.cons_tree.delete(item)
        df = core.consensus_df()
        for _, row in df.iterrows():
            self.cons_tree.insert("", "end", values=(row["pathogen"], row["phage"], row["antibiotic"], row["supporting_articles"], round(row["mean_synergy_score"], 1)))

    def setup_input_tab(self):
        self.tab_input.grid_columnconfigure(0, weight=1)
        self.input_form = ctk.CTkFrame(self.tab_input)
        self.input_form.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        fields = [
            ("Источник / Reference:", "ref"),
            ("Год:", "year"),
            ("Возбудитель:", "pathogen"),
            ("Фаг / Коктейль:", "phage"),
            ("Антибиотик:", "atb"),
            ("Synergy Score (0-100):", "score")
        ]
        
        self.inputs = {}
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(self.input_form, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            entry = ctk.CTkEntry(self.input_form, width=300)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            self.inputs[key] = entry
            
        ctk.CTkButton(self.input_form, text="Сохранить запись", command=self.save_input, fg_color="#10b981").grid(row=len(fields), column=0, columnspan=2, pady=20)

    def save_input(self):
        try:
            art_id = core.create_article(self.inputs["ref"].get(), int(self.inputs["year"].get() or 2026), "", "in vitro", "")
            exp_id = core.create_experiment(art_id, self.inputs["pathogen"].get(), "strain X", "source", "planktonic", "model", 0, 1, 1, 0, 1, 1, 0)
            ther_id = core.create_therapy(self.inputs["phage"].get(), self.inputs["atb"].get(), "", "", 1, 5, 0)
            core.create_interpretation(exp_id, ther_id, 3, 3, float(self.inputs["score"].get() or 50), "PAS", 0, 0, 1, 1, 0, "Manual input")
            messagebox.showinfo("Успех", "Запись сохранена!")
            self.refresh_kpis()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def setup_import_tab(self):
        self.tab_import.grid_columnconfigure(0, weight=1)
        
        frame = ctk.CTkFrame(self.tab_import)
        frame.pack(pady=40, padx=40, fill="both")
        
        ctk.CTkLabel(frame, text="Управление данными", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        ctk.CTkButton(frame, text="Импортировать CSV (Legacy)", command=self.import_csv, width=300).pack(pady=10)
        
        self.migrate_btn = ctk.CTkButton(frame, text="Миграция из старых БД (v6-v8)", command=self.run_migration, width=300, fg_color="#6366f1")
        self.migrate_btn.pack(pady=10)
        
        if not core.previous_db(): self.migrate_btn.configure(state="disabled", text="Старые БД не найдены")

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            try:
                stats = core.import_legacy_csv(path)
                messagebox.showinfo("Импорт", f"Успешно импортировано: {stats['interpretations']} записей")
                self.refresh_kpis()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка импорта: {e}")

    def run_migration(self):
        prev = core.previous_db()
        if prev:
            stats = core.migrate_from_previous_db(prev)
            messagebox.showinfo("Миграция", f"Завершено! Перенесено {stats['interpretations']} записей.")
            self.refresh_kpis()

    def setup_help_tab(self):
        text = (
            "Инструкция PhageATB Native v9:\n\n"
            "1. Подбор (Ranking): Основной экран для поиска синергичных комбинаций.\n"
            "   - Используйте фильтры для уточнения поиска.\n"
            "   - Итоговый балл (Итог) учитывает эффект, доказательность и качество.\n\n"
            "2. Аудит: Проверка всех записей базы на предмет блокирующих проблем.\n\n"
            "3. Консенсус: Группировка данных по парам Фаг+АТБ для поиска самого сильного сигнала.\n\n"
            "4. Ввод данных: Ручное добавление новых исследований в базу.\n\n"
            "5. Импорт: Загрузка данных из CSV шаблона v4."
        )
        ctk.CTkTextbox(self.tab_help, width=600, height=400).pack(padx=20, pady=20, fill="both", expand=True)
        self.tab_help.winfo_children()[0].insert("1.0", text)

if __name__ == "__main__":
    app = PhageATBApp()
    app.mainloop()
