from __future__ import annotations
import pandas as pd
import streamlit as st
import core_logic as core
from core_logic import t, tf, norm, as_num, split_csv, normalize_pathogen, normalize_antibiotic, normalize_growth_state

def status_label(status: str) -> str:
    mapping = {
        "validated": {"ru": "validated", "en": "validated"},
        "curated": {"ru": "curated", "en": "curated"},
        "raw": {"ru": "raw", "en": "raw"},
        "excluded": {"ru": "excluded", "en": "excluded"},
    }
    return mapping.get(str(status), {}).get(st.session_state.get("ui_lang", "ru"), str(status))

def render_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #0b1120 0%, #111827 48%, #0f172a 100%); color: #e5eef8; }
        .block-container { max-width: 1480px; padding-top: 1.2rem; }
        .hero { background: linear-gradient(135deg, #020617 0%, #0f2f4d 55%, #134e4a 100%); border-radius: 24px; padding: 1.4rem 1.5rem; color: #f8fafc; margin-bottom: 1rem; }
        .hero h1 { margin: 0 0 0.35rem 0; font-size: 2rem; }
        .hero p { margin: 0; color: rgba(226,232,240,0.9); }
        .kpi { background: linear-gradient(180deg, rgba(15, 23, 42, 0.92) 0%, rgba(17, 24, 39, 0.96) 100%); border: 1px solid rgba(71, 85, 105, 0.42); border-radius: 18px; padding: 0.9rem 1rem; }
        .kpi-label { color: #9fb1c5; font-size: 0.8rem; }
        .kpi-value { color: #f8fafc; font-size: 1.55rem; font-weight: 700; }
        .card { background: linear-gradient(180deg, rgba(15,23,42,0.94) 0%, rgba(17,24,39,0.98) 100%); border: 1px solid rgba(71,85,105,0.40); border-radius: 22px; padding: 1rem 1.1rem; margin-bottom: 1rem; }
        .card-title { color: #f8fafc; font-size: 1.15rem; font-weight: 800; margin-bottom: 0.25rem; }
        .card-sub { color: #9fb1c5; font-size: 0.92rem; margin-bottom: 0.65rem; }
        .pill { display: inline-block; border-radius: 999px; padding: 0.22rem 0.62rem; font-size: 0.78rem; font-weight: 700; margin: 0 0.38rem 0.45rem 0; border: 1px solid transparent; }
        .pill-status { background: rgba(59,130,246,0.16); color: #bfdbfe; border-color: rgba(59,130,246,0.35); }
        .pill-high { background: rgba(16,185,129,0.16); color: #a7f3d0; border-color: rgba(16,185,129,0.35); }
        .pill-medium { background: rgba(59,130,246,0.16); color: #bfdbfe; border-color: rgba(59,130,246,0.35); }
        .pill-low { background: rgba(245,158,11,0.16); color: #fde68a; border-color: rgba(245,158,11,0.35); }
        .pill-danger { background: rgba(239,68,68,0.16); color: #fecaca; border-color: rgba(239,68,68,0.35); }
        .pill-neutral { background: rgba(148,163,184,0.12); color: #dbe7f3; border-color: rgba(148,163,184,0.26); }
        .metric-box { background: rgba(15,23,42,0.58); border: 1px solid rgba(71,85,105,0.28); border-radius: 14px; padding: 0.7rem 0.8rem; }
        .metric-label { color: #8ea4bb; font-size: 0.76rem; margin-bottom: 0.18rem; }
        .metric-value { color: #f8fafc; font-size: 1.02rem; font-weight: 700; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def kpi(label: str, value: object) -> None:
    st.markdown(f"""<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>""", unsafe_allow_html=True)

def pill_class_for_status(status: str) -> str:
    mapping = {"validated": "pill-high", "curated": "pill-medium", "raw": "pill-low", "excluded": "pill-danger"}
    return mapping.get(str(status), "pill-neutral")

def confidence_band(score: float) -> str:
    if score >= 80: return "high"
    if score >= 60: return "medium"
    if score >= 40: return "low"
    return "exclude"

def pill_class_for_confidence(score: float) -> str:
    mapping = {"high": "pill-high", "medium": "pill-medium", "low": "pill-low", "exclude": "pill-danger"}
    return mapping[confidence_band(score)]

def render_metric_box(label: str, value: object) -> None:
    st.markdown(f"""<div class="metric-box"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>""", unsafe_allow_html=True)

def interpretation_measurements_df(interpretation_id: int) -> pd.DataFrame:
    return core.query_df(
        """
        SELECT measurement_type, measurement_value, measurement_unit, raw_text, is_primary_endpoint
        FROM effect_measurements
        WHERE experiment_id = (SELECT experiment_id FROM outcome_interpretations WHERE id = ?)
          AND therapy_id = (SELECT therapy_id FROM outcome_interpretations WHERE id = ?)
        ORDER BY is_primary_endpoint DESC, id
        """,
        [interpretation_id, interpretation_id],
    )

def render_result_card(row: pd.Series) -> None:
    status_class = pill_class_for_status(str(row["record_status"]))
    conf_class = pill_class_for_confidence(float(row["confidence_score"]))
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{row["phage"]} + {row["antibiotic"]}</div>
            <div class="card-sub">{row["pathogen"]} | {row["reference"]}</div>
            <div>
                <span class="pill {status_class}">status {row["record_status"]}</span>
                <span class="pill {conf_class}">confidence {row["confidence_score"]}</span>
                <span class="pill pill-neutral">{row["synergy_prediction"]}</span>
                <span class="pill pill-neutral">evidence {row["evidence_level"]}</span>
                <span class="pill pill-neutral">quality {row["quality_score"]}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if bool(row.get("resistant_override", False)):
        st.markdown('<span class="pill pill-danger">resistant override</span>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: render_metric_box(t("final_score"), row["final_score"])
    with m2: render_metric_box(t("relevance"), row["relevance_score"])
    with m3: render_metric_box(t("effect"), row["effect_score"])
    with m4: render_metric_box(t("evidence"), row["evidence_score"])
    st.markdown(f"**{t('why_ranked')}:** {row['why_it_ranked']}")
    measurements = interpretation_measurements_df(int(row["interpretation_id"]))
    if not measurements.empty:
        with st.expander(t("evidence_base"), expanded=False):
            st.dataframe(measurements, width="stretch", hide_index=True)
            if str(row.get("warning_flags", "")).strip(): st.caption(f"Предупреждения: {row['warning_flags']}")
            if str(row.get("critical_flags", "")).strip(): st.caption(f"Critical flags: {row['critical_flags']}")

def render_audit_card(row: pd.Series) -> None:
    status_class = pill_class_for_status(str(row["record_status"]))
    conf_class = pill_class_for_confidence(float(row["confidence_score"]))
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{row["phage"]} + {row["antibiotic"]}</div>
            <div class="card-sub">{row["pathogen"]} | {row["reference"]}</div>
            <div>
                <span class="pill {status_class}">status {row["record_status"]}</span>
                <span class="pill {conf_class}">confidence {row["confidence_score"]}</span>
                <span class="pill pill-neutral">evidence {row["evidence_level"]}</span>
                <span class="pill pill-neutral">quality {row["quality_score"]}</span>
                <span class="pill pill-neutral">synergy {row["synergy_score"]}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if str(row.get("critical_flags", "")).strip(): st.error(f"Blocking issues: {row['critical_flags']}")
    if str(row.get("warning_flags", "")).strip(): st.warning(f"Warnings: {row['warning_flags']}")

def render_help() -> None:
    st.subheader(t("guide_title"))
    st.markdown(
        "- `effect_measurements` хранят отдельные измерения эффекта\n"
        "- `outcome_interpretations` хранят уже нормализованную интерпретацию\n"
        "- `record_statuses` отделяют существование записи от допуска в ranking\n"
        "- `validation_issues` хранят формализованные проблемы качества\n"
        "- `consensus` показывает агрегированный сигнал по комбинации"
    )

TRANSLATIONS = {
    "app_title": {"ru": "Фаг + АТБ подбор v9", "en": "Phage + Antibiotic Selector v9"},
    "hero_text": {"ru": "Новая схема базы: отдельно факты, отдельно измерения эффекта, отдельно интерпретации и статусы зрелости записи.", "en": "New database model: facts, effect measurements, interpretations, and record maturity statuses are stored separately."},
    "warning": {"ru": "v9 остаётся исследовательским инструментом. Он не заменяет клиническое решение.", "en": "v9 remains a research tool. It does not replace a clinical decision."},
    "tab_ranking": {"ru": "Подбор", "en": "Ranking"},
    "tab_audit": {"ru": "Аудит", "en": "Audit"},
    "tab_consensus": {"ru": "Консенсус", "en": "Consensus"},
    "tab_input": {"ru": "Ввод", "en": "Input"},
    "tab_import": {"ru": "Импорт и миграция", "en": "Import and Migration"},
    "tab_help": {"ru": "Памятка", "en": "Guide"},
    "language": {"ru": "Язык", "en": "Language"},
    "articles": {"ru": "Статей", "en": "Articles"},
    "experiments": {"ru": "Экспериментов", "en": "Experiments"},
    "therapies": {"ru": "Терапий", "en": "Therapies"},
    "measurements": {"ru": "Измерений", "en": "Measurements"},
    "interpretations": {"ru": "Интерпретаций", "en": "Interpretations"},
    "pathogen": {"ru": "Возбудитель", "en": "Pathogen"},
    "top_n": {"ru": "Top-N", "en": "Top-N"},
    "sensitive": {"ru": "Sensitive АТБ", "en": "Sensitive antibiotics"},
    "resistant": {"ru": "Resistant АТБ", "en": "Resistant antibiotics"},
    "resistant_mode": {"ru": "Режим resistant", "en": "Resistant mode"},
    "min_evidence": {"ru": "Минимальный evidence_level", "en": "Minimum evidence level"},
    "min_confidence": {"ru": "Минимальный confidence", "en": "Minimum confidence"},
    "only_validated": {"ru": "Только validated/curated", "en": "Validated/curated only"},
    "priority_mdr": {"ru": "Приоритет MDR", "en": "Prioritize MDR"},
    "priority_xdr": {"ru": "Приоритет XDR", "en": "Prioritize XDR"},
    "only_active_pairs": {"ru": "Только активные пары", "en": "Only active pairs"},
    "exclude_antagonism": {"ru": "Исключить antagonism", "en": "Exclude antagonism"},
    "run_ranking": {"ru": "Рассчитать ranking v9", "en": "Run v9 ranking"},
    "no_data": {"ru": "Нет данных для расчёта.", "en": "No data available for ranking."},
    "shown_pairs": {"ru": "Показано комбинаций", "en": "Pairs shown"},
    "avg_conf": {"ru": "Средний confidence", "en": "Average confidence"},
    "validated_records": {"ru": "Validated записей", "en": "Validated records"},
    "left_out": {"ru": "Что осталось за бортом", "en": "Excluded from ranking"},
    "guide_title": {"ru": "Памятка v9", "en": "v9 Guide"},
    "growth_focus": {"ru": "Фокус по росту", "en": "Growth state focus"},
    "any": {"ru": "Любой", "en": "Any"},
    "download_csv": {"ru": "Скачать ranking CSV", "en": "Download ranking CSV"},
    "found_prev_db": {"ru": "Найдена предыдущая база: {path}", "en": "Previous database found: {path}"},
    "migrate_to_v9": {"ru": "Перенести данные в v9", "en": "Migrate data to v9"},
    "migrate_done": {"ru": "Перенос завершён. Статей: {articles}, экспериментов: {experiments}, терапий: {therapies}, измерений: {measurements}, интерпретаций: {interpretations}.", "en": "Migration completed. Articles: {articles}, experiments: {experiments}, therapies: {therapies}, measurements: {measurements}, interpretations: {interpretations}."},
    "status": {"ru": "статус", "en": "status"},
    "blocking_issues": {"ru": "Блокирующие проблемы", "en": "Blocking issues"},
    "warnings": {"ru": "Предупреждения", "en": "Warnings"},
    "critical_flags": {"ru": "Критические флаги", "en": "Critical flags"},
    "why_ranked": {"ru": "Почему система подняла запись", "en": "Why the system ranked this record"},
    "evidence_base": {"ru": "Доказательная база и measurements", "en": "Evidence base and measurements"},
    "final_score": {"ru": "Итоговый балл", "en": "Final score"},
    "relevance": {"ru": "Релевантность", "en": "Relevance"},
    "effect": {"ru": "Эффект", "en": "Effect"},
    "evidence": {"ru": "Доказательность", "en": "Evidence"},
    "quality": {"ru": "Качество", "en": "Quality"},
    "synergy": {"ru": "Синергия", "en": "Synergy"},
    "resistant_override": {"ru": "переопределение resistant", "en": "resistant override"},
    "audit_empty": {"ru": "База пока пустая.", "en": "The database is still empty."},
    "total_interpretations": {"ru": "Всего интерпретаций", "en": "Total interpretations"},
    "excluded": {"ru": "Исключено", "en": "Excluded"},
    "low_confidence": {"ru": "Низкий confidence", "en": "Low confidence"},
    "show_status": {"ru": "Показать статус", "en": "Show status"},
    "all": {"ru": "Все", "en": "All"},
    "full_audit": {"ru": "Полная audit-таблица", "en": "Full audit table"},
    "consensus_empty": {"ru": "Пока нет данных для консенсуса.", "en": "No data for consensus yet."},
    "filter_pathogen": {"ru": "Фильтр по pathogen", "en": "Filter by pathogen"},
    "filter_antibiotic": {"ru": "Фильтр по antibiotic", "en": "Filter by antibiotic"},
    "consensus_summary": {"ru": "Краткая интерпретация консенсуса", "en": "Consensus summary"},
    "quick_input": {"ru": "Быстрый ввод v9", "en": "Quick v9 input"},
    "reference": {"ru": "Источник / reference", "en": "Reference"},
    "year": {"ru": "Год", "en": "Year"},
    "study_type": {"ru": "Тип исследования", "en": "Study type"},
    "phage": {"ru": "Фаг / коктейль", "en": "Phage / cocktail"},
    "antibiotic": {"ru": "Антибиотик", "en": "Antibiotic"},
    "growth_state": {"ru": "Состояние роста", "en": "Growth state"},
    "synergy_type": {"ru": "Тип синергии", "en": "Synergy type"},
    "save_record": {"ru": "Сохранить запись", "en": "Save record"},
    "record_saved": {"ru": "Запись сохранена. interpretation_id={id}", "en": "Record saved. interpretation_id={id}"},
    "upload_legacy": {"ru": "Загрузить legacy CSV", "en": "Upload legacy CSV"},
    "use_demo": {"ru": "Использовать demo CSV", "en": "Use demo CSV"},
    "import_to_v9": {"ru": "Импортировать CSV в v9", "en": "Import CSV into v9"},
    "import_done": {"ru": "Импорт завершён. Статей: {articles}, экспериментов: {experiments}, терапий: {therapies}, измерений: {measurements}, интерпретаций: {interpretations}.", "en": "Import completed. Articles: {articles}, experiments: {experiments}, therapies: {therapies}, measurements: {measurements}, interpretations: {interpretations}."},
    "status_validated": {"ru": "validated", "en": "validated"},
    "status_curated": {"ru": "curated", "en": "curated"},
    "status_raw": {"ru": "raw", "en": "raw"},
    "status_excluded": {"ru": "excluded", "en": "excluded"},
    "avg_confidence": {"ru": "Средний confidence", "en": "Average confidence"},
    "migration_found": {"ru": "Найдена предыдущая база: {db}", "en": "Previous database found: {db}"},
}

def t(key: str) -> str:
    lang = st.session_state.get("ui_lang", "ru")
    return TRANSLATIONS.get(key, {}).get(lang, key)

def tf(key: str, **kwargs) -> str:
    return t(key).format(**kwargs)

def main() -> None:
    core.run_schema()
    st.set_page_config(page_title=core.APP_TITLE, layout="wide")
    render_styles()
    st.session_state.setdefault("ui_lang", "ru")
    st.selectbox(t("language"), options=["ru", "en"], key="ui_lang", format_func=lambda x: "Русский" if x == "ru" else "English")
    st.markdown(f"""<div class="hero"><h1>{t("app_title")}</h1><p>{t("hero_text")}</p></div>""", unsafe_allow_html=True)
    st.warning(t("warning"))

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: kpi(t("articles"), core.table_count("articles"))
    with m2: kpi(t("experiments"), core.table_count("experiments"))
    with m3: kpi(t("therapies"), core.table_count("therapies"))
    with m4: kpi(t("measurements"), core.table_count("effect_measurements"))
    with m5: kpi(t("interpretations"), core.table_count("outcome_interpretations"))

    tabs = st.tabs([t("tab_ranking"), t("tab_audit"), t("tab_consensus"), t("tab_input"), t("tab_import"), t("tab_help")])

    with tabs[0]:
        prev = core.previous_db()
        if core.is_empty() and prev is not None:
            st.info(tf("found_prev_db", path=prev))
            if st.button(t("migrate_to_v9"), use_container_width=True):
                stats = core.migrate_from_previous_db(prev)
                st.success(tf("migrate_done", **stats))
                st.rerun()
        
        c1, c2, c3 = st.columns(3)
        pathogen = c1.text_input(t("pathogen"), "Pseudomonas aeruginosa")
        growth_mode = c2.selectbox(t("growth_focus"), [t("any"), "biofilm", "planktonic"])
        top_n = c3.slider(t("top_n"), 3, 20, 8)
        
        c4, c5, c6 = st.columns(3)
        sensitive = c4.text_input(t("sensitive"), "Ceftazidime")
        resistant = c5.text_input(t("resistant"), "")
        resistant_mode = c6.radio(t("resistant_mode"), ["strict", "soft"], horizontal=True)
        
        c7, c8, c9 = st.columns(3)
        min_evidence = c7.slider(t("min_evidence"), 0, 5, 1)
        min_confidence = c8.slider(t("min_confidence"), 0, 100, 45)
        only_validated = c9.checkbox(t("only_validated"), value=True)
        
        c10, c11, c12 = st.columns(3)
        wants_mdr = c10.checkbox(t("priority_mdr"), value=True)
        wants_xdr = c11.checkbox(t("priority_xdr"), value=False)
        only_active_pairs = c12.checkbox(t("only_active_pairs"), value=False)
        
        exclude_antagonism = st.checkbox(t("exclude_antagonism"), value=True)
        
        if st.button(t("run_ranking"), type="primary", use_container_width=True):
            patient = {
                "pathogen": normalize_pathogen(pathogen),
                "growth_mode": growth_mode,
                "sensitive": [norm(normalize_antibiotic(x)) for x in split_csv(sensitive)],
                "resistant": [norm(normalize_antibiotic(x)) for x in split_csv(resistant)],
                "resistant_mode": resistant_mode,
                "wants_mdr": wants_mdr,
                "wants_xdr": wants_xdr,
                "min_evidence": min_evidence,
                "min_confidence": min_confidence,
                "exclude_antagonism": exclude_antagonism,
                "only_active_pairs": only_active_pairs,
                "only_validated": only_validated,
            }
            result = core.ranking_df(patient)
            if result.empty:
                st.warning(t("no_data"))
            else:
                top = result.head(top_n)
                s1, s2, s3 = st.columns(3)
                with s1: kpi(t("shown_pairs"), len(top))
                with s2: kpi(t("avg_conf"), round(float(top["confidence_score"].mean()), 1))
                with s3: kpi(t("validated_records"), int((top["record_status"] == "validated").sum()))
                
                for _, row in top.iterrows():
                    render_result_card(row)
                
                excluded = result[~result["eligible_for_ranking"]].head(8)
                if not excluded.empty:
                    st.subheader(t("left_out"))
                    st.dataframe(excluded[["phage", "antibiotic", "pathogen", "record_status", "exclusion_reason", "critical_flags", "warning_flags"]], width="stretch", height=220)
                
                st.download_button(t("download_csv"), data=result.head(top_n).to_csv(index=False).encode("utf-8-sig"), file_name="phage_atb_ranking_v9.csv", mime="text/csv")

    with tabs[1]:
        audit = core.audit_df()
        if audit.empty:
            st.info(t("audit_empty"))
        else:
            a1, a2, a3, a4 = st.columns(4)
            with a1: kpi(t("total_interpretations"), len(audit))
            with a2: kpi(t("excluded"), int((audit["record_status"] == "excluded").sum()))
            with a3: kpi(t("low_confidence"), int((audit["confidence_score"] < 60).sum()))
            with a4: kpi(t("avg_confidence"), round(float(audit["confidence_score"].mean()), 1))
            
            status_options = [("all", t("all")), ("validated", t("status_validated")), ("curated", t("status_curated")), ("raw", t("status_raw")), ("excluded", t("status_excluded"))]
            selected_status_label = st.selectbox(t("show_status"), [label for _, label in status_options])
            status_filter = dict((label, value) for value, label in status_options)[selected_status_label]
            view = audit if status_filter == "all" else audit[audit["record_status"] == status_filter]
            with st.expander(t("full_audit"), expanded=False):
                st.dataframe(view, width="stretch", height=360)

    with tabs[2]:
        consensus = core.consensus_df()
        if consensus.empty:
            st.info(t("consensus_empty"))
        else:
            c1, c2 = st.columns(2)
            pathogen_filter = c1.text_input(t("filter_pathogen"), "")
            antibiotic_filter = c2.text_input(t("filter_antibiotic"), "")
            view = consensus.copy()
            if pathogen_filter.strip():
                view = view[view["pathogen"].str.contains(pathogen_filter, case=False, na=False)]
            if antibiotic_filter.strip():
                view = view[view["antibiotic"].str.contains(antibiotic_filter, case=False, na=False)]
            st.dataframe(view, width="stretch", height=450)

    with tabs[3]:
        st.subheader(t("quick_input"))
        with st.form("input_form"):
            c1, c2, c3 = st.columns(3)
            reference = c1.text_input(t("reference"), "New Study 2026")
            year = c2.number_input(t("year"), 2000, 2030, 2026)
            study_type = c3.selectbox(t("study_type"), ["in vitro", "animal", "clinical", "case report"])
            
            c4, c5, c6 = st.columns(3)
            pathogen_in = c4.text_input(t("pathogen"), "Klebsiella pneumoniae")
            phage_in = c5.text_input(t("phage"), "K.p. Phage 1")
            antibiotic_in = c6.text_input(t("antibiotic"), "Meropenem")
            
            c7, c8, c9 = st.columns(3)
            growth_in = c7.selectbox(t("growth_state"), ["planktonic", "biofilm"])
            synergy_in = c8.selectbox(t("synergy_type"), ["PAS", "additive", "antagonism", "none"])
            score_in = c9.slider("Synergy Score", 0, 100, 50)
            
            if st.form_submit_button(t("save_record")):
                art_id = core.create_article(reference, year, "", study_type, "")
                exp_id = core.create_experiment(art_id, pathogen_in, "strain X", "source", growth_in, "model", 1 if growth_in == "biofilm" else 0, 1, 1, 0, 1, 1, 0)
                ther_id = core.create_therapy(phage_in, antibiotic_in, "", "", 1, 5, 0)
                int_id = core.create_interpretation(exp_id, ther_id, 3, 3, score_in, synergy_in, 0, 0, 1, 1, 0, "Manual input")
                st.success(tf("record_saved", id=int_id))

    with tabs[4]:
        st.subheader(t("tab_import"))
        up = st.file_view = st.file_uploader(t("upload_legacy"), type=["csv"])
        if up:
            if st.button(t("import_to_v9")):
                # Save to temp file as import_legacy_csv expects path
                temp_path = "temp_import.csv"
                with open(temp_path, "wb") as f: f.write(up.getbuffer())
                stats = core.import_legacy_csv(temp_path)
                st.success(tf("import_done", **stats))
                st.rerun()

    with tabs[5]:
        render_help()

if __name__ == "__main__":
    main()
