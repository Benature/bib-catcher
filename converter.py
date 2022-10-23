# %%
from importlib.resources import contents
import re
from collections import namedtuple
import pandas as pd
import os
import shutil
import traceback
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


def idx2citekey(r):
    content = ""
    for idx in r.group(0).strip('[]').split(','):
        cdf = df[df.cidx == int(idx)]
        if content != "":  # not the first one
            content += ", "

        if len(cdf) == 0:
            content += idx
        else:
            citekey = cdf.citekey.tolist()[0]
            content += f"[[{citekey}]]"
    return "(" + content + ")"


# %%

while True:
    text = input("Input text: ")
    output = re.sub(r'\[([\d,]+)\]', idx2citekey, text)
    pc.copy(output)
    print()
    print(output)
    print()
    print("The content has been replaced in the clipboard!")
    print("="*30)
