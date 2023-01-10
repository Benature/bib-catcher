# %%
import re
from collections import namedtuple
import pandas as pd
import os
import shutil
import traceback
import argparse
import time
from gscholar import query
import bibtexparser

from utils.util import *

# %%

parser = argparse.ArgumentParser()
parser.add_argument('source', type=str, default="")
args = parser.parse_args()

source = args.source.lstrip('@')
# CITEKEY = '@benson2010network'.lstrip('@')

# %%
check_environment()

# parse input
if os.path.exists(os.path.join(root_dir, 'input', source + ".txt")):
    print('Reading reference list from file')
    CITEKEY = source
    with open(os.path.join(root_dir, f'input/{CITEKEY}.txt'), 'r') as f:
        cites = f.read()
        cites = cites.replace('\n', ' ').strip(' \n') + ' [00]'
        cite_list = re.findall(r'\[\d+\].*?(?= \[\d+\])', cites)
else:
    print('Getting reference list from url/doi')
    cite_list = get_refs_from_url(source)
    bibs = query(source)
    assert len(bibs) > 0, f"Cannot find paper {source}"
    bib_dict = bibtexparser.loads(bibs[0]).entries[0]
    CITEKEY = bib_dict['ID']
    print(f"Paper: {bib_dict['title']} ({CITEKEY})")

# output dir
output_dir = os.path.join(root_dir, 'output', CITEKEY)
os.makedirs(output_dir, exist_ok=True)

title_path = os.path.join(output_dir, 'title.csv')
fail_ignore_path = os.path.join(output_dir, 'fail_ignore.txt')

base_df = pd.read_csv(base_path)
exist_titles = base_df.title.tolist()

last_fail_ignore = []
if os.path.exists(fail_ignore_path):
    with open(fail_ignore_path, 'r') as f:
        last_fail_ignore = f.read().split('\n')

Cite = namedtuple("Cite", "citekey cidx title")

# %%

results = []
bibs = []
fail_try, fail_ignore = [], []

if len(cite_list) == 0:
    cprint("No citation found. Exit.", c=Color.red)
    os._exit(1)

for i in range(len(cite_list)):
    try:
        cidx = int(re.findall(r'\[\d+\]', cite_list[i])[0].strip('[]'))
        cite = re.sub(r'\[\d+\]', '', cite_list[i]).strip()
        if cite == "":
            continue

        cprint(cidx, "|", cite)

        if "Website [online]" in cite:
            print("It is a website 😯")
            continue

        # if cite_list[i] in last_fail_ignore:
        #     fail_ignore.append(cite_list[i])
        #     cprint("[Pass] failed to find this paper before 😩", c=Color.yellow)
        #     continue

        # check whether the paper exists in base
        duplicate_cites = base_df[base_df.title.apply(
            lambda t: is_same_item(t, cite))]
        if len(duplicate_cites) != 0:
            dc = duplicate_cites.reset_index()
            # titles[cidx] = dc.title[0]
            results.append(Cite(dc.citekey[0], cidx, dc.title[0]))
            cprint("[Pass] bibtex is exist. 💾", c=Color.cyan, s=Style.faded)
            continue

        # query google scholar
        bib = query(cite)

        if len(bib) == 0:  # empty output
            cprint("not found 😢", c=Color.red)
            fail_try.append(cite_list[i])
            continue

        bib = bib[0]
        bib_db = bibtexparser.loads(bib)
        bib_dict = bib_db.entries[0]

        if not is_same_item(bib_dict['title'], cite,
                            echo=True):  # not same item
            cprint("different title 😢", c=Color.red)
            fail_ignore.append(cite_list[i])
            continue

        bibs.append(enrich_bib(bib_db))
        citekey = bib_dict['ID']
        results.append(Cite(citekey, cidx, bib_dict['title']))
        print("OK ✅", citekey)

    except ConnectionResetError or requests.exceptions.ProxyError:
        print("Network Error, wait 10s.")
        time.sleep(10)
        continue
    except Exception as e:
        print(e)
        traceback.print_exc()
        print(cite_list[i])
        break

# %%

# =======================================
#                收尾工作
# =======================================

with open(os.path.join(output_dir, 'title.txt'), 'w') as f:
    f.write('\n'.join(cite_list))

with open(os.path.join(output_dir, 'ref.bib'), 'a+') as f:
    f.write('\n'.join(bibs))

with open(os.path.join(output_dir, 'fail_try.txt'), 'w',
          encoding='utf-8') as f:
    f.write('\n'.join(fail_try))

with open(fail_ignore_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(fail_ignore))

if len(results) > 0:
    title_df = pd.DataFrame(results)
    if os.path.exists(title_path):
        title_df_old = pd.read_csv(title_path)
        title_df = pd.concat([title_df_old, title_df])
        title_df = title_df.drop_duplicates('cidx', keep='last')
    title_df_cidx = title_df.cidx.astype(int)
    title_df = title_df.drop('cidx', axis=1)
    title_df.insert(0, 'cidx', title_df_cidx)
    title_df = title_df.sort_values('cidx')
    title_df.to_csv(title_path, index=False)

    with open(os.path.join(output_dir, "zotero.md"), 'w') as f:
        f.write("\n".join([
            f"- [{row.cidx}: {row.title}](zotero://select/items/@{row.citekey})"
            for _, row in title_df.iterrows()
        ]))

shutil.rmtree('recent')
shutil.copytree(output_dir, 'recent')

# %%
base_df = pd.read_csv(base_path)
new_cites = []
for cite in results:
    subdf = base_df[base_df.citekey == cite.citekey]
    if len(subdf) == 0:
        new_cites.append(
            dict(
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
all_df = pd.concat([base_df, pd.DataFrame(new_cites)
                    ]).sort_values(['cite_count', 'citekey'], ascending=False)
all_df.to_csv(base_path, index=False)

# %%

print("\n", "==" * 30, sep='')
print("CITEKEY", CITEKEY)
with open(os.path.join(base_dir, 'history.txt'), 'a+') as f:
    f.write(CITEKEY + "\n")
# %%
