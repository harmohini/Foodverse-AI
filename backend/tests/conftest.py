"""Test configuration — ensure DB tables exist before tests."""
import pytest
from app.database.connection import init_db


@pytest.fixture(autouse=True, scope="session")
def setup_database():
    """Initialize the test database before all tests."""
    init_db()
