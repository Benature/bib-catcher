import json
import os

from flask import Flask, Response, request

from converter import Converter

app = Flask(__name__)

converter = Converter()


@app.route("/obsidian", methods=['POST', 'GET'])
def note_convert():
    req = request.get_json()

    _, filename = os.path.split(req['path'])
    citekey, _ = os.path.splitext(filename)

    converter.load_paper(citekey)
    text = converter.convert_note(req['text'])

    if text == req['text']:
        data = {"replace": False}
    else:
        data = {"text": text, "replace": True}
    return Response(json.dumps(data), mimetype='application/json')


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7070, debug=True)