"""
Database Layer for Mkulima Gemma
Provides SQLAlchemy ORM session management and schema initialization,
plus SQLite raw connection utilities for backward compatibility.
"""

import os
import sqlite3
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Base directory for the database file
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "mkulima.db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Create SQLAlchemy engine with sqlite check_same_thread set to False
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy database session.
    Ensures session is closed after request completes.
    """
    try:
        from app.main import DB_PATH
        target_path = str(DB_PATH)
    except Exception:
        target_path = str(DB_PATH)

    current_url = str(engine.url)
    if target_path and not current_url.endswith(target_path):
        target_engine = create_engine(f"sqlite:///{target_path}", connect_args={"check_same_thread": False})
        db = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)()
    else:
        db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None, db_path: Optional[str] = None) -> None:
    """
    Initialize database schema by creating all tables defined in ORM models.
    """
    if isinstance(target_engine, str):
        db_path = target_engine
        target_engine = None

    # Import all models to ensure they are registered with Base.metadata
    from app.models import FarmerActivityLog, WeatherCache, PestDiseaseHistory, ExtensionDirectory  # noqa: F401

    if db_path:
        eng = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    else:
        eng = target_engine or engine

    Base.metadata.create_all(bind=eng)

    conn = None
    if db_path:
        conn = get_db_connection(db_path)
    else:
        try:
            conn = eng.raw_connection()
        except Exception:
            pass

    if conn:
        try:
            _ensure_all_columns(conn)
        finally:
            try:
                conn.close()
            except Exception:
                pass


def _ensure_all_columns(conn) -> None:
    cursor = conn.cursor()

    # 1. farmer_activity_logs
    cursor.execute("PRAGMA table_info(farmer_activity_logs)")
    cols = {row[1] for row in cursor.fetchall()}
    if cols:
        if "farmer_id" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN farmer_id TEXT NOT NULL DEFAULT 'default_farmer'")
        if "farmer_name" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN farmer_name TEXT")
        if "activity_type" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN activity_type TEXT")
        if "crop_type" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN crop_type TEXT")
        if "description" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN description TEXT")
        if "details" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN details TEXT")
        if "quantity" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN quantity REAL")
        if "unit" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN unit TEXT")
        if "field_location" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN field_location TEXT")
        if "notes" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN notes TEXT")
        if "logged_at" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN logged_at TEXT")
        if "created_at" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN created_at TEXT")
        if "timestamp" not in cols:
            cursor.execute("ALTER TABLE farmer_activity_logs ADD COLUMN timestamp TEXT")

    # 2. weather_cache
    cursor.execute("PRAGMA table_info(weather_cache)")
    cols = {row[1] for row in cursor.fetchall()}
    if cols:
        if "location_name" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN location_name TEXT")
        if "location" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN location TEXT")
        if "latitude" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN latitude REAL")
        if "longitude" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN longitude REAL")
        if "forecast_date" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN forecast_date TEXT")
        if "temp_min_c" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN temp_min_c REAL")
        if "temp_max_c" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN temp_max_c REAL")
        if "temperature" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN temperature REAL")
        if "humidity" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN humidity REAL")
        if "humidity_pct" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN humidity_pct INTEGER")
        if "precipitation" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN precipitation REAL")
        if "precipitation_mm" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN precipitation_mm REAL")
        if "wind_speed_kmh" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN wind_speed_kmh REAL")
        if "forecast" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN forecast TEXT")
        if "condition_text" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN condition_text TEXT")
        if "is_synced" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN is_synced INTEGER DEFAULT 1")
        if "fetched_at" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN fetched_at TEXT")
        if "cached_at" not in cols:
            cursor.execute("ALTER TABLE weather_cache ADD COLUMN cached_at TEXT")

    # 3. pest_disease_history
    cursor.execute("PRAGMA table_info(pest_disease_history)")
    cols = {row[1] for row in cursor.fetchall()}
    if cols:
        if "farmer_id" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN farmer_id TEXT NOT NULL DEFAULT 'default_farmer'")
        if "crop_type" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN crop_type TEXT")
        if "crop_name" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN crop_name TEXT")
        if "issue_type" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN issue_type TEXT")
        if "issue_name" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN issue_name TEXT")
        if "severity" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN severity TEXT DEFAULT 'MEDIUM'")
        if "image_path" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN image_path TEXT")
        if "symptoms_description" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN symptoms_description TEXT")
        if "description" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN description TEXT")
        if "ai_diagnosis_summary" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN ai_diagnosis_summary TEXT")
        if "recommended_treatment" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN recommended_treatment TEXT")
        if "treatment" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN treatment TEXT")
        if "chemical_safety_warning" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN chemical_safety_warning TEXT")
        if "status" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN status TEXT DEFAULT 'ACTIVE'")
        if "detected_at" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN detected_at TEXT")
        if "logged_at" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN logged_at TEXT")
        if "created_at" not in cols:
            cursor.execute("ALTER TABLE pest_disease_history ADD COLUMN created_at TEXT")

    # 4. extension_directory
    cursor.execute("PRAGMA table_info(extension_directory)")
    cols = {row[1] for row in cursor.fetchall()}
    if cols:
        if "name" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN name TEXT")
        if "provider_name" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN provider_name TEXT")
        if "role_or_type" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN role_or_type TEXT")
        if "organization" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN organization TEXT")
        if "county_region" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN county_region TEXT")
        if "region" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN region TEXT")
        if "sub_county_ward" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN sub_county_ward TEXT")
        if "phone_number" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN phone_number TEXT")
        if "contact_info" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN contact_info TEXT")
        if "email" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN email TEXT")
        if "services_offered" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN services_offered TEXT")
        if "is_verified" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN is_verified INTEGER DEFAULT 1")
        if "created_at" not in cols:
            cursor.execute("ALTER TABLE extension_directory ADD COLUMN created_at TEXT")

    try:
        conn.commit()
    except Exception:
        pass


# --- Raw SQLite Utilities for Backward Compatibility ---

DEFAULT_DB_PATH = str(DB_PATH)


def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Establish and return a SQLite database connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def add_activity(
    farmer_name: str,
    activity_type: str,
    crop_name: str,
    details: str,
    timestamp: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO farmer_activity_logs (
            farmer_id, farmer_name, activity_type, crop_type, description, details, logged_at, timestamp, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (farmer_name, farmer_name, activity_type, crop_name, details, details, timestamp, timestamp, now_str)
    )
    activity_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": activity_id,
        "farmer_name": farmer_name,
        "activity_type": activity_type,
        "crop_name": crop_name,
        "details": details,
        "timestamp": timestamp
    }


def get_activities(
    farmer_name: Optional[str] = None,
    limit: int = 50,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if farmer_name:
        cursor.execute(
            """
            SELECT * FROM farmer_activity_logs
            WHERE farmer_name = ? OR farmer_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (farmer_name, farmer_name, limit)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM farmer_activity_logs
            ORDER BY id DESC LIMIT ?
            """,
            (limit,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_pest_record(
    crop_name: str,
    issue_name: str,
    description: Optional[str] = "",
    treatment: Optional[str] = "",
    logged_at: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    if not logged_at:
        logged_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO pest_disease_history (
            farmer_id, crop_type, crop_name, issue_type, issue_name, severity, symptoms_description, description, recommended_treatment, treatment, detected_at, logged_at, status, created_at
        )
        VALUES ('default_farmer', ?, ?, 'PEST', ?, 'MEDIUM', ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
        """,
        (crop_name, crop_name, issue_name, description or "", description or "", treatment or "", treatment or "", logged_at, logged_at, now_str)
    )
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": record_id,
        "crop_name": crop_name,
        "issue_name": issue_name,
        "description": description,
        "treatment": treatment,
        "logged_at": logged_at
    }


