# %%
import re
import requests
from bs4 import BeautifulSoup as bs
import time
import random
from collections import namedtuple
import pandas as pd
import os
import shutil
import traceback
import argparse

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

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
}
scholar = "https://scholar.google.com/scholar?q="


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
        cidx = re.findall(r'\[\d+\]', cite_list[i])[0].strip('[]')
        cidx = int(cidx)
        cite = re.sub(r'\[\d+\]', '', cite_list[i]).strip()
        if cite == "":
            continue

        print()
        print(cidx, "|", cite)

        duplicate = False

        duplicate_cites = base_df[base_df.title.apply(
            lambda t: is_same_item(t, cite))]
        print(base_df.title.apply(lambda t: is_same_item(t, cite)))
        if len(duplicate_cites) != 0:
            dc = duplicate_cites.reset_index()
            results.append(Cite(dc.citekey[0], cidx, dc.title[0]))
            print("[Pass] bibtex is exist. 💾")
            continue

        time.sleep(random.random()*3)
        url = scholar + cite
        response = requests.get(url, headers=headers)
        soup = bs(response.text, 'lxml')

        if check_block(soup):
            print("[Fatal] request too frequent! Please try later. 🤡")
            break

        gs_ris = soup.select('.gs_r.gs_or.gs_scl')
        CONTINUE = False
        if len(gs_ris) == 0:
            print("No result")
            CONTINUE = True
        else:
            gs = gs_ris[0]
            title = gs.select('h3')[0].text.strip()
            if not is_same_item(title, cite, echo=True):
                CONTINUE = True

        if CONTINUE:
            print(url.replace(" ", "%20"))
            print("not found 😢")
            fails.append(cite_list[i])
            # break # debug
            continue

        titles[cidx] = title

        # https://stackoverflow.com/questions/69428700/how-to-scrape-full-paper-citation-from-google-scholar-search-results-python
        data_cid = gs['data-cid']
        url_cite = f"https://scholar.google.com/scholar?q=info:{data_cid}:scholar.google.com/&output=cite&scirp=0&hl=zh-CN"

        ref = requests.get(url_cite)
        ref_soup = bs(ref.content, 'lxml')
        for citi in ref_soup.select('.gs_citi'):
            if 'BibTeX' == citi.text:
                bib = requests.get(citi['href'])
                if 'We\'re sorry...' in bib.text:
                    print("[Fatal] request too frequent! Please try later. 🤡\n")
                    print(bib.text)
                    BREAK = True
                    break
                bibs.append(bib.text)
                citekey = re.findall(r'@\w+\{(\w+),', bib.text)[0]
                results.append(Cite(citekey, cidx, title))
                print("OK ✌️", citekey)
                BREAK = False
                break
        if BREAK:
            print("BREAK")

            break

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
