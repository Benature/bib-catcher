# %%
import re
import pandas as pd
import os
import argparse
from gscholar import query
import bibtexparser
import pyperclip as pc
import json

from utils import *
from obsidian import write_note

# %%

parser = argparse.ArgumentParser()
parser.add_argument('citekey', type=str, default="")
args = parser.parse_args()

CITEKEY = args.citekey.lstrip('@')

# %%

df = pd.read_csv(os.path.join('output', CITEKEY, 'title.csv'))

if os.path.exists(zotero_bib_path):
    with open(zotero_bib_path, "r") as f:
        zdf = pd.DataFrame(bibtexparser.load(f).entries)
else:
    zdf = None

ob_config_path = os.path.join(obsidian_bse_path, ob_citation_plugin_path)
if os.path.exists(ob_config_path):
    with open(ob_config_path, 'r') as f:
        ob_template = json.loads(f.read())['literatureNoteContentTemplate']
else:
    ob_template = None

citekey_to_touch = []


def touch_note(citekey):
    # print("touch", citekey)
    if ob_template is None:
        print("no template")
        return
    note_path = os.path.join(obsidian_bse_path, ob_note_path, f"@{citekey}.md")
    # print(note_path)
    if os.path.exists(note_path):
        print("Note exists:", citekey)
        return
    md = write_note(citekey, ob_template, zdf)
    if md == "":
        return
    print("Write new note:", citekey)
    with open(note_path, 'w') as f:
        f.write(md)


def idx2citekey(r):
    content = ""
    idxs = r.group(2).strip('[]').split(',')
    for idx in idxs:
        cdf = df[df.cidx == int(idx)]
        if content != "":  # not the first one
            content += ", "

        if len(cdf) == 0:
            content += idx
        else:
            citekey = cdf.citekey.tolist()[0]
            content += f"[[{citekey}]]"
            citekey_to_touch.append(citekey)
            # touch_note(citekey)

    if len(idxs) == 1 and zdf is not None:
        bdf = zdf[zdf.ID == citekey]
        if len(bdf) != 0:
            if pd.notna(bdf.shorttitle.tolist()[0]):
                shorttitle = re.sub('[{}]', '', bdf.shorttitle.tolist()[0])
                if is_same_item(shorttitle, r.group(1)):
                    return f"[[{citekey}|{shorttitle}]]"

    return r.group(1) + " (" + content + ")"


# %%
if __name__ == '__main__':
    while True:
        text = input("Input text:\n")
        print()
        output = re.sub(r'([\w\.]+) (\[[\d,]+\])', idx2citekey, text)
        pc.copy(output)
        print()
        print(output)
        print()
        print("The content has been replaced in the clipboard!")
        print()
        for ck in citekey_to_touch:
            touch_note(ck)
        citekey_to_touch = []
        print("="*30)
