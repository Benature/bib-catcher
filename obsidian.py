import getpass
import json
import re
import requests

import bibtexparser
import pandas as pd


def write_note(citekey, template, bdf):
    cite = bdf[bdf.ID == citekey]
    if len(cite) == 0:
        print("Fail to find paper in Zotero")
        return ""
    idx = cite.index[0]
    bib = bdf.loc[idx].to_dict()

    template = template.replace(
        "{{entry.data.fields.shorttitle}}", "{{shorttitle}}")
    md = str(template)
    for k, v in bib.items():
        if pd.notna(v):
            v = re.sub(r'[{}]', '', v)
        else:
            v = ""
        md = md.replace("{{%s}}" % k, v)
    container = re.sub(r'[\\\{\}]', '', bib['booktitle'].replace(
        '\\vphantom', '')) if pd.notna(bib['booktitle']) else ""
    md = md.replace("{{containerTitle}}", container)
    md = md.replace("{{URL}}", requests.get(
        "https://doi.org/" + bib['doi']).url if pd.notna(bib['doi']) else "")
    md = md.replace("{{zoteroSelectURI}}", f"zotero://select/items/@{citekey}")
    md = md.replace("{{#each entry.author}} [[{{given}} {{family}}]],{{/each}}", ",".join(
        map(lambda x: " [["+x.strip()+"]]", bib['author'].replace(',', '').split('and'))))
    return md
