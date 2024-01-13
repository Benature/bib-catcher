import json
import os

from flask import Flask, Response, request, url_for

from converter import Converter, touch_note
import requests

app = Flask(__name__)

HOST = "127.0.0.1"
PORT = 7070

converter = Converter()


@app.route("/obsidian", methods=['POST', 'GET'])
def note_convert():
    req = request.get_json()

    _, filename = os.path.split(req['path'])
    citekey, _ = os.path.splitext(filename)

    converter.load_paper(citekey)
    text = converter.convert_note(req['text'])
    detect_citekey_num = len(converter.citekey_to_touch)
    converter.touch_notes()
    # new_notes = converter.touch_notes()

    notification = f"BIB-CATCHER 🫳\n"
    if detect_citekey_num > 0:
        notification += f"😮 Detect {detect_citekey_num} papers."
        # if len(new_notes) > 0:
        #     notification += f"\n🆕 Create {len(new_notes)} new notes: {', '.join(new_notes)}"
    else:
        notification += "🙅‍♂️ No paper detected."

    data = {}
    if text != req['text']:
        data.update({"text": text})
    data.update({"notification": notification})
    return Response(json.dumps(data), mimetype='application/json')


@app.route("/touch", methods=['POST', 'GET'])
def touch_md():
    req = request.get_json()
    citekey = req['citekey']
    touch_note(citekey)
    return Response(json.dumps(dict(status=200)))


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
