from sqlalchemy import inspect, create_engine
from app.database import init_db


def test_database_table_creation():
    """
    Verify all 4 required tables are created during database initialization:
    - farmer_activity_logs
    - weather_cache
    - pest_disease_history
    - extension_directory
    """
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    init_db(target_engine=test_engine)

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    required_tables = [
        "farmer_activity_logs",
        "weather_cache",
        "pest_disease_history",
        "extension_directory",
    ]

    for table in required_tables:
        assert table in tables, f"Expected table '{table}' to be created, but found: {tables}"
