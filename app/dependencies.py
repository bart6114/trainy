"""Dependencies for FastAPI routes."""

from typing import Generator

from trainy.config import settings
from trainy.database import Repository


def get_repo() -> Generator[Repository, None, None]:
    """Dependency that provides a repository instance."""
    repo = Repository(settings.database_path)
    try:
        yield repo
    finally:
        repo.close()
