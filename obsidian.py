import getpass
import json
import re
import requests

import bibtexparser
import pandas as pd

ccf = pd.read_csv('base/CCF.csv')
ccf.name = ccf.name.str.replace("IEEE", '').replace("ACM", '')


def get_tag(container, bib):
    find = False
    doi_az = re.findall(r'[a-zA-Z]+', bib['doi'])
    if len(doi_az) != 0:
        abbr = doi_az[0]
        cdf = ccf[ccf.abbr == abbr]
        find = len(cdf) != 0

    if not find:
        cdf = ccf[ccf.name.apply(lambda x: x in container)]
        find = len(cdf) != 0

    if find:
        level = cdf.level.tolist()[0]
        abbr = cdf.abbr.tolist()[0]
        return f"A/CCF/{level}/{abbr}/{bib['year'][-2:]}"
    return ""


def write_note(citekey, template, bdf):
    cite = bdf[bdf.ID == citekey]
    if len(cite) == 0:
        print("Fail to find paper in Zotero")
        return ""
    idx = cite.index[0]
    bib = bdf.loc[idx].to_dict()

    template = template.replace("{{entry.data.fields.shorttitle}}",
                                "{{shorttitle}}")
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
    md = md.replace(
        "{{URL}}",
        requests.get("https://doi.org/" +
                     bib['doi']).url if pd.notna(bib['doi']) else "")
    md = md.replace("{{zoteroSelectURI}}", f"zotero://select/items/@{citekey}")
    md = md.replace(
        "{{#each entry.author}} [[{{given}} {{family}}]],{{/each}}", ",".join(
            map(lambda x: " [[" + x.strip() + "]]",
                bib['author'].replace(',', '').split('and'))))
    md = md.replace("tags: \n", f"tags: {get_tag(container, bib)}\n")
    return md