def get_pest_records(
    crop_name: Optional[str] = None,
    limit: int = 50,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if crop_name:
        cursor.execute(
            """
            SELECT * FROM pest_disease_history
            WHERE crop_name = ? OR crop_type = ?
            ORDER BY id DESC LIMIT ?
            """,
            (crop_name, crop_name, limit)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM pest_disease_history
            ORDER BY id DESC LIMIT ?
            """,
            (limit,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_extension_service(
    provider_name: str,
    region: str,
    contact_info: str,
    services_offered: str,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO extension_directory (
            name, provider_name, role_or_type, county_region, region, phone_number, contact_info, services_offered, is_verified, created_at
        )
        VALUES (?, ?, 'Extension Officer', ?, ?, ?, ?, ?, 1, ?)
        """,
        (provider_name, provider_name, region, region, contact_info, contact_info, services_offered, now_str)
    )
    provider_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": provider_id,
        "provider_name": provider_name,
        "region": region,
        "contact_info": contact_info,
        "services_offered": services_offered
    }


def get_extension_services(
    region: Optional[str] = None,
    limit: int = 50,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if region:
        cursor.execute(
            """
            SELECT * FROM extension_directory
            WHERE region = ? OR county_region = ?
            ORDER BY id DESC LIMIT ?
            """,
            (region, region, limit)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM extension_directory
            ORDER BY id DESC LIMIT ?
            """,
            (limit,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_extension_services(
    region: Optional[str] = None,
    limit: int = 50,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if region:
        cursor.execute(
            """
            SELECT * FROM extension_directory
            WHERE region LIKE ? OR county_region LIKE ?
            ORDER BY id DESC LIMIT ?
            """,
            (f"%{region}%", f"%{region}%", limit)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM extension_directory
            ORDER BY id DESC LIMIT ?
            """,
            (limit,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def upsert_weather_cache(
    location: str,
    temperature: float,
    humidity: float,
    precipitation: float,
    forecast: str,
    cached_at: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    if not cached_at:
        cached_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    today_date = cached_at[:10]
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weather_cache WHERE location = ? OR location_name = ?", (location, location))
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE weather_cache
            SET location_name = ?, location = ?, forecast_date = ?, temp_min_c = ?, temp_max_c = ?,
                temperature = ?, humidity = ?, humidity_pct = ?, precipitation = ?, precipitation_mm = ?,
                forecast = ?, condition_text = ?, cached_at = ?, fetched_at = ?, is_synced = 1
            WHERE id = ?
            """,
            (
                location, location, today_date, temperature, temperature,
                temperature, humidity, int(humidity), precipitation, precipitation,
                forecast, forecast, cached_at, now_str, existing["id"]
            )
        )
    else:
        cursor.execute(
            """
            INSERT INTO weather_cache (
                location_name, location, forecast_date, temp_min_c, temp_max_c, temperature,
                humidity, humidity_pct, precipitation, precipitation_mm, forecast, condition_text, cached_at, fetched_at, is_synced
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                location, location, today_date, temperature, temperature, temperature,
                humidity, int(humidity), precipitation, precipitation, forecast, forecast, cached_at, now_str
            )
        )
    conn.commit()

    cursor.execute("SELECT * FROM weather_cache WHERE location = ? OR location_name = ?", (location, location))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else {
        "location": location,
        "temperature": temperature,
        "humidity": humidity,
        "precipitation": precipitation,
        "forecast": forecast,
        "cached_at": cached_at
    }


def get_weather_cache(
    location: str = "Nairobi",
    db_path: str = DEFAULT_DB_PATH
) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM weather_cache WHERE location = ? OR location_name = ?", (location, location))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
