import os
import tempfile
import shutil
import pytest
import pexpect
import pexpect.popen_spawn  # <-- Import the Windows sub-module
from schema import create_database
from daycare import add_client

@pytest.fixture(scope="function")
def test_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_daycare.db")
    os.environ["DATABASE_PATH"] = db_path
    
    create_database()

    yield

    shutil.rmtree(temp_dir)
    os.environ.pop("DATABASE_PATH", None)

@pytest.fixture(scope="function")
def spawn_app(test_db):
    """Spawns the CLI application as a sub-process for testing on Windows."""
    child_processes = []

    def _spawn():
        # Use python -u to force unbuffered output so pexpect reads it instantly
        cmd = ["python", "-u", "app.py"] 

        current_env = os.environ.copy()
        
        # Change pexpect.spawn to pexpect.popen_spawn.PopenSpawn
        child = pexpect.popen_spawn.PopenSpawn(cmd, encoding="utf-8", timeout=3, env=current_env)
        child_processes.append(child)
        return child

    yield _spawn

    # Clean up the processes on teardown
    for child in child_processes:
        try:
            if child.proc.poll() is None:  # Check if Windows process is still running
                child.proc.kill()
        except Exception:
            pass

@pytest.fixture(scope="function")
def existing_client(test_db):
    new_client_id = add_client("Jon Wolfe", phone="614-555-0123", email="jonwolfe@example.com")
    return new_client_id