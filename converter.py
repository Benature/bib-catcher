# %%
import re
import pandas as pd
import os
import argparse
from gscholar import query
import bibtexparser
import pyperclip as pc
import json
from math import floor
from collections import defaultdict

from utils.util import *
from utils.obsidian import write_note

from functools import partial

import urllib.parse

# %%

parser = argparse.ArgumentParser()
parser.add_argument('citekey', type=str, default="", nargs='?')
args = parser.parse_args()

# %%
print("Loading Zotero database...")
if os.path.exists(zotero_bib_path):
    with open(zotero_bib_path, "r") as f:
        zdf = pd.DataFrame(bibtexparser.load(f).entries)
else:
    zdf = None

print("Loading Citation plugin configuration...")
ob_config_path = os.path.join(obsidian_bse_path, ob_citation_plugin_path)
if os.path.exists(ob_config_path):
    with open(ob_config_path, 'r') as f:
        ob_template = json.loads(f.read())['literatureNoteContentTemplate']
else:
    ob_template = None


def touch_note(citekey):
    # print("touch", citekey)
    if ob_template is None:
        cprint("no template", 31)
        return False
    note_path = os.path.join(obsidian_bse_path, ob_note_path, f"@{citekey}.md")
    # print(note_path)
    if os.path.exists(note_path):
        cprint(f"[INFO] Note exists: {citekey}")
        return False
    md = write_note(citekey, ob_template, zdf)
    if md == "":
        return False
    cprint(f"[INFO] Write new note: {citekey}", c=33)
    with open(note_path, 'w') as f:
        f.write(md)
    return True


class Converter():

    def __init__(self):
        self.dfs = {}
        self.load_success = False
        self.citekey_to_touch = set()
        # self.citekey_to_touch = defaultdict(list)

    def load_paper(self, paper):
        '''paper CITEKEY'''
        paper = paper.lstrip('@')
        if paper not in self.dfs:
            paper_path = os.path.join(root_dir, 'output', paper, 'title.csv')
            if os.path.exists(paper_path):
                self.dfs[paper] = pd.read_csv(paper_path)
            else:
                print(f"Unknown paper: {paper}")
                self.load_success = False
                return False
        self.df = self.dfs[paper]
        self.load_success = True
        return True

    def note_idx2citekey(self, r):
        '''
        @r: re match object
        '''
        self.citekey_to_touch = []
        content = ""
        citekey = ""
        MAX_IDX = self.df.cidx.max()
        idxs_raw = r.group(1).strip('[] ').split(',')
        idxs = []
        for idx in idxs_raw:
            connecter = r'[\-–]'
            if re.search(connecter, idx):
                start, end = re.split(connecter, idx)
                idxs += list(range(int(start), int(end) + 1))
            else:
                if int(idx) > MAX_IDX:
                    idx = str(idx).strip()
                    start_len = floor(len(idx) / 2)
                    start, end = idx[:start_len], idx[start_len:]
                    idxs += list(range(int(start), int(end) + 1))
                else:
                    idxs.append(int(idx))

        for idx in idxs:
            cdf = self.df[self.df.cidx == int(idx)]
            if content != "":  # not the first one
                content += ", "

            if len(cdf) == 0:
                content += f"[{idx}]"
            else:
                citekey = cdf.citekey.tolist()[0]
                content += f"[[@{citekey}]]"
                self.citekey_to_touch.append(citekey)

        if len(idxs) == 1 and zdf is not None:
            bdf = zdf[zdf.ID == citekey]
            if len(bdf) != 0:
                if pd.notna(bdf.shorttitle.tolist()[0]):
                    shorttitle = re.sub('[{}]', '', bdf.shorttitle.tolist()[0])
                    if is_same_item(shorttitle, r.group(1)):
                        return f"[[{citekey}|{shorttitle}]]"

        self.citekey_to_touch = set(self.citekey_to_touch)

        if citekey == "":  # no citekey found
            return r.group(0)
        else:
            return "(" + content + ")"

    def idx2paper(self, idx):
        cdf = self.df[self.df.cidx == int(idx)]
        if len(cdf) == 0:
            return None
        else:
            for _, row in cdf.iterrows():
                return row

    def touch_notes(self):
        new_notes = []
        for ck in self.citekey_to_touch:
            t = touch_note(ck)
            if t:
                new_notes.append(ck)
        self.citekey_to_touch = []
        return new_notes

    def convert_note(self, text):
        if self.load_success:
            pattern = r'(?:[^\s]+) (\[[\d, \-–]+\])'
            # print(re.findall(pattern, text))
            return re.sub(pattern, self.note_idx2citekey, text)
        else:
            cprint("[WARN]: Load paper failed, return original text.", c=31)
            return text


# %%

if __name__ == '__main__':
    CITEKEY = args.citekey.lstrip('@')
    if CITEKEY == "":
        with open(os.path.join(base_dir, 'history.txt'), 'r') as f:
            CITEKEY = f.readlines()[-1].strip('\n')
            cprint(f"[INFO] Load recent paper: {CITEKEY}", c=Color.yellow)

    # df = pd.read_csv(os.path.join('output', CITEKEY, 'title.csv'))

    with open(os.path.join('output', CITEKEY, 'title.txt'), 'r') as f:
        title_txt = f.read()

    converter = Converter()
    converter.load_paper(CITEKEY)
    while True:
        try:
            cprint("[INFO] Input text: (Double enter to force conversion)")
            lines = []
            for line in iter(partial(input, '>'), ''):
                lines.append(line)
                if re.match(r'^\d+$', line) is not None:
                    break
            text = '\n'.join(lines)

            if re.match(r'^\d+$', text) is not None:
                idx = int(text.strip())
                paper = converter.idx2paper(idx)
                if paper is not None:
                    citekey = paper.citekey
                    cprint(citekey, c=Color.cyan)
                    cprint(paper.title, c=Color.white, s=Style.bright)
                    cprint(f"zotero://select/items/@{citekey}",
                           c=Color.blue,
                           s=Style.underline)
                else:
                    cprint("Unfond citekey")
                    cite_str = re.findall(
                        r"(?:^|\n)\[" + str(idx) + r"\].*?(?:\n|$)", title_txt)
                    if len(cite_str) > 0:
                        cite_str = cite_str[0].strip("\n")
                        cprint(cite_str, c=35)
                        google_scholar_url = f"https://scholar.google.com/scholar&q={urllib.parse.quote(cite_str)}&lookup=0&hl=en"
                        cprint(google_scholar_url,
                               c=Color.blue,
                               s=Style.underline)
            else:
                cprint("Result:", c=44)
                output = converter.convert_note(text)
                pc.copy(output)
                cprint(output, c=36)
                print()

                cprint(
                    "[INFO] The content has been replaced in the clipboard!")
                converter.touch_notes()
            print("\n", "==" * 30, sep="")
        except KeyboardInterrupt:
            # print("Bye~")
            # break
            print("")
            continue