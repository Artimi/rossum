import os.path

from flask import Flask, request, send_from_directory

import rossum.utils


app = Flask(__name__)

DATA_DIR = 'data/'


@app.route("/v1/post", methods=['POST'])
def post():
    if len(request.files) > 1:
        return 'More than one file uploaded', 400
    if not request.files:
        return 'No file uploaded', 400
    file = next(request.files.values())
    task_id = rossum.utils.hash_file(file)
    file.save(os.path.join(DATA_DIR, f'{task_id}.pdf'))
    # TODO start the asynchronous task
    return {
        'task_id': task_id
    }

@app.route("/v1/info/<task_id>")
def info(task_id: str):
    # TODO retrieve state of the task
    return {
        'task_id': task_id,
        'status': 'unknown',
        'pages': 0,
    }

@app.route("/v1/get/<task_id>/<int:page>")
def get(task_id: str, page: int):
    return send_from_directory(DATA_DIR, task_id, f'{page}.png')

