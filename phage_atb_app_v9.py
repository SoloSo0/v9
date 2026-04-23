from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Dict, Iterable, List

import pandas as pd
import streamlit as st

APP_TITLE = "Фаг + АТБ подбор v9"
APP_DIR = Path(__file__).resolve().parent
DB_FILE = APP_DIR / "phage_atb_v9.db"
LEGACY_TEMPLATE = APP_DIR / "phage_antibiotic_template_v4.csv"
PREV_DBS = [
    APP_DIR.parent / "v8" / "phage_atb_v8.db",
    APP_DIR.parent / "v7" / "phage_atb_v7.db",
    APP_DIR.parent / "v6" / "phage_atb_v6.db",
]

PATHOGEN_ALIASES = {
    "p. aeruginosa": "Pseudomonas aeruginosa",
    "pseudomonas aeruginosa": "Pseudomonas aeruginosa",
    "k. pneumoniae": "Klebsiella pneumoniae",
    "klebsiella pneumoniae": "Klebsiella pneumoniae",
    "s. aureus": "Staphylococcus aureus",
    "staphylococcus aureus": "Staphylococcus aureus",
}
ANTIBIOTIC_ALIASES = {
    "ceftazidim": "Ceftazidime",
    "ceftazidime": "Ceftazidime",
    "tobramycin": "Tobramycin",
    "vancomycin": "Vancomycin",
}

TRANSLATIONS = {
    "app_title": {"ru": "Фаг + АТБ подбор v9", "en": "Phage + Antibiotic Selector v9"},
    "hero_text": {
        "ru": "Новая схема базы: отдельно факты, отдельно измерения эффекта, отдельно интерпретации и статусы зрелости записи.",
        "en": "New database model: facts, effect measurements, interpretations, and record maturity statuses are stored separately.",
    },
    "warning": {
        "ru": "v9 остаётся исследовательским инструментом. Он не заменяет клиническое решение.",
        "en": "v9 remains a research tool. It does not replace a clinical decision.",
    },
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
    "migrate_done": {
        "ru": "Перенос завершён. Статей: {articles}, экспериментов: {experiments}, терапий: {therapies}, измерений: {measurements}, интерпретаций: {interpretations}.",
        "en": "Migration completed. Articles: {articles}, experiments: {experiments}, therapies: {therapies}, measurements: {measurements}, interpretations: {interpretations}.",
    },
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
    "import_done": {
        "ru": "Импорт завершён. Статей: {articles}, экспериментов: {experiments}, терапий: {therapies}, измерений: {measurements}, интерпретаций: {interpretations}.",
        "en": "Import completed. Articles: {articles}, experiments: {experiments}, therapies: {therapies}, measurements: {measurements}, interpretations: {interpretations}.",
    },
}


def get_lang() -> str:
    return st.session_state.get("ui_lang", "ru")


def t(key: str) -> str:
    return TRANSLATIONS.get(key, {}).get(get_lang(), key)


def tf(key: str, **kwargs) -> str:
    return t(key).format(**kwargs)


