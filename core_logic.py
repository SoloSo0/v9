from __future__ import annotations
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Iterable, List, Any
import os
import sys
import shutil

# --- Configuration & Paths ---
APP_TITLE = "Фаг + АТБ подбор v9.1"
VERSION = "9.1"
LAST_CHANGES = """
Версия 9.1 (Нативная):
- Полный переход со Streamlit на нативный GUI (CustomTkinter).
- Исправлены критические ошибки отрисовки шрифтов.
- Добавлена KPI-панель реального времени.
- Реализованы все вкладки: Ranking, Аудит, Консенсус, Ввод.
- Улучшена портативность (единый EXE без веб-сервера).
"""

if getattr(sys, 'frozen', False):
    # Если запущено как exe, база должна лежать рядом с exe
    EXE_DIR = Path(sys.executable).parent
    APP_DIR = Path(sys._MEIPASS)
    DB_FILE = EXE_DIR / "phage_atb_v9.db"
else:
    APP_DIR = Path(__file__).resolve().parent
    DB_FILE = APP_DIR / "phage_atb_v9.db"

LEGACY_TEMPLATE = APP_DIR / "phage_antibiotic_template_v4.csv"
PREV_DBS = [
    APP_DIR.parent / "v8" / "phage_atb_v8.db",
    APP_DIR.parent / "v7" / "phage_atb_v7.db",
    APP_DIR.parent / "v6" / "phage_atb_v6.db",
]

# --- Aliases ---
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

# --- Database Core ---
def get_conn() -> sqlite3.Connection:
    # Ensure initial DB exists in resource path for copy if needed
    if getattr(sys, 'frozen', False) and not DB_FILE.exists():
        resource_db = APP_DIR / "phage_atb_v9.db"
        if resource_db.exists():
            shutil.copy(resource_db, DB_FILE)
            
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

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

# --- Normalization Helpers ---
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

# --- Validation Logic ---
def issue_dict(severity: str, code: str, msg: str, blocking: int) -> Dict:
    return {"severity": severity, "issue_code": code, "issue_message": msg, "is_blocking": blocking}

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
    
    study_type_norm = norm(payload.get("study_type", ""))
    max_evidence = {"in vitro": 2, "ex vivo": 3, "animal": 3, "in vivo": 4, "case report": 4, "case series": 4, "clinical": 5, "clinical observational": 4, "prospective": 5, "rct": 5, "meta-analysis": 5, "": 3}.get(study_type_norm, 3)
    
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

def validation_flags(interpretation_id: int) -> Dict[str, List[str]]:
    issues = query_df("SELECT severity, issue_message, is_blocking FROM validation_issues WHERE entity_type='interpretation' AND entity_id = ?", [int(interpretation_id)])
    critical = [str(item["issue_message"]) for _, item in issues.iterrows() if int(item["is_blocking"]) > 0 or item["severity"] == "critical"]
    warnings = [str(item["issue_message"]) for _, item in issues.iterrows() if int(item["is_blocking"]) == 0 and item["severity"] != "critical"]
    return {"critical": critical, "warnings": warnings}

# --- Data Persistence ---
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

# --- Analysis & Ranking ---
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

def confidence_score(row: pd.Series) -> float:
    flags = validation_flags(row["interpretation_id"])
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
    if stype == "antagonism": return "antagonism"
    if stype == "pas": return "PAS"
    if synergy_score >= 85 or mic_fold >= 8 or log_red >= 3: return "strong synergy"
    if synergy_score >= 65 or mic_fold >= 4 or log_red >= 2: return "moderate synergy"
    if synergy_score >= 45 or mic_fold >= 2 or log_red >= 1: return "weak synergy"
    return "unclear"

def ranking_eligibility(row: pd.Series, patient: Dict) -> tuple[bool, str]:
    flags = validation_flags(row["interpretation_id"])
    if flags["critical"]:
        return False, flags["critical"][0]
    if patient.get("only_validated") and row["record_status"] not in {"validated", "curated"}:
        return False, "Статус записи ниже порога ranking."
    if patient.get("resistant_mode") == "strict" and norm(row["antibiotic"]) in patient.get("resistant", []):
        return False, "Антибиотик отмечен как resistant."
    if as_num(row["evidence_level"]) < patient.get("min_evidence", 0):
        return False, "Недостаточный evidence_level."
    if confidence_score(row) < patient.get("min_confidence", 0):
        return False, "Недостаточный confidence_score."
    return True, ""

