# %%
import re
from collections import namedtuple
import pandas as pd
import os
import shutil
import traceback
import argparse
from gscholar import query
import bibtexparser

from utils import *

# %%

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input',  type=str, required=False, default="")
args = parser.parse_args()

if args.input == "":
    CITEKEY = '@benson2010network'.lstrip('@')
else:
    CITEKEY = args.input.lstrip('@')

# %%
check_environment()


output_dir = os.path.join('output', CITEKEY)
os.makedirs(output_dir, exist_ok=True)

title_path = os.path.join(output_dir, 'title.csv')


base_df = pd.read_csv(base_path)
exist_titles = base_df.title.tolist()

with open(f'input/{CITEKEY}.txt', 'r') as f:
    cites = f.read()
    cites = cites.replace('\n', ' ').strip(' \n') + ' [00]'


Cite = namedtuple("Cite", "citekey cidx title")

# %%

try:
    BREAK = True
    results = []
    fails = []
    titles = {}
    bibs = []

    cite_list = re.findall(r'\[\d+\].*?(?= \[\d+\])', cites)
    for i in range(len(cite_list)):
        cidx = int(re.findall(r'\[\d+\]', cite_list[i])[0].strip('[]'))
        cite = re.sub(r'\[\d+\]', '', cite_list[i]).strip()
        if cite == "":
            continue

        print('\n', cidx, "|", cite)

        # check whether the paper exists in base
        duplicate_cites = base_df[base_df.title.apply(
            lambda t: is_same_item(t, cite))]
        if len(duplicate_cites) != 0:
            dc = duplicate_cites.reset_index()
            titles[cidx] = dc.title[0]
            results.append(Cite(dc.citekey[0], cidx, dc.title[0]))
            print("[Pass] bibtex is exist. 💾")
            continue

        # query google scholar
        bib = query(cite)

        if len(bib) == 0:  # empty output
            print("not found 😢")
            fails.append(cite_list[i])
        bib = bib[0]
        bib_dict = bibtexparser.loads(bib).entries[0]

        if not is_same_item(bib_dict['title'], cite, echo=True):  # not same item
            print("different title 😢")
            fails.append(cite_list[i])
            continue

        title = bib_dict['title']
        titles[cidx] = title

        bibs.append(bib)
        citekey = bib_dict['ID']
        results.append(Cite(citekey, cidx, title))
        print("OK ✌️", citekey)

    # return titles, bibs, fails
except Exception as e:
    print(e)
    traceback.print_exc()

# %%


# =======================================
#                收尾工作
# =======================================

with open(os.path.join(output_dir, 'title.txt'), 'w') as f:
    f.write('\n'.join(cite_list))

with open(os.path.join(output_dir, 'ref.bib'), 'w') as f:
    f.write('\n'.join(bibs))

with open(os.path.join(output_dir, 'fail.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(fails))

df = pd.DataFrame(titles.items(), columns=['cid', 'title'])
if os.path.exists(title_path):
    title_df = pd.read_csv(title_path)
    df = pd.concat([title_df, df]).drop_duplicates('cid', keep='last')
    df = df.sort_values('cid')
df.to_csv(title_path, index=False)

shutil.rmtree('recent')
shutil.copytree(output_dir, 'recent')

# %%
base_df = pd.read_csv(base_path)
new_cites = []
for cite in results:
    subdf = base_df[base_df.citekey == cite.citekey]
    if len(subdf) == 0:
        new_cites.append(dict(
            citekey=cite.citekey,
            title=cite.title,
            cite_count=1,
            cite_by=f'{CITEKEY}({cite.cidx})',
        ))
    else:  # exist
        idx = subdf.index[0]
        if CITEKEY in base_df.loc[idx, 'cite_by']:
            continue
        base_df.loc[idx, 'cite_by'] += f';{CITEKEY}({cite.cidx})'
        base_df.loc[idx, 'cite_count'] += 1
all_df = pd.concat([base_df, pd.DataFrame(new_cites)]).sort_values(
    ['cite_count', 'citekey'], ascending=False)
all_df.to_csv(base_path, index=False)

# %%
