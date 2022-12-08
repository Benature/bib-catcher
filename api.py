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

    detect_citekey_num = len(converter.citekey_to_touch)
    new_notes = converter.touch_notes()

    notification = f"BIB-CATCHER 🫳\n"
    if detect_citekey_num > 0:
        notification += f"😮 Detect {detect_citekey_num} papers."
        if len(new_notes) > 0:
            notification += f"\n🆕 Create {len(new_notes)} new notes: {', '.join(new_notes)}"
    else:
        notification += "🙅‍♂️ No paper detected."

    data = {}
    if text != req['text']:
        data.update({"text": text})
    data.update({"notification": notification})
    return Response(json.dumps(data), mimetype='application/json')


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7070, debug=True)