def score_row(row: pd.Series, patient: Dict) -> float:
    fit = 0.0
    fit += 20 if norm(row["pathogen"]) == norm(patient.get("pathogen", "")) else 0
    fit += 10 if patient.get("growth_mode") != "Любой" and norm(row["growth_state"]) == norm(patient.get("growth_mode", "")) else 0
    fit += 12 if norm(row["antibiotic"]) in patient.get("sensitive", []) else 0
    fit -= 18 if norm(row["antibiotic"]) in patient.get("resistant", []) and patient.get("resistant_mode") == "strict" else 45 if norm(row["antibiotic"]) in patient.get("resistant", []) else 0
    fit += 8 if patient.get("wants_mdr") and as_num(row["mdr_relevant"]) > 0 else 0
    fit += 10 if patient.get("wants_xdr") and as_num(row["xdr_relevant"]) > 0 else 0
    fit += as_num(row["phage_active"]) * 8 + as_num(row["antibiotic_active"]) * 7 + as_num(row["direct_isolate_match"]) * 12 + as_num(row["species_match"]) * 6
    effect = as_num(row["synergy_score"]) * 0.3 + min(as_num(row["mic_fold_reduction"]), 16) * 2.2 + min(as_num(row["log_reduction"]), 6) * 4.5
    evidence_component = as_num(row["evidence_level"]) * 8 + as_num(row["quality_score"]) * 5 + min(as_num(row["n_strains_tested"]), 40) * 0.7
    cocktail_component = min(as_num(row["phage_cocktail_size"]), 6) * 1.5 + min(as_num(row["host_range_score"]), 10) * 1.8
    penalty = as_num(row["toxicity_signal"]) * 8 + max(0, 60 - confidence_score(row)) * 0.35
    return round(evidence_component * 0.26 + effect * 0.28 + fit * 0.30 + cocktail_component * 0.08 + confidence_score(row) * 0.08 - penalty, 2)

def explain_row(row: pd.Series) -> str:
    parts: List[str] = []
    if row.get("relevance_score", 0) >= 30: parts.append("хорошее совпадение с текущим контекстом")
    if row.get("effect_score", 0) >= 30: parts.append("сильный эффект комбинации")
    elif row.get("effect_score", 0) >= 18: parts.append("умеренный эффект комбинации")
    if row.get("evidence_score", 0) >= 18: parts.append("приличная доказательная база")
    if row.get("penalty_score", 0) >= 12: parts.append("есть штрафы за слабые места")
    return "; ".join(parts) if parts else "сигнал смешанный и требует осторожности"

def ranking_df(patient: Dict) -> pd.DataFrame:
    df = ranking_base_df()
    if df.empty: return df
    df["synergy_prediction"] = df.apply(lambda row: classify_synergy(row["synergy_type"], as_num(row["synergy_score"]), as_num(row["mic_fold_reduction"]), as_num(row["log_reduction"])), axis=1)
    df["confidence_score"] = df.apply(confidence_score, axis=1)
    flags = df.apply(lambda r: validation_flags(r["interpretation_id"]), axis=1)
    df["critical_flags"] = flags.apply(lambda item: " | ".join(item["critical"]))
    df["warning_flags"] = flags.apply(lambda item: " | ".join(item["warnings"]))
    eligibility = df.apply(lambda row: ranking_eligibility(row, patient), axis=1)
    df["eligible_for_ranking"] = eligibility.apply(lambda item: item[0])
    df["exclusion_reason"] = eligibility.apply(lambda item: item[1])
    
    def calc_relevance(row):
        score = 0.0
        score += 20 if norm(row["pathogen"]) == norm(patient.get("pathogen", "")) else 0
        score += 10 if patient.get("growth_mode") != "Любой" and norm(row["growth_state"]) == norm(patient.get("growth_mode", "")) else 0
        score += 12 if norm(row["antibiotic"]) in patient.get("sensitive", []) else 0
        score -= 18 if norm(row["antibiotic"]) in patient.get("resistant", []) else 0
        score += 8 if patient.get("wants_mdr") and as_num(row["mdr_relevant"]) > 0 else 0
        score += 10 if patient.get("wants_xdr") and as_num(row["xdr_relevant"]) > 0 else 0
        score += as_num(row["phage_active"]) * 8 + as_num(row["antibiotic_active"]) * 7 + as_num(row["direct_isolate_match"]) * 12 + as_num(row["species_match"]) * 6
        return max(0.0, score)
    
    df["relevance_score"] = df.apply(calc_relevance, axis=1)
    df["effect_score"] = df.apply(lambda row: round(as_num(row["synergy_score"]) * 0.3 + min(as_num(row["mic_fold_reduction"]), 16) * 2.2 + min(as_num(row["log_reduction"]), 6) * 4.5, 2), axis=1)
    df["evidence_score"] = df.apply(lambda row: round(as_num(row["evidence_level"]) * 8 + as_num(row["quality_score"]) * 5 + min(as_num(row["n_strains_tested"]), 40) * 0.7, 2), axis=1)
    df["penalty_score"] = df.apply(lambda row: round(as_num(row["toxicity_signal"]) * 8 + max(0, 60 - as_num(row["confidence_score"])) * 0.35, 2), axis=1)
    df["resistant_override"] = df.apply(lambda row: patient.get("resistant_mode") == "soft" and norm(row["antibiotic"]) in patient.get("resistant", []), axis=1)
    df["final_score"] = df.apply(lambda row: score_row(row, patient), axis=1)
    df["why_it_ranked"] = df.apply(explain_row, axis=1)
    
    if patient.get("exclude_antagonism"):
        df = df[df["synergy_prediction"] != "antagonism"]
    if patient.get("only_active_pairs"):
        df = df[(df["phage_active"] > 0) & (df["antibiotic_active"] > 0)]
    if patient.get("only_validated"):
        df = df[df["eligible_for_ranking"]]
    return df.sort_values(["eligible_for_ranking", "resistant_override", "final_score"], ascending=[False, True, False])

