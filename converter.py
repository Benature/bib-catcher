# %%
import re
import pandas as pd
import os
import argparse
import bibtexparser
import pyperclip as pc
import json
from math import floor
import urllib.parse
from functools import partial
import subprocess
import sys

from utils.util import *
from utils.obsidian import write_note
from utils.markdown import MarkdownMetadataHandler

# %%

parser = argparse.ArgumentParser()
parser.add_argument('citekey', type=str, default="", nargs='?')
parser.add_argument('--command', type=str, default="convert", required=False)
args = parser.parse_args()

# %%
print("Loading Zotero database...")
if os.path.exists(zotero_bib_path):
    with open(zotero_bib_path, "r") as f:
        ZDF = pd.DataFrame(bibtexparser.load(f).entries)  # Zotero DataFrame
else:
    ZDF = None

print("Loading Citation plugin configuration...")
ob_config_path = os.path.join(obsidian_base_path, ob_citation_plugin_path)
if os.path.exists(ob_config_path):
    with open(ob_config_path, 'r') as f:
        ob_template = json.loads(f.read())['literatureNoteContentTemplate']
else:
    ob_template = None


def gen_note_path(citekey):
    return Path(obsidian_base_path, ob_note_path, f"@{citekey}.md")


def touch_note(citekey):
    print("touch", citekey)
    if ob_template is None:
        cprint("no template", 31)
        return False
    note_path = gen_note_path(citekey)
    # print(note_path)
    if os.path.exists(note_path):
        cprint(f"[INFO] Note already exists: {citekey}")
        return False
    md = write_note(citekey, ob_template, ZDF)
    if md == "":
        return False
    cprint(f"[INFO] Write new note: {citekey}", c=33)
    with open(note_path, 'w') as f:
        f.write(md)
    return True


def get_alias_from_ob_note(citekey):
    """get alias from obsidian note

    Args:
        citekey (str): 

    Returns:
        link: link to note
        alias(es): string | List[string]
    """
    note_path = gen_note_path(citekey)
    if note_path.exists():
        handler = MarkdownMetadataHandler(note_path)
        meta = handler.extract_metadata()
        aliases = []
        if "alias" in meta:
            aliases.append(meta["alias"])
        if "aliases" in meta and meta["aliases"] is not None:
            aliases += meta["aliases"]

        while None in aliases:
            aliases.remove(None)

        if aliases:
            return f"[[@{citekey}|{aliases[0]}]]", aliases
    else:
        cprint(f"[WARN]: Cannot find note of {citekey}, ignored.", c=31)
    return "", []


def get_shorttitle_from_zotero(citekey):
    bdf = ZDF[ZDF.ID == citekey]
    if len(bdf) != 0 and pd.notna(bdf.shorttitle.tolist()[0]):
        shorttitle = re.sub(r'[\{\}]', '', bdf.shorttitle.tolist()[0])
        return f"[[@{citekey}|{shorttitle}]]"
    return ""


class Converter():

    def __init__(self):
        self.dfs = {}
        self.load_success = False
        self.citekey_to_touch = set()

    def load_paper(self, paper):
        '''paper CITEKEY'''
        paper = paper.lstrip('@')
        if paper not in self.dfs:
            paper_path = ROOT_DIR / 'output' / paper / 'title.csv'
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
        content = ""
        citekey = ""
        MAX_IDX = self.df.cidx.max()

        pre_str = r.group('pre') or r.group('pre_cn')
        match_str = r.group('idx') or r.group('idx_cn')

        idxs_raw = re.split(r'[,，]', match_str.strip('[]【】 '))
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

        cite_valid_num = 0
        for idx in idxs:
            cdf = self.df[self.df.cidx == int(idx)]
            if content != "":  # not the first one
                content += ", "

            if len(cdf) == 0:
                content += f"[{idx}]"
            else:
                citekey = cdf.citekey.tolist()[0]
                self.citekey_to_touch.add(citekey)

                # find paper alias
                new_text, aliases = get_alias_from_ob_note(citekey)
                if new_text == "":
                    new_text = get_shorttitle_from_zotero(citekey)
                if new_text == "":
                    new_text = f"[[@{citekey}]]"
                content += new_text
                cite_valid_num += 1

        if citekey == "":  # no citekey found
            return r.group(0)
        else:
            whole_str = r.group(0)
            if cite_valid_num > 1:
                content = "{" + content + "}"
            else:  # only one citation
                for alias in aliases:
                    alias_m = re.search(alias, pre_str, re.IGNORECASE)
                    if alias_m is not None:
                        new_pre = pre_str.replace(
                            alias_m.group(),
                            f"[[@{citekey}|{alias_m.group().strip()}]]")
                        whole_str = whole_str.replace(pre_str,
                                                      new_pre.rstrip())
                        content = ""
                        break
            return whole_str.replace(match_str, content)

    def idx2paper(self, idx):
        cdf = self.df[self.df.cidx == int(idx)]
        if len(cdf) == 0:
            return None
        else:
            for _, row in cdf.iterrows():
                return row

    def touch_notes(self):
        citekeys = ",".join(self.citekey_to_touch)
        subprocess.Popen(
            ["python3",
             str(__file__), citekeys, "--command", "touch"])
        self.citekey_to_touch = set()

    def convert_note(self, text):
        if self.load_success:
            pattern = r'(?P<pre>[^\s]+ )(?P<idx>\[[\d, \-–]+\])|(?P<pre_cn>[^\s【】]+? ?)(?P<idx_cn>[\[【][\d, ，\-–]+?[】\]])'
            print(re.findall(pattern, text))
            return re.sub(pattern, self.note_idx2citekey, text)
        else:
            cprint("[WARN]: Load paper failed, return original text.", c=31)
            return text


# %%

if __name__ == '__main__':
    CITEKEY = args.citekey.lstrip('@')
    if args.command == 'convert':
        pass
    elif args.command == "touch":
        for ck in CITEKEY.split(","):
            touch_note(ck)
        print(">", end="")
        sys.exit(0)
    else:
        raise Warning("Unknown command:", args.command)
    if CITEKEY == "":
        with open(os.path.join(base_dir, 'history.txt'), 'r') as f:
            CITEKEY = f.readlines()[-1].strip('\n')
            cprint(f"[INFO] Load recent paper: {CITEKEY}", c=Color.yellow)

    with open(os.path.join('output', CITEKEY, 'title.txt'), 'r') as f:
        title_txt = f.read()

    converter = Converter()
    converter.load_paper(CITEKEY)
    while True:
        try:
            cprint(
                "[INFO] Input text: (Double enter to start conversion, Ctrl+D to quit)"
            )
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
