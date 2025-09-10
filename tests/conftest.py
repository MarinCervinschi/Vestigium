import pytest
import tempfile
import os
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def clean_env():
    """Provide a clean environment for tests."""
    original_dir = os.getcwd()
    yield
    os.chdir(original_dir)