def audit_df() -> pd.DataFrame:
    df = ranking_base_df()
    if df.empty: return df
    df["confidence_score"] = df.apply(confidence_score, axis=1)
    flags = df.apply(lambda r: validation_flags(r["interpretation_id"]), axis=1)
    df["critical_flags"] = flags.apply(lambda item: " | ".join(item["critical"]))
    df["warning_flags"] = flags.apply(lambda item: " | ".join(item["warnings"]))
    return df[["interpretation_id", "record_status", "reference", "pathogen", "phage", "antibiotic", "confidence_score", "evidence_level", "quality_score", "synergy_score", "critical_flags", "warning_flags"]].sort_values(["record_status", "confidence_score"], ascending=[True, True])

def consensus_df() -> pd.DataFrame:
    df = ranking_base_df()
    if df.empty: return df
    df["confidence_score"] = df.apply(confidence_score, axis=1)
    return df.groupby(["pathogen", "phage", "antibiotic", "growth_state"], dropna=False).agg(
        supporting_articles=("reference", "nunique"),
        mean_synergy_score=("synergy_score", "mean"),
        mean_confidence_score=("confidence_score", "mean"),
        max_evidence=("evidence_level", "max")
    ).reset_index().sort_values(["mean_confidence_score", "mean_synergy_score"], ascending=False)

# --- Import & Migration ---
def migrate_from_previous_db(path: Path) -> Dict[str, int]:
    source = sqlite3.connect(path)
    source.row_factory = sqlite3.Row
    try:
        has_outcomes = bool(source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='outcomes'").fetchone())
        for row in source.execute("SELECT * FROM articles ORDER BY id"):
            create_article(row["reference"], int(row["year"] or 0), row["doi"], row["study_type"], row.get("notes", ""))
        for row in source.execute("SELECT * FROM experiments ORDER BY id"):
            create_experiment(row["article_id"], row["pathogen"], row["strain"], row["sample_source"], row["growth_state"], row["infection_model"], int(row["biofilm"]), as_num(row["n_strains_tested"]), int(row["replicated"]), int(row["direct_isolate_match"]), int(row["species_match"]), int(row["mdr_relevant"]), int(row["xdr_relevant"]))
        for row in source.execute("SELECT * FROM therapies ORDER BY id"):
            cocktail = row.get("cocktail_size", row.get("phage_cocktail_size", 0))
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
        rows.append({
            "row": int(idx) + 2,
            "reference": payload["reference"],
            "pathogen": payload["pathogen"],
            "phage": payload["phage"],
            "antibiotic": payload["antibiotic"],
            "status": "ok" if not any(item["is_blocking"] for item in issues) else "error",
            "issues": " | ".join(item["issue_message"] for item in issues)
        })
    return pd.DataFrame(rows)

def import_legacy_csv(file_path: str) -> Dict[str, int]:
    df = pd.read_csv(file_path)
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
    return {
        "articles": table_count("articles"),
        "experiments": table_count("experiments"),
        "therapies": table_count("therapies"),
        "measurements": table_count("effect_measurements"),
        "interpretations": table_count("outcome_interpretations")
    }

def previous_db() -> Path | None:
    for path in PREV_DBS:
        if path.exists():
            return path
    return None

def is_empty() -> bool:
    try:
        return table_count("articles") == 0
    except Exception:
        return True
