import pathlib
import shutil
import os

import dramatiq
import pytest

import rossum.utils
import rossum.pdf


TEST_FILE = pathlib.Path(__file__).parent / "resources" / "PDF_rendering_app.pdf"
with open(TEST_FILE, "rb") as f:
    TEST_DOCUMENT_ID = rossum.utils.hash_file(f)
MAX_SIZE = (1200, 1600)


@pytest.fixture()
def stub_broker() -> dramatiq.Broker:
    rossum.pdf.broker.flush_all()
    return rossum.pdf.broker


@pytest.fixture()
def stub_worker() -> dramatiq.Worker:
    worker = dramatiq.Worker(rossum.pdf.broker, worker_timeout=10)
    worker.start()
    yield worker
    worker.stop()


@pytest.fixture
def document_path(tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / f"{TEST_DOCUMENT_ID}.pdf"
    shutil.copyfile(TEST_FILE, path)
    return path


def test_pdf_to_png(
    tmp_path: pathlib.Path,
    document_path: pathlib.Path,
    stub_broker: dramatiq.Broker,
    stub_worker: dramatiq.Worker,
) -> None:
    rossum.pdf.pdf_to_png.send(
        str(document_path), TEST_DOCUMENT_ID, str(tmp_path), MAX_SIZE
    )
    stub_broker.join(rossum.pdf.pdf_to_png.queue_name)
    stub_worker.join()
    assert os.path.exists(tmp_path / TEST_DOCUMENT_ID)
    assert os.path.exists(tmp_path / TEST_DOCUMENT_ID / "1.png")
    assert os.path.exists(tmp_path / TEST_DOCUMENT_ID / "2.png")


def test_pdf_info(document_path: pathlib.Path) -> None:
    pdf_info = rossum.pdf.pdf_info(str(document_path))
    assert pdf_info["Pages"] == 2
