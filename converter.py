# %%
import re
import pandas as pd
import os
import argparse
from gscholar import query
import bibtexparser
import pyperclip as pc

from utils import *

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

    if len(idxs) == 1 and zdf is not None:
        bdf = zdf[zdf.ID == citekey]
        if len(bdf) != 0:
            shorttitle = re.sub('[{}]', '', bdf.shorttitle.tolist()[0])
            if is_same_item(shorttitle, r.group(1)):
                return f"[[{citekey}|{shorttitle}]]"

    return r.group(1) + " (" + content + ")"


# %%

while True:
    text = input("Input text:\n")
    output = re.sub(r'([\w\.]+) (\[[\d,]+\])', idx2citekey, text)
    pc.copy(output)
    print()
    print(output)
    print()
    print("The content has been replaced in the clipboard!")
    print("="*30)
