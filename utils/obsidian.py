import re
import requests
import pandas as pd
from pathlib import Path
from .util import *

root_dir = Path(__file__).parent.parent

ccf = pd.read_csv(root_dir / "base/CCF.csv")
ccf.name = ccf.name.str.replace("IEEE", '').replace("ACM", '')


def get_tag(container, bib):
    find = False
    if isinstance(bib['doi'], str):
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
        if " " not in abbr.strip():
            return f"A/CCF/{level}/{abbr}/{bib['year'][-2:]}"
    return ""


def clean_latex(s):
    s = s.replace('\\vphantom', '')
    s = re.sub(r'[\\\{\}]', '', s)
    return s


def write_note(citekey, template, bdf):
    cite = bdf[bdf.ID == citekey]
    if len(cite) == 0:
        cprint("Fail to find paper in Zotero", c=Color.red)
        return ""
    idx = cite.index[0]
    B = bdf.loc[idx].to_dict()

    def get(key, f=str):
        return f(B[key]) if pd.notna(B[key]) else ""

    # template = template.replace("{{entry.data.fields.shorttitle}}",
    #                             "{{shorttitle}}")
    md = str(template)
    container = get("booktitle", clean_latex)
    md = md.replace("{{containerTitle}}", container)
    md = md.replace("{{titleShort}}", get("shorttitle", clean_latex))
    try:
        doi_url = requests.get("https://doi.org/" + str(B['doi'])).url
    except requests.exceptions.ProxyError:
        doi_url = ""
    md = md.replace(
        "{{#if URL}}{{URL}}{{else}}{{#if DOI}}https://doi.org/{{DOI}}{{/if}}{{/if}}",
        doi_url if pd.notna(B['doi']) else "")
    md = md.replace("{{zoteroSelectURI}}", f"zotero://select/items/@{citekey}")
    md = md.replace(
        "{{#each entry.author}} [[{{given}} {{family}}]],{{/each}}", ",".join(
            map(lambda x: " [[" + re.sub(r'[\{\}]', '', x.strip()) + "]]",
                B['author'].replace(',', '').split('and'))))
    md = md.replace("tags: \n", f"tags: {get_tag(container, B)}\n")
    for k, v in B.items():
        if pd.notna(v):
            v = re.sub(r'[{}]', '', v)
        else:
            v = ""
        v = clean_latex(v)
        md = md.replace("{{%s}}" % k, v)
    return md
