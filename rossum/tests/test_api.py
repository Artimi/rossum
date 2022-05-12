import pathlib

import dramatiq
import flask
import flask.testing
import pytest

import rossum.api
import rossum.utils
import rossum.pdf

TEST_FILE = pathlib.Path(__file__).parent / "resources" / "PDF_rendering_app.pdf"
with open(TEST_FILE, "rb") as f:
    TEST_DOCUMENT_ID = rossum.utils.hash_file(f)


@pytest.fixture()
def app(tmp_path: pathlib.Path) -> flask.Flask:
    app = rossum.api.app
    app.config.update(
        {
            "TESTING": True,
            "DATA_DIR": str(tmp_path),
        }
    )

    yield app


@pytest.fixture()
def client(app: flask.Flask) -> flask.testing.FlaskClient:
    return app.test_client()


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


def test_info_missing(client: flask.testing.FlaskClient) -> None:
    response = client.get("/v1/info/abc")
    assert response.status_code == 404


def test_post(client: flask.testing.FlaskClient) -> None:
    response = client.post("/v1/post", data={"pdf": TEST_FILE.open("rb")})
    assert response.status_code == 200
    assert response.json == {
        "document_id": TEST_DOCUMENT_ID,
    }
    assert response.content_type == "application/json"


def test_post_multiple_files(client: flask.testing.FlaskClient) -> None:
    response = client.post(
        "/v1/post", data={"pdf": TEST_FILE.open("rb"), "pdf2": TEST_FILE.open("rb")}
    )
    assert response.status_code == 400


def test_post_missing_file(client: flask.testing.FlaskClient) -> None:
    response = client.post("/v1/post")
    assert response.status_code == 400


def test_get_missing(client: flask.testing.FlaskClient) -> None:
    response = client.get(f"/v1/get/MISSING/5")
    assert response.status_code == 404


def test_end_to_end(client: flask.testing.FlaskClient, stub_broker: dramatiq.Broker, stub_worker: dramatiq.Worker) -> None:
    response = client.post("/v1/post", data={"pdf": TEST_FILE.open("rb")})
    assert response.status_code == 200
    assert response.json == {
        "document_id": TEST_DOCUMENT_ID,
    }
    assert response.content_type == "application/json"
    stub_broker.join(rossum.pdf.pdf_to_png.queue_name)
    stub_worker.join()

    response = client.get(f"/v1/info/{TEST_DOCUMENT_ID}")
    assert response.status_code == 200
    assert response.json == {
        "document_id": TEST_DOCUMENT_ID,
        "pages": 2,
        "status": "done",
    }
    assert response.content_type == "application/json"

    response = client.get(f"/v1/get/{TEST_DOCUMENT_ID}/1")
    assert response.status_code == 200
    assert response.data[:4] == b"\x89PNG"
    assert response.content_type == "image/png"

    response = client.get(f"/v1/get/{TEST_DOCUMENT_ID}/2")
    assert response.status_code == 200
    assert response.data[:4] == b"\x89PNG"
    assert response.content_type == "image/png"
