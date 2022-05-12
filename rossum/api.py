import os.path

from flask import Flask, request, send_from_directory
from flask.typing import ResponseReturnValue
import werkzeug.security

import rossum.utils
import rossum.pdf


app = Flask(__name__)
app.config.from_object("rossum.settings")


@app.route("/v1/post", methods=["POST"])
def post() -> ResponseReturnValue:
    if len(request.files) > 1:
        return "More than one file uploaded", 400
    if not request.files:
        return "No file uploaded", 400
    file = next(request.files.values())
    document_id = rossum.utils.hash_file(file)
    document_path = os.path.join(app.config["DATA_DIR"], f"{document_id}.pdf")
    file.save(document_path)
    rossum.pdf.pdf_to_png.send(
        document_path, document_id, app.config["DATA_DIR"], app.config["IMAGE_SIZE"]
    )
    return {"document_id": document_id}


@app.route("/v1/info/<document_id>")
def info(document_id: str) -> ResponseReturnValue:
    document_dir_path = werkzeug.security.safe_join(app.config["DATA_DIR"], document_id)
    document_path = werkzeug.security.safe_join(
        app.config["DATA_DIR"], f"{document_id}.pdf"
    )
    if not os.path.exists(document_path):
        return f"Document with id = {document_id} not found", 404

    if os.path.exists(document_dir_path):
        status = "done"
    else:
        status = "in_progress"

    pages = rossum.pdf.pdf_info(document_path)["Pages"]

    return {
        "document_id": document_id,
        "status": status,
        "pages": pages,
    }


@app.route("/v1/get/<document_id>/<int:page>")
def get(document_id: str, page: int) -> ResponseReturnValue:
    return send_from_directory(
        werkzeug.security.safe_join(app.config["DATA_DIR"], document_id), f"{page}.png"
    )
