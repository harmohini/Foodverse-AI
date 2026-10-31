"""Test configuration — isolated temporary test database and demo settings."""
import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.database.connection import Base, get_db
from app.main import app

# Ensure tests run in demo mode by default
settings.ai_provider = "demo"
settings.gemini_api_key = ""
settings.openai_api_key = ""


@pytest.fixture(autouse=True, scope="session")
def setup_test_environment():
    """Create isolated test database and override get_db dependency for tests."""
    settings.ai_provider = "demo"
    settings.gemini_api_key = ""
    settings.openai_api_key = ""

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        test_db_path = tf.name

    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(test_db_path):
        try:
            os.unlink(test_db_path)
        except OSError:
            pass
