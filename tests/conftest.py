import pytest

from app import config
from app.pipeline.ingest import load_pdf


@pytest.fixture(scope="session")
def halaman_demo():
    """Halaman PDF modul demo, dibaca sekali untuk semua pengujian."""
    return load_pdf(config.MODULE_DIR / "modul_demo.pdf")