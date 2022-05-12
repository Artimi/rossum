import os.path

from flasgger import Swagger
from flask import Flask, request, send_from_directory
from flask.typing import ResponseReturnValue
import werkzeug.security

import rossum.utils
import rossum.pdf


app = Flask(__name__)
swagger = Swagger(app)
app.config.from_object("rossum.settings")


@app.route("/v1/post", methods=["POST"])
def post() -> ResponseReturnValue:
    """
    Endpoint serving to post PDF.
    ---
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: upfile
        type: file
        description: The file to upload.
    definitions:
      PostResponse:
        type: object
        properties:
          document_id:
            type: string
    responses:
      200:
        description: Document id assigned to the given document
        schema:
          $ref: '#/definitions/PostResponse'
      400:
        description: Uploaded document is not correct or missing
    """
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
    """
    Info about document status
    ---
    parameters:
      - name: document_id
        in: path
        type: string
        required: true
    definitions:
      InfoResponse:
        type: object
        properties:
          document_id:
            type: string
          status:
            type: string
            enum: ["in_progress", "done"]
          pages:
            type: integer
    responses:
      200:
        description: Info about the document
        schema:
          $ref: '#/definitions/InfoResponse'
      404:
        description: Document with given id was not posted
    """
    document_dir_path = werkzeug.security.safe_join(app.config["DATA_DIR"], document_id)
    document_path = werkzeug.security.safe_join(
        app.config["DATA_DIR"], f"{document_id}.pdf"
    )
    if not os.path.exists(document_path):
        return f"Document with id = {document_id} was not found", 404

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
    """
    Get page from the processed document
    ---
    parameters:
      - name: document_id
        in: path
        type: string
        required: true
      - name: page
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Normalized PNG page of the document
        content:
          image/png:
            schema:
              type: string
              format: binary
      404:
        description: Document with given id and page cannot be found
    """
    return send_from_directory(
        werkzeug.security.safe_join(app.config["DATA_DIR"], document_id), f"{page}.png"
    )