def status_label(status: str) -> str:
    mapping = {
        "validated": {"ru": "validated", "en": "validated"},
        "curated": {"ru": "curated", "en": "curated"},
        "raw": {"ru": "raw", "en": "raw"},
        "excluded": {"ru": "excluded", "en": "excluded"},
    }
    return mapping.get(str(status), {}).get(get_lang(), str(status))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def norm(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def as_num(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def split_csv(text: str) -> List[str]:
    return [norm(x) for x in str(text).split(",") if x.strip()]


def normalize_pathogen(value: str) -> str:
    text = str(value).strip()
    return PATHOGEN_ALIASES.get(norm(text), text)


def normalize_antibiotic(value: str) -> str:
    text = str(value).strip()
    normalized = ANTIBIOTIC_ALIASES.get(norm(text), text)
    return normalized.title() if normalized and normalized == normalized.lower() else normalized


def normalize_growth_state(value: str) -> str:
    text = norm(value)
    if text in {"", "biofilm", "planktonic"}:
        return text
    if text == "any":
        return ""
    return text


def query_df(sql: str, params: Iterable | None = None) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=list(params or []))


def table_count(table: str) -> int:
    with get_conn() as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def run_schema() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_key TEXT UNIQUE NOT NULL,
                reference TEXT NOT NULL,
                year INTEGER DEFAULT 0,
                doi TEXT DEFAULT '',
                study_type TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_key TEXT UNIQUE NOT NULL,
                article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                pathogen TEXT NOT NULL,
                strain TEXT DEFAULT '',
                sample_source TEXT DEFAULT '',
                growth_state TEXT DEFAULT '',
                infection_model TEXT DEFAULT '',
                biofilm INTEGER DEFAULT 0,
                n_strains_tested REAL DEFAULT 0,
                replicated INTEGER DEFAULT 0,
                direct_isolate_match INTEGER DEFAULT 0,
                species_match INTEGER DEFAULT 0,
                mdr_relevant INTEGER DEFAULT 0,
                xdr_relevant INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS therapies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                therapy_key TEXT UNIQUE NOT NULL,
                phage TEXT NOT NULL,
                phage_target TEXT DEFAULT '',
                phage_cocktail_size REAL DEFAULT 0,
                antibiotic TEXT NOT NULL,
                antibiotic_class TEXT DEFAULT '',
                host_range_score REAL DEFAULT 0,
                resistance_tradeoff REAL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS effect_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
                therapy_id INTEGER NOT NULL REFERENCES therapies(id) ON DELETE CASCADE,
                measurement_type TEXT NOT NULL,
                measurement_value REAL DEFAULT 0,
                measurement_unit TEXT DEFAULT '',
                raw_text TEXT DEFAULT '',
                is_primary_endpoint INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS outcome_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
                therapy_id INTEGER NOT NULL REFERENCES therapies(id) ON DELETE CASCADE,
                primary_measurement_id INTEGER REFERENCES effect_measurements(id) ON DELETE SET NULL,
                evidence_level REAL DEFAULT 0,
                quality_score REAL DEFAULT 0,
                synergy_score REAL DEFAULT 0,
                synergy_type TEXT DEFAULT '',
                phage_active INTEGER DEFAULT 0,
                antibiotic_active INTEGER DEFAULT 0,
                toxicity_signal REAL DEFAULT 0,
                interpretation_notes TEXT DEFAULT '',
                curated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS record_statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                record_status TEXT NOT NULL,
                status_reason TEXT DEFAULT '',
                reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS validation_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                severity TEXT NOT NULL,
                issue_code TEXT NOT NULL,
                issue_message TEXT NOT NULL,
                is_blocking INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def previous_db() -> Path | None:
    for path in PREV_DBS:
        if path.exists():
            return path
    return None


def is_empty() -> bool:
    return table_count("outcome_interpretations") == 0


def issue_dict(severity: str, code: str, message: str, blocking: int) -> Dict:
    return {"severity": severity, "issue_code": code, "issue_message": message, "is_blocking": blocking}


def derive_issues(payload: Dict) -> List[Dict]:
    issues: List[Dict] = []
    if not str(payload.get("reference", "")).strip():
        issues.append(issue_dict("critical", "missing_reference", "Нет reference статьи.", 1))
    if not str(payload.get("pathogen", "")).strip():
        issues.append(issue_dict("critical", "missing_pathogen", "Не указан pathogen.", 1))
    growth = normalize_growth_state(payload.get("growth_state", ""))
    if growth not in {"", "biofilm", "planktonic"}:
        issues.append(issue_dict("critical", "bad_growth_state", "growth_state вне допустимого набора.", 1))
    if as_num(payload.get("biofilm", 0)) > 0 and growth == "planktonic":
        issues.append(issue_dict("warning", "growth_conflict", "biofilm=1 конфликтует с growth_state=planktonic.", 0))
    max_evidence = {"in vitro": 2, "ex vivo": 3, "animal": 3, "in vivo": 4, "case report": 4, "case series": 4, "clinical": 5, "clinical observational": 4, "prospective": 5, "rct": 5, "meta-analysis": 5, "": 3}.get(norm(payload.get("study_type", "")), 3)
    if as_num(payload.get("evidence_level", 0)) > max_evidence:
        issues.append(issue_dict("warning", "overstated_evidence", "evidence_level выглядит завышенным для типа исследования.", 0))
    if norm(payload.get("synergy_type", "")) == "pas" and as_num(payload.get("synergy_score", 0)) < 55 and as_num(payload.get("mic_fold_reduction", 0)) < 2 and as_num(payload.get("log_reduction", 0)) < 1:
        issues.append(issue_dict("warning", "weak_pas_claim", "PAS заявлен, но количественные метрики слабы.", 0))
    if as_num(payload.get("quality_score", 0)) < 1:
        issues.append(issue_dict("warning", "low_quality", "Очень низкий quality_score.", 0))
    return issues


def status_from_payload(payload: Dict) -> tuple[str, str]:
    issues = derive_issues(payload)
    if any(issue["is_blocking"] for issue in issues):
        return "excluded", "Есть blocking issues."
    if as_num(payload.get("quality_score", 0)) >= 3 and as_num(payload.get("evidence_level", 0)) >= 2:
        return "validated", "Запись выглядит пригодной для ranking."
    return "curated", "Запись структурирована, но требует осторожности."


def write_status_and_issues(conn: sqlite3.Connection, interpretation_id: int, payload: Dict) -> None:
    status, reason = status_from_payload(payload)
    conn.execute(
        "INSERT INTO record_statuses(entity_type, entity_id, record_status, status_reason) VALUES ('interpretation', ?, ?, ?)",
        [interpretation_id, status, reason],
    )
    for issue in derive_issues(payload):
        conn.execute(
            """
            INSERT INTO validation_issues(entity_type, entity_id, severity, issue_code, issue_message, is_blocking)
            VALUES ('interpretation', ?, ?, ?, ?, ?)
            """,
            [interpretation_id, issue["severity"], issue["issue_code"], issue["issue_message"], issue["is_blocking"]],
        )


def create_article(reference: str, year: int, doi: str, study_type: str, notes: str) -> int:
    article_key = "|".join([norm(reference), norm(doi), str(year or 0)])
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO articles(article_key, reference, year, doi, study_type, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(article_key) DO UPDATE SET
                reference=excluded.reference, year=excluded.year, doi=excluded.doi, study_type=excluded.study_type, notes=excluded.notes
            """,
            [article_key, reference.strip(), int(year or 0), doi.strip(), study_type.strip(), notes.strip()],
        )
        conn.commit()
        return int(conn.execute("SELECT id FROM articles WHERE article_key = ?", [article_key]).fetchone()[0])


def create_experiment(article_id: int, pathogen: str, strain: str, sample_source: str, growth_state: str, infection_model: str, biofilm: int, n_strains_tested: float, replicated: int, direct_isolate_match: int, species_match: int, mdr_relevant: int, xdr_relevant: int) -> int:
    pathogen = normalize_pathogen(pathogen)
    growth_state = normalize_growth_state(growth_state)
    key = "|".join([str(article_id), norm(pathogen), norm(strain), norm(sample_source), norm(growth_state), norm(infection_model)])
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO experiments(
                experiment_key, article_id, pathogen, strain, sample_source, growth_state, infection_model,
                biofilm, n_strains_tested, replicated, direct_isolate_match, species_match, mdr_relevant, xdr_relevant
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(experiment_key) DO UPDATE SET
                pathogen=excluded.pathogen, strain=excluded.strain, sample_source=excluded.sample_source, growth_state=excluded.growth_state,
                infection_model=excluded.infection_model, biofilm=excluded.biofilm, n_strains_tested=excluded.n_strains_tested,
                replicated=excluded.replicated, direct_isolate_match=excluded.direct_isolate_match, species_match=excluded.species_match,
                mdr_relevant=excluded.mdr_relevant, xdr_relevant=excluded.xdr_relevant
            """,
            [key, article_id, pathogen, strain.strip(), sample_source.strip(), growth_state.strip(), infection_model.strip(), int(biofilm), float(n_strains_tested), int(replicated), int(direct_isolate_match), int(species_match), int(mdr_relevant), int(xdr_relevant)],
        )
        conn.commit()
        return int(conn.execute("SELECT id FROM experiments WHERE experiment_key = ?", [key]).fetchone()[0])


def create_therapy(phage: str, antibiotic: str, phage_target: str, antibiotic_class: str, cocktail_size: float, host_range_score: float, resistance_tradeoff: float) -> int:
    antibiotic = normalize_antibiotic(antibiotic)
    key = "|".join([norm(phage), norm(antibiotic), norm(phage_target), norm(antibiotic_class)])
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO therapies(
                therapy_key, phage, phage_target, phage_cocktail_size, antibiotic, antibiotic_class, host_range_score, resistance_tradeoff
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(therapy_key) DO UPDATE SET
                phage=excluded.phage, phage_target=excluded.phage_target, phage_cocktail_size=excluded.phage_cocktail_size,
                antibiotic=excluded.antibiotic, antibiotic_class=excluded.antibiotic_class, host_range_score=excluded.host_range_score,
                resistance_tradeoff=excluded.resistance_tradeoff
            """,
            [key, phage.strip(), phage_target.strip(), float(cocktail_size), antibiotic.strip(), antibiotic_class.strip(), float(host_range_score), float(resistance_tradeoff)],
        )
        conn.commit()
        return int(conn.execute("SELECT id FROM therapies WHERE therapy_key = ?", [key]).fetchone()[0])


def create_interpretation(experiment_id: int, therapy_id: int, evidence_level: float, quality_score: float, synergy_score: float, synergy_type: str, mic_fold_reduction: float, log_reduction: float, phage_active: int, antibiotic_active: int, toxicity_signal: float, notes: str) -> int:
    with get_conn() as conn:
        primary_id = None
        if synergy_score > 0:
            cur = conn.execute(
                "INSERT INTO effect_measurements(experiment_id, therapy_id, measurement_type, measurement_value, measurement_unit, raw_text, is_primary_endpoint) VALUES (?, ?, 'synergy_score', ?, 'score', ?, 1)",
                [experiment_id, therapy_id, float(synergy_score), f"synergy_score={synergy_score}"],
            )
            primary_id = int(cur.lastrowid)
        if mic_fold_reduction > 0:
            conn.execute(
                "INSERT INTO effect_measurements(experiment_id, therapy_id, measurement_type, measurement_value, measurement_unit, raw_text) VALUES (?, ?, 'mic_fold_reduction', ?, 'fold', ?)",
                [experiment_id, therapy_id, float(mic_fold_reduction), f"mic_fold_reduction={mic_fold_reduction}"],
            )
        if log_reduction > 0:
            conn.execute(
                "INSERT INTO effect_measurements(experiment_id, therapy_id, measurement_type, measurement_value, measurement_unit, raw_text) VALUES (?, ?, 'log_reduction', ?, 'log', ?)",
                [experiment_id, therapy_id, float(log_reduction), f"log_reduction={log_reduction}"],
            )
        cur = conn.execute(
            """
            INSERT INTO outcome_interpretations(
                experiment_id, therapy_id, primary_measurement_id, evidence_level, quality_score, synergy_score,
                synergy_type, phage_active, antibiotic_active, toxicity_signal, interpretation_notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [experiment_id, therapy_id, primary_id, float(evidence_level), float(quality_score), float(synergy_score), synergy_type.strip(), int(phage_active), int(antibiotic_active), float(toxicity_signal), notes.strip()],
        )
        interpretation_id = int(cur.lastrowid)
        joined = conn.execute(
            """
            SELECT a.reference, a.study_type, e.pathogen, e.growth_state, e.biofilm, e.n_strains_tested
            FROM experiments e JOIN articles a ON a.id = e.article_id WHERE e.id = ?
            """,
            [experiment_id],
        ).fetchone()
        payload = {
            "reference": joined["reference"] if joined else "",
            "study_type": joined["study_type"] if joined else "",
            "pathogen": joined["pathogen"] if joined else "",
            "growth_state": joined["growth_state"] if joined else "",
            "biofilm": joined["biofilm"] if joined else 0,
            "n_strains_tested": joined["n_strains_tested"] if joined else 0,
            "evidence_level": evidence_level,
            "quality_score": quality_score,
            "synergy_score": synergy_score,
            "synergy_type": synergy_type,
            "mic_fold_reduction": mic_fold_reduction,
            "log_reduction": log_reduction,
        }
        write_status_and_issues(conn, interpretation_id, payload)
        conn.commit()
        return interpretation_id


def migrate_from_previous_db(path: Path) -> Dict[str, int]:
    source = sqlite3.connect(path)
    source.row_factory = sqlite3.Row
    try:
        has_outcomes = bool(source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='outcomes'").fetchone())
        for row in source.execute("SELECT * FROM articles ORDER BY id"):
            create_article(row["reference"], int(row["year"] or 0), row["doi"], row["study_type"], row["notes"] if "notes" in row.keys() else "")
        for row in source.execute("SELECT * FROM experiments ORDER BY id"):
            create_experiment(row["article_id"], row["pathogen"], row["strain"], row["sample_source"], row["growth_state"], row["infection_model"], int(row["biofilm"]), as_num(row["n_strains_tested"]), int(row["replicated"]), int(row["direct_isolate_match"]), int(row["species_match"]), int(row["mdr_relevant"]), int(row["xdr_relevant"]))
        for row in source.execute("SELECT * FROM therapies ORDER BY id"):
            cocktail = row["cocktail_size"] if "cocktail_size" in row.keys() else row["phage_cocktail_size"] if "phage_cocktail_size" in row.keys() else 0
            create_therapy(row["phage"], row["antibiotic"], row["phage_target"], row["antibiotic_class"], as_num(cocktail), as_num(row["host_range_score"]), as_num(row["resistance_tradeoff"]))
        if has_outcomes:
            for row in source.execute("SELECT * FROM outcomes ORDER BY id"):
                create_interpretation(row["experiment_id"], row["therapy_id"], as_num(row["evidence_level"]), as_num(row["quality_score"]), as_num(row["synergy_score"]), row["synergy_type"], as_num(row["mic_fold_reduction"]), as_num(row["log_reduction"]), int(row["phage_active"]), int(row["antibiotic_active"]), as_num(row["toxicity_signal"]), row["notes"])
    finally:
        source.close()
    return {
        "articles": table_count("articles"),
        "experiments": table_count("experiments"),
        "therapies": table_count("therapies"),
        "measurements": table_count("effect_measurements"),
        "interpretations": table_count("outcome_interpretations"),
    }


def ranking_base_df() -> pd.DataFrame:
    return query_df(
        """
        SELECT
            i.id AS interpretation_id,
            a.reference, a.year, a.doi, a.study_type,
            e.id AS experiment_id, e.pathogen, e.strain, e.sample_source, e.growth_state, e.infection_model, e.n_strains_tested,
            e.replicated, e.direct_isolate_match, e.species_match, e.mdr_relevant, e.xdr_relevant, e.biofilm,
            t.id AS therapy_id, t.phage, t.antibiotic, t.phage_target, t.antibiotic_class, t.phage_cocktail_size, t.host_range_score, t.resistance_tradeoff,
            i.evidence_level, i.quality_score, i.synergy_score, i.synergy_type, i.phage_active, i.antibiotic_active, i.toxicity_signal, i.interpretation_notes,
            COALESCE(MAX(CASE WHEN m.measurement_type='mic_fold_reduction' THEN m.measurement_value END), 0) AS mic_fold_reduction,
            COALESCE(MAX(CASE WHEN m.measurement_type='log_reduction' THEN m.measurement_value END), 0) AS log_reduction,
            COALESCE(MAX(rs.record_status), 'raw') AS record_status
        FROM outcome_interpretations i
        JOIN experiments e ON e.id = i.experiment_id
        JOIN therapies t ON t.id = i.therapy_id
        JOIN articles a ON a.id = e.article_id
        LEFT JOIN effect_measurements m ON m.experiment_id = i.experiment_id AND m.therapy_id = i.therapy_id
        LEFT JOIN record_statuses rs ON rs.entity_type='interpretation' AND rs.entity_id=i.id
        GROUP BY i.id
        """
    )


def validation_flags(row: pd.Series) -> Dict[str, List[str]]:
    issues = query_df("SELECT severity, issue_message, is_blocking FROM validation_issues WHERE entity_type='interpretation' AND entity_id = ?", [int(row["interpretation_id"])])
    critical = [str(item["issue_message"]) for _, item in issues.iterrows() if int(item["is_blocking"]) > 0 or item["severity"] == "critical"]
    warnings = [str(item["issue_message"]) for _, item in issues.iterrows() if int(item["is_blocking"]) == 0 and item["severity"] != "critical"]
    return {"critical": critical, "warnings": warnings}


def confidence_score(row: pd.Series) -> float:
    flags = validation_flags(row)
    score = 100.0 - len(flags["critical"]) * 30 - len(flags["warnings"]) * 8
    score -= 4 if not str(row.get("doi", "")).strip() else 0
    score -= 6 if as_num(row.get("replicated", 0)) <= 0 else 0
    score += 8 if as_num(row.get("direct_isolate_match", 0)) > 0 else 0
    score += 4 if as_num(row.get("species_match", 0)) > 0 else 0
    score += 6 if as_num(row.get("n_strains_tested", 0)) >= 5 else 3 if as_num(row.get("n_strains_tested", 0)) >= 2 else 0
    score += min(as_num(row.get("quality_score", 0)), 5) * 2.5
    score += min(as_num(row.get("evidence_level", 0)), 5) * 1.5
    score += 6 if row.get("record_status", "") == "validated" else -25 if row.get("record_status", "") == "excluded" else 0
    return round(max(0.0, min(100.0, score)), 1)


def classify_synergy(synergy_type: str, synergy_score: float, mic_fold: float, log_red: float) -> str:
    stype = norm(synergy_type)
    if stype == "antagonism":
        return "antagonism"
    if stype == "pas":
        return "PAS"
    if synergy_score >= 85 or mic_fold >= 8 or log_red >= 3:
        return "strong synergy"
    if synergy_score >= 65 or mic_fold >= 4 or log_red >= 2:
        return "moderate synergy"
    if synergy_score >= 45 or mic_fold >= 2 or log_red >= 1:
        return "weak synergy"
    return "unclear"


def ranking_eligibility(row: pd.Series, patient: Dict) -> tuple[bool, str]:
    flags = validation_flags(row)
    if flags["critical"]:
        return False, flags["critical"][0]
    if patient["only_validated"] and row["record_status"] not in {"validated", "curated"}:
        return False, "Статус записи ниже порога ranking."
    if patient["resistant_mode"] == "strict" and norm(row["antibiotic"]) in patient["resistant"]:
        return False, "Антибиотик отмечен как resistant."
    if as_num(row["evidence_level"]) < patient["min_evidence"]:
        return False, "Недостаточный evidence_level."
    if confidence_score(row) < patient["min_confidence"]:
        return False, "Недостаточный confidence_score."
    return True, ""


def explain_row(row: pd.Series) -> str:
    parts: List[str] = []
    if row["relevance_score"] >= 30:
        parts.append("хорошее совпадение с текущим контекстом")
    if row["effect_score"] >= 30:
        parts.append("сильный эффект комбинации")
    elif row["effect_score"] >= 18:
        parts.append("умеренный эффект комбинации")
    if row["evidence_score"] >= 18:
        parts.append("приличная доказательная база")
    if row["penalty_score"] >= 12:
        parts.append("есть штрафы за слабые места")
    return "; ".join(parts) if parts else "сигнал смешанный и требует осторожности"


def score_row(row: pd.Series, patient: Dict) -> float:
    fit = 0.0
    fit += 20 if norm(row["pathogen"]) == norm(patient["pathogen"]) else 0
    fit += 10 if patient["growth_mode"] != "Любой" and norm(row["growth_state"]) == norm(patient["growth_mode"]) else 0
    fit += 12 if norm(row["antibiotic"]) in patient["sensitive"] else 0
    fit -= 18 if norm(row["antibiotic"]) in patient["resistant"] and patient["resistant_mode"] == "strict" else 45 if norm(row["antibiotic"]) in patient["resistant"] else 0
    fit += 8 if patient["wants_mdr"] and as_num(row["mdr_relevant"]) > 0 else 0
    fit += 10 if patient["wants_xdr"] and as_num(row["xdr_relevant"]) > 0 else 0
    fit += as_num(row["phage_active"]) * 8 + as_num(row["antibiotic_active"]) * 7 + as_num(row["direct_isolate_match"]) * 12 + as_num(row["species_match"]) * 6
    effect = as_num(row["synergy_score"]) * 0.3 + min(as_num(row["mic_fold_reduction"]), 16) * 2.2 + min(as_num(row["log_reduction"]), 6) * 4.5
    evidence_component = as_num(row["evidence_level"]) * 8 + as_num(row["quality_score"]) * 5 + min(as_num(row["n_strains_tested"]), 40) * 0.7
    cocktail_component = min(as_num(row["phage_cocktail_size"]), 6) * 1.5 + min(as_num(row["host_range_score"]), 10) * 1.8
    penalty = as_num(row["toxicity_signal"]) * 8 + max(0, 60 - confidence_score(row)) * 0.35
    return round(evidence_component * 0.26 + effect * 0.28 + fit * 0.30 + cocktail_component * 0.08 + confidence_score(row) * 0.08 - penalty, 2)


def ranking_df(patient: Dict) -> pd.DataFrame:
    df = ranking_base_df()
    if df.empty:
        return df
    df["synergy_prediction"] = df.apply(lambda row: classify_synergy(row["synergy_type"], as_num(row["synergy_score"]), as_num(row["mic_fold_reduction"]), as_num(row["log_reduction"])), axis=1)
    df["confidence_score"] = df.apply(confidence_score, axis=1)
    flags = df.apply(validation_flags, axis=1)
    df["critical_flags"] = flags.apply(lambda item: " | ".join(item["critical"]))
    df["warning_flags"] = flags.apply(lambda item: " | ".join(item["warnings"]))
    eligibility = df.apply(lambda row: ranking_eligibility(row, patient), axis=1)
    df["eligible_for_ranking"] = eligibility.apply(lambda item: item[0])
    df["exclusion_reason"] = eligibility.apply(lambda item: item[1])
    df["relevance_score"] = df.apply(lambda row: max(0.0, (20 if norm(row["pathogen"]) == norm(patient["pathogen"]) else 0) + (10 if patient["growth_mode"] != "Любой" and norm(row["growth_state"]) == norm(patient["growth_mode"]) else 0) + (12 if norm(row["antibiotic"]) in patient["sensitive"] else 0) - (18 if norm(row["antibiotic"]) in patient["resistant"] else 0) + (8 if patient["wants_mdr"] and as_num(row["mdr_relevant"]) > 0 else 0) + (10 if patient["wants_xdr"] and as_num(row["xdr_relevant"]) > 0 else 0) + as_num(row["phage_active"]) * 8 + as_num(row["antibiotic_active"]) * 7 + as_num(row["direct_isolate_match"]) * 12 + as_num(row["species_match"]) * 6), axis=1)
    df["effect_score"] = df.apply(lambda row: round(as_num(row["synergy_score"]) * 0.3 + min(as_num(row["mic_fold_reduction"]), 16) * 2.2 + min(as_num(row["log_reduction"]), 6) * 4.5, 2), axis=1)
    df["evidence_score"] = df.apply(lambda row: round(as_num(row["evidence_level"]) * 8 + as_num(row["quality_score"]) * 5 + min(as_num(row["n_strains_tested"]), 40) * 0.7, 2), axis=1)
    df["penalty_score"] = df.apply(lambda row: round(as_num(row["toxicity_signal"]) * 8 + max(0, 60 - as_num(row["confidence_score"])) * 0.35, 2), axis=1)
    df["resistant_override"] = df.apply(lambda row: patient["resistant_mode"] == "soft" and norm(row["antibiotic"]) in patient["resistant"], axis=1)
    df["final_score"] = df.apply(lambda row: score_row(row, patient), axis=1)
    df["why_it_ranked"] = df.apply(explain_row, axis=1)
    if patient["exclude_antagonism"]:
        df = df[df["synergy_prediction"] != "antagonism"]
    if patient["only_active_pairs"]:
        df = df[(df["phage_active"] > 0) & (df["antibiotic_active"] > 0)]
    if patient["only_validated"]:
        df = df[df["eligible_for_ranking"]]
    return df.sort_values(["eligible_for_ranking", "resistant_override", "final_score"], ascending=[False, True, False])


def audit_df() -> pd.DataFrame:
    df = ranking_base_df()
    if df.empty:
        return df
    df["confidence_score"] = df.apply(confidence_score, axis=1)
    flags = df.apply(validation_flags, axis=1)
    df["critical_flags"] = flags.apply(lambda item: " | ".join(item["critical"]))
    df["warning_flags"] = flags.apply(lambda item: " | ".join(item["warnings"]))
    return df[["interpretation_id", "record_status", "reference", "pathogen", "phage", "antibiotic", "confidence_score", "evidence_level", "quality_score", "synergy_score", "critical_flags", "warning_flags"]].sort_values(["record_status", "confidence_score"], ascending=[True, True])


def consensus_df() -> pd.DataFrame:
    df = ranking_base_df()
    if df.empty:
        return df
    df["confidence_score"] = df.apply(confidence_score, axis=1)
    return df.groupby(["pathogen", "phage", "antibiotic", "growth_state"], dropna=False).agg(supporting_articles=("reference", "nunique"), mean_synergy_score=("synergy_score", "mean"), mean_confidence_score=("confidence_score", "mean"), max_evidence=("evidence_level", "max")).reset_index().sort_values(["mean_confidence_score", "mean_synergy_score"], ascending=False)


def normalize_legacy_row(row: pd.Series) -> Dict:
    growth_state_raw = str(row.get("growth_state", "")).strip() or ("biofilm" if as_num(row.get("biofilm", 0)) > 0 else "")
    return {
        "reference": str(row.get("reference", "")).strip() or "Без названия",
        "year": int(as_num(row.get("year", 0))),
        "doi": str(row.get("doi", "")).strip(),
        "study_type": str(row.get("study_type", "")).strip(),
        "pathogen": normalize_pathogen(row.get("pathogen", "")),
        "strain": str(row.get("strain", "")).strip(),
        "sample_source": str(row.get("sample_source", "")).strip(),
        "growth_state": normalize_growth_state(growth_state_raw),
        "infection_model": str(row.get("infection_model", "")).strip(),
        "biofilm": int(as_num(row.get("biofilm", 0))),
        "n_strains_tested": as_num(row.get("n_strains_tested", 0)),
        "replicated": int(as_num(row.get("replicated", 0))),
        "direct_isolate_match": int(as_num(row.get("direct_isolate_match", 0))),
        "species_match": int(as_num(row.get("species_match", 0))),
        "mdr_relevant": int(as_num(row.get("mdr_relevant", 0))),
        "xdr_relevant": int(as_num(row.get("xdr_relevant", 0))),
        "phage": str(row.get("phage", "")).strip(),
        "antibiotic": normalize_antibiotic(row.get("antibiotic", "")),
        "phage_target": str(row.get("phage_target", "")).strip(),
        "antibiotic_class": str(row.get("antibiotic_class", "")).strip(),
        "cocktail_size": as_num(row.get("cocktail_size", 0)),
        "host_range_score": as_num(row.get("host_range_score", 0)),
        "resistance_tradeoff": as_num(row.get("resistance_tradeoff", 0)),
        "evidence_level": as_num(row.get("evidence_level", 0)),
        "quality_score": as_num(row.get("quality_score", 0)),
        "synergy_score": as_num(row.get("synergy_score", 0)),
        "synergy_type": str(row.get("synergy_type", "")).strip(),
        "mic_fold_reduction": as_num(row.get("mic_fold_reduction", 0)),
        "log_reduction": as_num(row.get("log_reduction", 0)),
        "phage_active": int(as_num(row.get("phage_active", 0))),
        "antibiotic_active": int(as_num(row.get("antibiotic_active", 0))),
        "toxicity_signal": as_num(row.get("toxicity_signal", 0)),
        "notes": str(row.get("notes", "")).strip(),
    }


def build_import_review(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx, row in df.fillna("").iterrows():
        payload = normalize_legacy_row(row)
        issues = derive_issues(payload)
        rows.append({"row": int(idx) + 2, "reference": payload["reference"], "pathogen": payload["pathogen"], "phage": payload["phage"], "antibiotic": payload["antibiotic"], "status": "ok" if not any(item["is_blocking"] for item in issues) else "error", "issues": " | ".join(item["issue_message"] for item in issues)})
    return pd.DataFrame(rows)


def import_legacy_csv(file_obj) -> Dict[str, int]:
    df = pd.read_csv(file_obj)
    review = build_import_review(df)
    bad = review[review["status"] == "error"]
    if not bad.empty:
        sample = "; ".join([f'строка {item["row"]}: {item["issues"]}' for item in bad.head(10).to_dict("records")])
        raise ValueError("Импорт остановлен из-за blocking issues: " + sample)
    for _, row in df.fillna("").iterrows():
        payload = normalize_legacy_row(row)
        article_id = create_article(payload["reference"], payload["year"], payload["doi"], payload["study_type"], "")
        experiment_id = create_experiment(article_id, payload["pathogen"], payload["strain"], payload["sample_source"], payload["growth_state"], payload["infection_model"], payload["biofilm"], payload["n_strains_tested"], payload["replicated"], payload["direct_isolate_match"], payload["species_match"], payload["mdr_relevant"], payload["xdr_relevant"])
        therapy_id = create_therapy(payload["phage"], payload["antibiotic"], payload["phage_target"], payload["antibiotic_class"], payload["cocktail_size"], payload["host_range_score"], payload["resistance_tradeoff"])
        create_interpretation(experiment_id, therapy_id, payload["evidence_level"], payload["quality_score"], payload["synergy_score"], payload["synergy_type"], payload["mic_fold_reduction"], payload["log_reduction"], payload["phage_active"], payload["antibiotic_active"], payload["toxicity_signal"], payload["notes"])
    return {"articles": table_count("articles"), "experiments": table_count("experiments"), "therapies": table_count("therapies"), "measurements": table_count("effect_measurements"), "interpretations": table_count("outcome_interpretations")}


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
    mapping = {
        "validated": "pill-high",
        "curated": "pill-medium",
        "raw": "pill-low",
        "excluded": "pill-danger",
    }
    return mapping.get(str(status), "pill-neutral")


def confidence_band(score: float) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    if score >= 40:
        return "low"
    return "exclude"


def pill_class_for_confidence(score: float) -> str:
    mapping = {
        "high": "pill-high",
        "medium": "pill-medium",
        "low": "pill-low",
        "exclude": "pill-danger",
    }
    return mapping[confidence_band(score)]


def render_metric_box(label: str, value: object) -> None:
    st.markdown(
        f"""<div class="metric-box"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>""",
        unsafe_allow_html=True,
    )


def interpretation_measurements_df(interpretation_id: int) -> pd.DataFrame:
    return query_df(
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
    with m1:
        render_metric_box(t("final_score"), row["final_score"])
    with m2:
        render_metric_box(t("relevance"), row["relevance_score"])
    with m3:
        render_metric_box(t("effect"), row["effect_score"])
    with m4:
        render_metric_box(t("evidence"), row["evidence_score"])
    st.markdown(f"**Почему система подняла запись:** {row['why_it_ranked']}")
    measurements = interpretation_measurements_df(int(row["interpretation_id"]))
    if not measurements.empty:
        with st.expander("Доказательная база и measurements", expanded=False):
            st.dataframe(measurements, width="stretch", hide_index=True)
            if str(row.get("warning_flags", "")).strip():
                st.caption(f"Предупреждения: {row['warning_flags']}")
            if str(row.get("critical_flags", "")).strip():
                st.caption(f"Critical flags: {row['critical_flags']}")


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
    if str(row.get("critical_flags", "")).strip():
        st.error(f"Blocking issues: {row['critical_flags']}")
    if str(row.get("warning_flags", "")).strip():
        st.warning(f"Warnings: {row['warning_flags']}")


def render_help() -> None:
    st.subheader(t("guide_title"))
    st.markdown(
        "- `effect_measurements` хранят отдельные измерения эффекта\n"
        "- `outcome_interpretations` хранят уже нормализованную интерпретацию\n"
        "- `record_statuses` отделяют существование записи от допуска в ranking\n"
        "- `validation_issues` хранят формализованные проблемы качества\n"
        "- `consensus` показывает агрегированный сигнал по комбинации"
    )


def main() -> None:
    run_schema()
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    render_styles()
    st.session_state.setdefault("ui_lang", "ru")
    st.selectbox(t("language"), options=["ru", "en"], key="ui_lang", format_func=lambda x: "Русский" if x == "ru" else "English")
    st.markdown(f"""<div class="hero"><h1>{t("app_title")}</h1><p>{t("hero_text")}</p></div>""", unsafe_allow_html=True)
    st.warning(t("warning"))

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: kpi(t("articles"), table_count("articles"))
    with m2: kpi(t("experiments"), table_count("experiments"))
    with m3: kpi(t("therapies"), table_count("therapies"))
    with m4: kpi(t("measurements"), table_count("effect_measurements"))
    with m5: kpi(t("interpretations"), table_count("outcome_interpretations"))

    tabs = st.tabs([t("tab_ranking"), t("tab_audit"), t("tab_consensus"), t("tab_input"), t("tab_import"), t("tab_help")])

    with tabs[0]:
        prev = previous_db()
        if is_empty() and prev is not None:
            st.info(tf("migration_found", db=prev))
            if st.button(t("migrate_to_v9"), use_container_width=True):
                stats = migrate_from_previous_db(prev)
                st.success(f'Перенос завершён. Статей: {stats["articles"]}, экспериментов: {stats["experiments"]}, терапий: {stats["therapies"]}, измерений: {stats["measurements"]}, интерпретаций: {stats["interpretations"]}.')
                st.rerun()
        c1, c2, c3 = st.columns(3)
        pathogen = c1.text_input(t("pathogen"), "Pseudomonas aeruginosa")
        growth_mode = c2.selectbox("Growth state focus", ["Любой", "biofilm", "planktonic"])
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
            result = ranking_df(patient)
            if result.empty:
                st.warning(t("no_data"))
            else:
                top = result.head(top_n)
                s1, s2, s3 = st.columns(3)
                with s1:
                    kpi(t("shown_pairs"), len(top))
                with s2:
                    kpi(t("avg_conf"), round(float(top["confidence_score"].mean()), 1))
                with s3:
                    kpi(t("validated_records"), int((top["record_status"] == "validated").sum()))
                for _, row in top.iterrows():
                    render_result_card(row)
                excluded = result[~result["eligible_for_ranking"]].head(8)
                if not excluded.empty:
                    st.subheader(t("left_out"))
                    st.dataframe(
                        excluded[["phage", "antibiotic", "pathogen", "record_status", "exclusion_reason", "critical_flags", "warning_flags"]],
                        width="stretch",
                        height=220,
                    )
                st.download_button(t("download_csv"), data=result.head(top_n).to_csv(index=False).encode("utf-8-sig"), file_name="phage_atb_ranking_v9.csv", mime="text/csv")

    with tabs[1]:
        audit = audit_df()
        if audit.empty:
            st.info(t("audit_empty"))
        else:
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                kpi("Всего интерпретаций", len(audit))
            with a2:
                kpi(t("excluded"), int((audit["record_status"] == "excluded").sum()))
            with a3:
                kpi(t("low_confidence"), int((audit["confidence_score"] < 60).sum()))
            with a4:
                kpi(t("avg_confidence"), round(float(audit["confidence_score"].mean()), 1))
            status_options = [("all", t("all")), ("validated", t("status_validated")), ("curated", t("status_curated")), ("raw", t("status_raw")), ("excluded", t("status_excluded"))]
            selected_status_label = st.selectbox(t("show_status"), [label for _, label in status_options])
            status_filter = dict((label, value) for value, label in status_options)[selected_status_label]
            view = audit if status_filter == "all" else audit[audit["record_status"] == status_filter]
            with st.expander("Полная audit-таблица", expanded=False):
                st.dataframe(view, width="stretch", height=360)

    with tabs[2]:
        consensus = consensus_df()
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
            st.dataframe(view, width="stretch", height=380)
            if not view.empty:
                top_consensus = view.head(5)
                st.subheader(t("consensus_summary"))
                for _, row in top_consensus.iterrows():
                    st.markdown(
                        f"**{row['phage']} + {row['antibiotic']}** для `{row['pathogen']}`: "
                        f"поддержано источниками `{int(row['supporting_articles'])}`, "
                        f"средний synergy `{round(float(row['mean_synergy_score']), 1)}`, "
                        f"средний confidence `{round(float(row['mean_confidence_score']), 1)}`, "
                        f"максимальный evidence `{round(float(row['max_evidence']), 1)}`."
                    )

    with tabs[3]:
        st.subheader(t("quick_input"))
        with st.form("add_form", clear_on_submit=True):
            ref = st.text_area(t("reference"), height=80)
            a1, a2 = st.columns(2)
            year = a1.number_input("Год", 0, 2100, 2025, 1)
            study_type = a2.selectbox("Тип исследования", ["", "in vitro", "ex vivo", "animal", "in vivo", "case report", "case series", "clinical", "clinical observational", "prospective", "rct", "meta-analysis"])
            b1, b2, b3 = st.columns(3)
            pathogen_in = b1.text_input("Возбудитель")
            phage_in = b2.text_input("Фаг / коктейль")
            antibiotic_in = b3.text_input("Антибиотик")
            c1, c2, c3 = st.columns(3)
            growth_state_in = c1.selectbox("Growth state", ["", "biofilm", "planktonic"])
            mic_in = c2.number_input(t("mic_fold_reduction"), min_value=0.0, value=0.0, step=0.5)
            log_in = c3.number_input(t("log_reduction"), min_value=0.0, value=0.0, step=0.5)
            d1, d2, d3 = st.columns(3)
            evidence_in = d1.slider(t("evidence_level"), 0, 5, 1)
            quality_in = d2.slider(t("quality_score"), 0, 5, 1)
            synergy_in = d3.slider(t("synergy_score"), 0, 100, 50)
            synergy_type_in = st.selectbox(t("synergy_type"), ["", "PAS", "additive", "synergy", "antagonism"])
            if st.form_submit_button("Сохранить запись", use_container_width=True):
                article_id = create_article(ref, int(year), "", study_type, "")
                experiment_id = create_experiment(article_id, pathogen_in, "", "", growth_state_in, "", 1 if growth_state_in == "biofilm" else 0, 1.0, 0, 0, 1, 0, 0)
                therapy_id = create_therapy(phage_in, antibiotic_in, "", "", 0.0, 0.0, 0.0)
                interpretation_id = create_interpretation(experiment_id, therapy_id, evidence_in, quality_in, synergy_in, synergy_type_in, mic_in, log_in, 1, 1, 0.0, "")
                st.success(f"Запись сохранена. interpretation_id={interpretation_id}")
                st.rerun()

    with tabs[4]:
        uploaded = st.file_uploader(t("upload_legacy"), type=["csv"])
        use_demo = st.checkbox(t("use_demo"), value=False)
        source = uploaded if uploaded is not None else LEGACY_TEMPLATE if use_demo and LEGACY_TEMPLATE.exists() else None
        if source is not None:
            preview = pd.read_csv(source)
            st.dataframe(build_import_review(preview), width="stretch", height=260)
            if hasattr(source, "seek"):
                source.seek(0)
        if st.button(t("import_to_v9"), disabled=source is None, use_container_width=True):
            stats = import_legacy_csv(source)
            st.success(f'Импорт завершён. Статей: {stats["articles"]}, экспериментов: {stats["experiments"]}, терапий: {stats["therapies"]}, измерений: {stats["measurements"]}, интерпретаций: {stats["interpretations"]}.')
            st.rerun()

    with tabs[5]:
        render_help()


if __name__ == "__main__":
    main()
