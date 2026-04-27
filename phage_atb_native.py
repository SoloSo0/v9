import customtkinter as ctk
import core_logic as core
import pandas as pd
from tkinter import ttk, messagebox, filedialog
import sys
import os
from PIL import Image, ImageTk
import tkinter as tk
import logging
import traceback

# --- Logging Setup ---
logger = logging.getLogger("NativeApp")

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    messagebox.showerror("Critical Error", f"An unexpected error occurred:\n{exc_value}\n\nCheck app.log for details.")

sys.excepthook = handle_exception

class AutocompleteEntry(ctk.CTkEntry):
    def __init__(self, master, suggestions=None, **kwargs):
        super().__init__(master, **kwargs)
        self.suggestions = sorted(list(set(suggestions))) if suggestions else []
        self._hits = []
        self._hit_index = 0
        self.listbox = None
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._hide_listbox)
        self.bind('<Down>', self._on_down)
        self.bind('<Up>', self._on_up)
        self.bind('<Return>', self._on_enter)

    def _on_keyrelease(self, event):
        if event.keysym in ('Up', 'Down', 'Return', 'Escape', 'Tab'):
            return
            
        value = self.get()
        if not value:
            self._hide_listbox()
            return
            
        # Для полей с запятыми (например, список АТБ) берем последнее слово
        if ',' in value:
            parts = value.split(',')
            current_term = parts[-1].strip().lower()
            prefix = ",".join(parts[:-1]) + ", "
        else:
            current_term = value.strip().lower()
            prefix = ""

        if not current_term:
            self._hide_listbox()
            return

        # Fuzzy search: ищем вхождение подстроки в любом месте
        hits = [s for s in self.suggestions if current_term in s.lower()]
        
        # Сортируем: сначала те, что начинаются на current_term, потом остальные
        hits.sort(key=lambda x: (not x.lower().startswith(current_term), x.lower()))
        
        self._show_listbox(hits, prefix)

    def _show_listbox(self, hits, prefix):
        self._current_prefix = prefix # Сохраняем префикс для метода _on_select
        if not hits:
            self._hide_listbox()
            return
            
        if not hasattr(self, 'listbox_win') or not self.listbox_win:
            # Создаем плавающее окно для списка
            self.listbox_win = tk.Toplevel(self.winfo_toplevel())
            self.listbox_win.withdraw()
            self.listbox_win.overrideredirect(True)
            self.listbox_win.attributes("-topmost", True)
            self.listbox = tk.Listbox(self.listbox_win, bg="#2d2d2d", fg="white", 
                                    selectbackground="#005a9e", font=("Segoe UI Variable Text", 10),
                                    borderwidth=0, highlightthickness=1, highlightbackground="#3d3d3d")
            self.listbox.pack(fill="both", expand=True)
            self.listbox.bind('<ButtonRelease-1>', self._on_select)
            
        self.listbox.delete(0, "end")
        for hit in hits[:10]: # Ограничиваем 10 подсказками
            self.listbox.insert("end", hit)
            
        # Позиционируем окно под Entry
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = self.winfo_width()
        
        # Высота зависит от количества элементов
        h = min(len(hits), 10) * 25
        self.listbox_win.geometry(f"{w}x{h}+{x}+{y}")
        self.listbox_win.deiconify()
        self.listbox_win.lift()

    def _hide_listbox(self, event=None):
        if hasattr(self, 'listbox_win') and self.listbox_win:
            # Небольшая задержка, чтобы успел сработать клик по списку
            self.after(200, self.listbox_win.withdraw)

    def _on_select(self, event=None):
        if self.listbox.curselection():
            selection = self.listbox.get(self.listbox.curselection())
            prefix = getattr(self, '_current_prefix', "")
            self.delete(0, "end")
            self.insert(0, prefix + selection)
            self.focus_set() # Возвращаем фокус в поле ввода
            self.icursor("end") # Курсор в конец
            self.listbox_win.withdraw()

    def _on_down(self, event):
        if self.listbox and self.listbox.winfo_viewable():
            self.listbox.focus_set()
            self.listbox.selection_set(0)
            return "break"

    def _on_up(self, event):
        if self.listbox and self.listbox.winfo_viewable():
            self.listbox.focus_set()
            self.listbox.selection_set("end")
            return "break"

    def _on_enter(self, event):
        if hasattr(self, 'listbox_win') and self.listbox_win.winfo_viewable():
            self._on_select()
            return "break"

class PhageATBApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize core
        core.run_schema()
        self.suggestions = core.get_unique_suggestions()

        self.title(core.APP_TITLE)
        self.geometry("1400x900")
        
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Windows 11 Inspired Color Palette (Mica Dark)
        self.colors = {
            "bg_dark": "#1c1c1c",        # Windows 11 Mica Dark background
            "bg_card": "#2d2d2d",        # Elevated surface
            "accent": "#60cdff",         # Windows 11 Light Blue accent
            "success": "#6ccb5f",        # Windows 11 Success green
            "text_main": "#ffffff",
            "text_dim": "#a1a1a1",       # Secondary text
            "border": "#3d3d3d",         # Subtle border
            "hover": "#353535"           # Hover state
        }

        # Global styles for Treeview (Windows 11 Fluent style)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background=self.colors["bg_card"], 
                        foreground=self.colors["text_main"], 
                        fieldbackground=self.colors["bg_card"], 
                        borderwidth=0, 
                        font=("Segoe UI Variable Text", 10),
                        rowheight=38)    # More airy rows
        
        style.configure("Treeview.Heading", 
                        background=self.colors["bg_dark"], 
                        foreground="white", 
                        relief="flat", 
                        font=("Segoe UI Variable Display", 10, "bold"),
                        padding=5)
        
        # Фикс слияния при наведении (Hover state)
        style.map("Treeview.Heading",
                  background=[('active', self.colors["hover"]), ('pressed', self.colors["accent"])],
                  foreground=[('active', self.colors["accent"]), ('pressed', "black")])
        
        style.map("Treeview", 
                  background=[('selected', "#005a9e")], # Windows 11 Selection Blue
                  foreground=[('selected', "white")])
        
        # Add alternating row colors
        self.tree_tag_colors = {"even": "#2d2d2d", "odd": "#252525"}

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
        self.tab_analytics = self.tabview.add("Аналитика")
        self.tab_calc = self.tabview.add("Калькулятор")
        self.tab_input = self.tabview.add("Ввод данных")
        self.tab_import = self.tabview.add("Импорт / Миграция")
        self.tab_about = self.tabview.add("О программе")
        self.tab_help = self.tabview.add("Справка")

        self.setup_ranking_tab()
        self.setup_audit_tab()
        self.setup_consensus_tab()
        self.setup_analytics_tab()
        self.setup_calc_tab()
        self.setup_input_tab()
        self.setup_import_tab()
        self.setup_about_tab()
        self.setup_help_tab()

        # Bind keyboard shortcuts for copy/paste
        self.bind_shortcuts()

    def bind_shortcuts(self):
        """Привязка стандартных горячих клавиш для работы с текстом (универсальный метод)"""
        # Привязываем основные комбинации (английская раскладка)
        self.bind_all("<Control-v>", self._on_paste)
        self.bind_all("<Control-V>", self._on_paste)
        self.bind_all("<Control-c>", self._on_copy)
        self.bind_all("<Control-C>", self._on_copy)
        self.bind_all("<Control-x>", self._on_cut)
        self.bind_all("<Control-X>", self._on_cut)
        self.bind_all("<Control-a>", self._on_select_all)
        self.bind_all("<Control-A>", self._on_select_all)
        
        # Универсальный перехватчик для других раскладок (через KeyCode)
        self.bind_all("<Control-KeyPress>", self._handle_control_keys)
        
        # Добавляем поддержку контекстного меню (правой кнопкой мыши)
        self.bind_all("<Button-3>", self._show_context_menu)

    def _handle_control_keys(self, event):
        """Обработчик Ctrl+Клавиша по кодам клавиш для поддержки всех раскладок"""
        # Windows KeyCodes: V=86, C=67, X=88, A=65
        if event.keycode == 86: # V / М
            return self._on_paste(event)
        elif event.keycode == 67: # C / С
            return self._on_copy(event)
        elif event.keycode == 88: # X / Ч
            return self._on_cut(event)
        elif event.keycode == 65: # A / Ф
            return self._on_select_all(event)

    def _get_active_widget(self):
        """Возвращает текущий активный виджет, поддерживающий текстовые операции"""
        widget = self.focus_get()
        if not widget:
            return None
        
        # В CustomTkinter focus_get() часто возвращает внутренний tkinter-виджет (Entry или Text)
        # Нам нужно проверить, поддерживает ли он нужные методы
        if hasattr(widget, "insert") and (hasattr(widget, "get") or hasattr(widget, "selection_get")):
            return widget
        return None

    def _on_paste(self, event):
        widget = self._get_active_widget()
        if widget:
            try:
                # Пытаемся получить текст из буфера
                text = self.clipboard_get()
                if not text:
                    return
                
                # Если это Entry (обычный или CTk)
                if hasattr(widget, "selection_present") and widget.selection_present():
                    widget.delete("sel.first", "sel.last")
                elif hasattr(widget, "tag_ranges") and widget.tag_ranges("sel"):
                    widget.delete("sel.first", "sel.last")
                
                widget.insert("insert", text)
                return "break"
            except:
                pass

    def _on_copy(self, event):
        widget = self._get_active_widget()
        if widget:
            try:
                text = ""
                if hasattr(widget, "selection_present") and widget.selection_present():
                    # Для Entry
                    start = widget.index("sel.first")
                    end = widget.index("sel.last")
                    text = widget.get()[start:end]
                else:
                    # Для Text/Textbox
                    text = widget.get("sel.first", "sel.last")
                
                if text:
                    self.clipboard_clear()
                    self.clipboard_append(text)
                return "break"
            except:
                pass

    def _on_cut(self, event):
        widget = self._get_active_widget()
        if widget:
            self._on_copy(event)
            try:
                if hasattr(widget, "selection_present") and widget.selection_present():
                    widget.delete("sel.first", "sel.last")
                else:
                    widget.delete("sel.first", "sel.last")
                return "break"
            except:
                pass

    def _on_select_all(self, event):
        widget = self._get_active_widget()
        if widget:
            if hasattr(widget, "select_range"):
                widget.select_range(0, 'end')
                widget.icursor('end')
            elif hasattr(widget, "tag_add"):
                widget.tag_add("sel", "1.0", "end")
            return "break"

    def _show_context_menu(self, event):
        """Показывает контекстное меню (Копировать/Вставить/Вырезать)"""
        widget = event.widget
        # Проверяем, является ли виджет текстовым полем
        if not (hasattr(widget, "insert") and hasattr(widget, "get")):
            return

        menu = ctk.CTkFrame(self, fg_color=self.colors["bg_card"], border_width=1, border_color=self.colors["border"])
        
        # Создаем простое меню через Toplevel или прямое позиционирование (здесь используем меню Tkinter для надежности)
        from tkinter import Menu
        tk_menu = Menu(self, tearoff=0, bg=self.colors["bg_card"], fg=self.colors["text_main"], font=("Segoe UI", 10))
        tk_menu.add_command(label="Вырезать", command=lambda: self._on_cut(None))
        tk_menu.add_command(label="Копировать", command=lambda: self._on_copy(None))
        tk_menu.add_command(label="Вставить", command=lambda: self._on_paste(None))
        tk_menu.add_separator()
        tk_menu.add_command(label="Выделить всё", command=lambda: self._on_select_all(None))
        
        try:
            tk_menu.tk_popup(event.x_root, event.y_root)
        finally:
            tk_menu.grab_release()

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
        # Hero frame (Windows 11 Mica style)
        self.hero_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=self.colors["bg_card"], border_width=1, border_color=self.colors["border"])
        self.hero_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        self.title_label = ctk.CTkLabel(self.hero_frame, text=core.APP_TITLE, font=ctk.CTkFont(family="Segoe UI Variable Display", size=32, weight="bold"))
        self.title_label.pack(pady=(20, 5))
        
        self.subtitle_label = ctk.CTkLabel(self.hero_frame, text="Профессиональная нативная система подбора фаготерапии v9", font=ctk.CTkFont(family="Segoe UI Variable Text", size=14), text_color=self.colors["text_dim"])
        self.subtitle_label.pack(pady=(0, 20))

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
                card = ctk.CTkFrame(self.kpi_frame, corner_radius=12, border_width=1, border_color=self.colors["border"], fg_color=self.colors["bg_card"])
                card.grid(row=0, column=i, padx=8, pady=10, sticky="nsew")
                
                ctk.CTkLabel(card, text=label, font=ctk.CTkFont(family="Segoe UI Variable Text", size=12, weight="bold"), text_color=self.colors["text_dim"]).pack(pady=(15, 0))
                val_lbl = ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"), text_color=self.colors["accent"])
                val_lbl.pack(pady=(0, 15))
                self.kpi_labels[label] = val_lbl
            else:
                self.kpi_labels[label].configure(text=str(value))

    def setup_ranking_tab(self):
        self.tab_ranking.grid_columnconfigure(0, weight=1)
        self.tab_ranking.grid_rowconfigure(1, weight=1)

        # Filters frame
        self.filters_frame = ctk.CTkFrame(self.tab_ranking, corner_radius=12, fg_color="transparent", border_width=1, border_color=self.colors["border"])
        self.filters_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Grid for filters
        # Row 0
        ctk.CTkLabel(self.filters_frame, text="Возбудитель:", font=("Segoe UI Variable Text", 10)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.rank_pathogen = AutocompleteEntry(self.filters_frame, suggestions=self.suggestions["pathogens"], width=220, corner_radius=8)
        self.rank_pathogen.insert(0, "Pseudomonas aeruginosa")
        self.rank_pathogen.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(self.filters_frame, text="Growth state:", font=("Segoe UI Variable Text", 10)).grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.rank_growth = ctk.CTkComboBox(self.filters_frame, values=["Любой", "biofilm", "planktonic"], corner_radius=8)
        self.rank_growth.grid(row=0, column=3, padx=10, pady=10)

        ctk.CTkLabel(self.filters_frame, text="Top-N:", font=("Segoe UI Variable Text", 10)).grid(row=0, column=4, padx=10, pady=10, sticky="e")
        self.rank_topn = ctk.CTkSlider(self.filters_frame, from_=3, to=20, number_of_steps=17, button_color=self.colors["accent"], button_hover_color="#005a9e")
        self.rank_topn.set(8)
        self.rank_topn.grid(row=0, column=5, padx=10, pady=10)

        # Row 1
        ctk.CTkLabel(self.filters_frame, text="Sensitive АТБ:", font=("Segoe UI Variable Text", 10)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.rank_sensitive = AutocompleteEntry(self.filters_frame, suggestions=self.suggestions["antibiotics"], width=220, corner_radius=8)
        self.rank_sensitive.insert(0, "Ceftazidime")
        self.rank_sensitive.grid(row=1, column=1, padx=10, pady=10)

        ctk.CTkLabel(self.filters_frame, text="Resistant АТБ:", font=("Segoe UI Variable Text", 10)).grid(row=1, column=2, padx=10, pady=10, sticky="e")
        self.rank_resistant = AutocompleteEntry(self.filters_frame, suggestions=self.suggestions["antibiotics"], width=200, corner_radius=8)
        self.rank_resistant.grid(row=1, column=3, padx=10, pady=10)

        self.rank_res_mode = ctk.CTkSegmentedButton(self.filters_frame, values=["strict", "soft"], corner_radius=8, selected_color=self.colors["accent"])
        self.rank_res_mode.set("strict")
        self.rank_res_mode.grid(row=1, column=4, columnspan=2, padx=10, pady=10)

        # Row 2
        self.rank_validated = ctk.CTkCheckBox(self.filters_frame, text="Только validated/curated", font=("Segoe UI Variable Text", 10), corner_radius=4)
        self.rank_validated.select()
        self.rank_validated.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.rank_mdr = ctk.CTkCheckBox(self.filters_frame, text="Приоритет MDR", font=("Segoe UI Variable Text", 10), corner_radius=4)
        self.rank_mdr.select()
        self.rank_mdr.grid(row=2, column=2, padx=10, pady=10)

        self.rank_active = ctk.CTkCheckBox(self.filters_frame, text="Только активные пары", font=("Segoe UI Variable Text", 10), corner_radius=4)
        self.rank_active.grid(row=2, column=3, padx=10, pady=10)

        self.run_btn = ctk.CTkButton(self.filters_frame, text="РАССЧИТАТЬ RANKING v9", command=self.run_ranking, font=("Segoe UI Variable Display", 12, "bold"), corner_radius=8, fg_color=self.colors["accent"], hover_color="#005a9e", text_color="#000000")
        self.run_btn.grid(row=2, column=4, padx=10, pady=10, sticky="ew")

        # Добавляем подсказки для фильтров
        self.create_tooltip(self.rank_res_mode, "Strict: Исключает АТБ с резистентностью.\nSoft: Снижает их рейтинг на 18 баллов.")
        self.create_tooltip(self.rank_active, "Фильтрует только те пары Фаг-АТБ,\nкоторые показали активность в исследованиях.")
        self.create_tooltip(self.rank_mdr, "Повышает приоритет для комбинаций,\nэффективных против MDR штаммов.")

        self.export_btn = ctk.CTkButton(self.filters_frame, text="ЭКСПОРТ EXCEL", command=self.export_ranking, font=("Segoe UI Variable Display", 12, "bold"), corner_radius=8, fg_color=self.colors["success"], hover_color="#2d7a26", text_color="#000000")
        self.export_btn.grid(row=2, column=5, padx=10, pady=10, sticky="ew")
        self.export_btn.configure(state="disabled")

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
        
        # Подсказки для колонок таблицы
        self.create_tooltip(self.table_frame, "Итог: Итоговый балл (0-100)\nДоказ.: Уровень доказательности (1-5)\nДоверие: Статистическая достоверность")

        self.tree.pack(side="left", expand=True, fill="both")
        
        # Настройка тегов для цветового кодирования уровней доказательности
        self.tree.tag_configure("ev_high", foreground="#2ecc71")  # Зеленый (4-5)
        self.tree.tag_configure("ev_med", foreground="#f1c40f")   # Желтый (3)
        self.tree.tag_configure("ev_low", foreground="#e67e22")   # Оранжевый (1-2)
        self.tree.tag_configure("ev_none", foreground="#95a5a6")  # Серый (0)
        
        # Тег для предупреждения о резистентности (Soft mode)
        # ВАЖНО: Теги в Treeview применяются в порядке их конфигурации. 
        # Последний сконфигурированный тег имеет приоритет.
        self.tree.tag_configure("res_warn", foreground="#e74c3c", font=("Segoe UI Variable Text", 10, "italic"))
        
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
        
        self.last_ranking_df = core.ranking_df(patient)
        if self.last_ranking_df.empty:
            messagebox.showinfo("Ranking", "Нет данных для отображения")
            self.export_btn.configure(state="disabled")
            return
            
        self.export_btn.configure(state="normal")
        for i, row in self.last_ranking_df.head(int(self.rank_topn.get())).iterrows():
            ev_score = row["evidence_score"]
            if ev_score >= 4: ev_tag = "ev_high"
            elif ev_score >= 3: ev_tag = "ev_med"
            elif ev_score >= 1: ev_tag = "ev_low"
            else: ev_tag = "ev_none"
            
            row_tag = "even" if i % 2 == 0 else "odd"
            
            # Если это резистентный вариант в Soft mode, переопределяем теги
            if row.get("resistant_override"):
                tags = (row_tag, "res_warn")
                atb_name = f"⚠️ {row['antibiotic']} (R)"
            else:
                tags = (row_tag, ev_tag)
                atb_name = row["atb"] if "atb" in row else row["antibiotic"]
            
            self.tree.insert("", "end", values=(
                row["phage"], atb_name, row["final_score"],
                row["relevance_score"], row["effect_score"], row["evidence_score"],
                row["confidence_score"], row["synergy_prediction"]
            ), tags=tags)
        
        self.tree.tag_configure("even", background=self.tree_tag_colors["even"])
        self.tree.tag_configure("odd", background=self.tree_tag_colors["odd"])

    def export_ranking(self):
        if not hasattr(self, 'last_ranking_df') or self.last_ranking_df.empty:
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if path:
            if core.export_to_excel(self.last_ranking_df.head(int(self.rank_topn.get())), path):
                messagebox.showinfo("Экспорт", "Отчет успешно сохранен!")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить отчет.")

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

    def setup_analytics_tab(self):
        self.tab_analytics.grid_columnconfigure(0, weight=1)
        self.tab_analytics.grid_rowconfigure(1, weight=1)
        
        # Controls
        ctrl_frame = ctk.CTkFrame(self.tab_analytics)
        ctrl_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkButton(ctrl_frame, text="Обновить аналитику", command=self.refresh_analytics, fg_color=self.colors["accent"]).pack(pady=10)
        
        # Plot area
        self.plot_frame = ctk.CTkFrame(self.tab_analytics, fg_color=self.colors["bg_card"])
        self.plot_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.plot_label = ctk.CTkLabel(self.plot_frame, text="Нажмите кнопку для генерации графиков")
        self.plot_label.pack(expand=True, fill="both")

    def refresh_analytics(self):
        # Получаем данные из текущего ранжирования (базовый набор)
        df = core.ranking_base_df()
        if df.empty:
            messagebox.showinfo("Аналитика", "Нет данных для анализа")
            return
            
        buf = core.generate_synergy_plot(df)
        if buf:
            img = Image.open(buf)
            # Масштабируем под размер окна
            img = img.resize((800, 480), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(800, 480))
            self.plot_label.configure(image=ctk_img, text="")
            self.plot_label.image = ctk_img # сохраняем ссылку

    def setup_calc_tab(self):
        self.tab_calc.grid_columnconfigure((0, 1), weight=1)
        
        # --- Phage Calculator ---
        phage_frame = ctk.CTkFrame(self.tab_calc, corner_radius=15, border_width=1, border_color=self.colors["border"])
        phage_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(phage_frame, text="Калькулятор Бактериофагов", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["accent"]).pack(pady=10)
        
        self.calc_phage_entries = {}
        phage_fields = [
            ("Концентрация бактерий (CFU/ml):", "cfu", "1e8"),
            ("Целевой MOI:", "moi", "1"),
            ("Объем среды (ml):", "vol", "10"),
            ("Концентрация стока фага (PFU/ml):", "stock", "1e10")
        ]
        
        for label, key, default in phage_fields:
            ctk.CTkLabel(phage_frame, text=label).pack(pady=(5, 0))
            entry = ctk.CTkEntry(phage_frame, width=200)
            entry.insert(0, default)
            entry.pack(pady=(0, 5))
            self.calc_phage_entries[key] = entry
            
        self.phage_res_label = ctk.CTkLabel(phage_frame, text="Нужный объем фага: ---", font=ctk.CTkFont(weight="bold"))
        self.phage_res_label.pack(pady=20)
        
        ctk.CTkButton(phage_frame, text="Рассчитать фаг", command=self.calculate_phage, fg_color=self.colors["accent"], text_color="#000000").pack(pady=10)
        
        # --- ATB Calculator ---
        atb_frame = ctk.CTkFrame(self.tab_calc, corner_radius=15, border_width=1, border_color=self.colors["border"])
        atb_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(atb_frame, text="Калькулятор Антибиотиков", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["success"]).pack(pady=10)
        
        self.calc_atb_entries = {}
        atb_fields = [
            ("Целевая концентрация (µg/ml):", "target", "16"),
            ("Концентрация стока (mg/ml):", "stock", "10"),
            ("Объем среды (ml):", "vol", "10")
        ]
        
        for label, key, default in atb_fields:
            ctk.CTkLabel(atb_frame, text=label).pack(pady=(5, 0))
            entry = ctk.CTkEntry(atb_frame, width=200)
            entry.insert(0, default)
            entry.pack(pady=(0, 5))
            self.calc_atb_entries[key] = entry
            
        self.atb_res_label = ctk.CTkLabel(atb_frame, text="Нужный объем АТБ: ---", font=ctk.CTkFont(weight="bold"))
        self.atb_res_label.pack(pady=20)
        
        ctk.CTkButton(atb_frame, text="Рассчитать АТБ", command=self.calculate_atb, fg_color=self.colors["success"], text_color="#000000").pack(pady=10)

    def create_tooltip(self, widget, text):
        """Создает простое всплывающее окно подсказки для виджета"""
        def enter(event):
            self.tooltip = tk.Toplevel(self)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")
            label = tk.Label(self.tooltip, text=text, justify='left',
                             background="#2c3e50", foreground="#ecf0f1",
                             relief='flat', borderwidth=0, padx=10, pady=5,
                             font=("Segoe UI Variable Text", 9))
            label.pack()
        def leave(event):
            if hasattr(self, "tooltip"):
                try:
                    self.tooltip.destroy()
                except:
                    pass
        
        # Некоторые виджеты CTk (например, SegmentedButton) не поддерживают прямой bind
        # Пытаемся привязаться к самому виджету или его внутренним компонентам
        try:
            widget.bind("<Enter>", enter)
            widget.bind("<Leave>", leave)
        except Exception:
            # Если прямой bind не сработал (NotImplementedError), пробуем через canvas или пропускаем
            try:
                if hasattr(widget, "_canvas"):
                    widget._canvas.bind("<Enter>", enter)
                    widget._canvas.bind("<Leave>", leave)
            except:
                pass

    def calculate_phage(self):
        try:
            cfu = float(self.calc_phage_entries["cfu"].get())
            moi = float(self.calc_phage_entries["moi"].get())
            vol = float(self.calc_phage_entries["vol"].get())
            stock = float(self.calc_phage_entries["stock"].get())
            
            # Нужное кол-во фагов = CFU * MOI * Volume
            needed_pfu = cfu * moi * vol
            needed_vol_ml = needed_pfu / stock
            needed_vol_mkl = needed_vol_ml * 1000
            
            self.phage_res_label.configure(text=f"Нужный объем фага: {needed_vol_mkl:.2f} µl")
        except Exception as e:
            messagebox.showerror("Ошибка", "Проверьте корректность введенных чисел (используйте 1e8 для экспоненциальной записи)")

    def calculate_atb(self):
        try:
            target = float(self.calc_atb_entries["target"].get()) # µg/ml
            stock = float(self.calc_atb_entries["stock"].get()) # mg/ml = 1000 µg/ml
            vol = float(self.calc_atb_entries["vol"].get()) # ml
            
            # C1 * V1 = C2 * V2
            # V1 = (C2 * V2) / C1
            # C2 = target (µg/ml), V2 = vol (ml), C1 = stock * 1000 (µg/ml)
            
            needed_vol_ml = (target * vol) / (stock * 1000)
            needed_vol_mkl = needed_vol_ml * 1000
            
            self.atb_res_label.configure(text=f"Нужный объем АТБ: {needed_vol_mkl:.2f} µl")
        except Exception as e:
            messagebox.showerror("Ошибка", "Проверьте корректность введенных чисел")

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
            ("Synergy Score (0-100):", "score"),
            ("Заметки / Абстракт:", "notes")
        ]
        
        self.inputs = {}
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(self.input_form, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            
            frame = ctk.CTkFrame(self.input_form, fg_color="transparent")
            frame.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            
            if key == "notes":
                entry = ctk.CTkTextbox(frame, width=400, height=100)
                entry.pack(side="left")
            elif key == "pathogen":
                entry = AutocompleteEntry(frame, suggestions=self.suggestions["pathogens"], width=400)
                entry.pack(side="left")
            elif key == "phage":
                entry = AutocompleteEntry(frame, suggestions=self.suggestions["phages"], width=400)
                entry.pack(side="left")
            elif key == "atb":
                entry = AutocompleteEntry(frame, suggestions=self.suggestions["antibiotics"], width=400)
                entry.pack(side="left")
            else:
                entry = ctk.CTkEntry(frame, width=400)
                entry.pack(side="left")
            
            self.inputs[key] = entry
            
            if key == "ref":
                btn = ctk.CTkButton(frame, text="Fetch DOI", width=80, command=self.fetch_doi, fg_color=self.colors["accent"])
                btn.pack(side="left", padx=5)
                self.create_tooltip(btn, "Автоматически загружает данные статьи по DOI\n(требуется интернет)")
            
        ctk.CTkButton(self.input_form, text="Сохранить запись", command=self.save_input, fg_color="#10b981").grid(row=len(fields), column=0, columnspan=2, pady=20)

    def fetch_doi(self):
        doi = self.inputs["ref"].get().strip()
        if not doi:
            messagebox.showwarning("Ввод", "Введите DOI или PMID")
            return

        # Валидация DOI/PMID формата
        if not (doi.startswith("10.") or doi.isdigit()):
            messagebox.showerror("Ошибка", "Некорректный формат DOI (должен начинаться с 10.) или PMID (только цифры)")
            return

        # Индикация загрузки
        original_text = self.inputs["ref"].get()
        self.inputs["ref"].delete(0, 'end')
        self.inputs["ref"].insert(0, "Загрузка данных...")
        self.inputs["ref"].configure(state="disabled")
        self.update_idletasks()
        
        try:
            metadata = core.fetch_pubmed_metadata(doi)
            self.inputs["ref"].configure(state="normal")
            self.inputs["ref"].delete(0, 'end')
            
            if metadata and metadata.get("reference"):
                self.inputs["ref"].insert(0, metadata["reference"])
                if metadata.get("year"):
                    self.inputs["year"].delete(0, 'end')
                    self.inputs["year"].insert(0, str(metadata["year"]))
                if metadata.get("notes"):
                    self.inputs["notes"].delete("1.0", "end")
                    self.inputs["notes"].insert("1.0", metadata["notes"])
                messagebox.showinfo("PubMed", "Данные успешно получены!")
            else:
                self.inputs["ref"].insert(0, original_text)
                messagebox.showwarning("PubMed", "Не удалось найти данные по этому идентификатору.")
        except Exception as e:
            self.inputs["ref"].configure(state="normal")
            self.inputs["ref"].delete(0, 'end')
            self.inputs["ref"].insert(0, original_text)
            messagebox.showerror("Ошибка", f"Сбой при загрузке: {e}")

    def save_input(self):
        try:
            ref = self.inputs["ref"].get()
            year = int(self.inputs["year"].get() or 2026)
            notes = self.inputs["notes"].get("1.0", "end-1c")
            
            art_id = core.create_article(ref, year, "", "in vitro", notes)
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
