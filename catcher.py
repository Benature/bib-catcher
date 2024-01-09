# %%
import re
from collections import namedtuple
import pandas as pd
import os
import sys
import shutil
import traceback
import argparse
import time
import gscholar
# from gscholar import query
import bibtexparser
import subprocess
from urllib.error import HTTPError

from utils.util import *
from utils.google_scholar import crazy_query, QueryError

# %%

ALL_FINISH = True

gscholar_outformat = gscholar.FORMAT_BIBTEX

parser = argparse.ArgumentParser()
parser.add_argument('source',
                    type=str,
                    default="",
                    nargs='?',
                    help="citekey or doi or url")
parser.add_argument('--ignore_last_fail',
                    "-i",
                    action="store_true",
                    help="ignore the references that failed before")
parser.add_argument(
    '--force',
    "-f",
    action="store_true",
    help="force parse reference even though it is stored in the base database")
args = parser.parse_args()

source = args.source.lstrip('@').strip("\n")

# %%
check_environment()

print("Loading Zotero database...")
if os.path.exists(zotero_bib_path):
    with open(zotero_bib_path, "r") as f:
        ZDF = pd.DataFrame(bibtexparser.load(f).entries)  # Zotero DataFrame
else:
    ZDF = None

#: parse input
if source == "":
    recent_file = sorted(list((ROOT_DIR / "input").glob("*")),
                         key=lambda p: p.stat().st_mtime,
                         reverse=True)[0]
    source = recent_file.stem
    print(
        f"You didn't specify citekey/doi, but your last modified file in `input/` is {source}"
    )
    cprint(f"source = {source} ? (Ctrl+C to quit)", c=Color.red)

if Path(ROOT_DIR, 'input', source + ".txt").exists():
    print('Reading reference list from file')
    CITEKEY = source
    with open(ROOT_DIR / f'input/{CITEKEY}.txt', 'r') as f:
        cites = f.read()
        cites = cites.replace('\n', ' ').strip(' \n') + ' [00]'
        cite_list = re.findall(r'\[\d+\].*?(?= \[\d+\])', cites)
else:
    print('Getting reference list from url/doi')
    cite_list = get_refs_from_url(source)
    bibs = gscholar.query(source)
    assert len(bibs) > 0, f"Cannot find paper {source}"
    bib_dict = bibtexparser.loads(bibs[0]).entries[0]
    CITEKEY = bib_dict['ID']
    print(f"Paper: {bib_dict['title']} ({CITEKEY})")

# output dir
output_dir = ROOT_DIR / 'output' / CITEKEY
os.makedirs(output_dir, exist_ok=True)

title_csv_path = output_dir / 'title.csv'
fail_try_path = output_dir / 'fail_try.txt'
fail_ignore_path = output_dir / 'fail_ignore.txt'

base_df = pd.read_csv(base_all_csv_path)
exist_titles = base_df.title.tolist()

if not args.force:
    known_idxs = set(
        re.findall(rf"{CITEKEY}\((\d+)\)", ";".join(base_df.cite_by.tolist())))

last_fail_ignore = []
if fail_ignore_path.exists():
    with open(fail_ignore_path, 'r') as f:
        last_fail_ignore = f.read().strip("\n").split('\n')
last_fail_try = []
if fail_try_path.exists():
    with open(fail_try_path, "r") as f:
        last_fail_try = f.read().strip("\n").split('\n')

Cite = namedtuple("Cite", "citekey cidx title")

# %%

results = []
bibs = []
new_bibs = []
fail_try, fail_ignore = last_fail_try, last_fail_ignore

if len(cite_list) == 0:
    cprint("No citation found. Exit.", c=Color.red)
    os._exit(1)

for i in range(len(cite_list)):
    try:
        cidx = int(re.findall(r'\[\d+\]', cite_list[i])[0].strip('[]'))
        cite = re.sub(r'\[\d+\]', '', cite_list[i]).strip()
        if cite == "":
            continue

        cprint(cidx, "|", cite, end="")
        if not args.force and str(cidx) in known_idxs:
            cprint(" [Passed as known]", c=Color.gray)
            continue

        if "Website [online]" in cite:
            print("It is a website 😯")
            continue

        def try_url():
            # try if it is a url
            url_t = extract_url(cite)
            if url_t is not None:
                print("😯 extracted url:", url_t)
                results.append(Cite("", cidx, url_t))

        if args.ignore_last_fail:
            if cite_list[i] in last_fail_ignore or cite_list[
                    i] in last_fail_try:
                cprint(" [Passed as failed]", c=Color.yellow)
                try_url()
                continue
        print()

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
        # bibs = gscholar.query(cite, gscholar_outformat)
        bibs = crazy_query(cite)

        if len(bibs) == 0:  # empty output
            cprint("😭 not found", c=Color.red)
            fail_try.append(cite_list[i])
            try_url()
            continue

        bib = bibs[0]
        bib_db = bibtexparser.loads(bib)
        bib_dict = bib_db.entries[0]

        if not is_same_item(bib_dict['title'], cite,
                            echo=True):  # not same item
            cprint("😢 different title", c=Color.red)
            fail_ignore.append(cite_list[i])
            try_url()
            continue

        bibs.append(enrich_bib(bib_db))
        citekey = bib_dict['ID']
        results.append(Cite(citekey, cidx, bib_dict['title']))
        if ZDF is not None and len(ZDF[ZDF.ID == citekey]) == 0:
            new_bibs.append(enrich_bib(bib_db))
        print("    ✅", citekey)

    except ConnectionResetError or requests.exceptions.ProxyError:
        print("Network Error, wait 10s.", flush=True)
        time.sleep(10)
        continue
    except QueryError as e:
        print("😱😱😱", e)
        continue
    except KeyboardInterrupt as e:
        print(e)
        cprint("Force End", c=Color.red)
        break
    except Exception as e:
        print(e)
        traceback.print_exc()
        print(cite_list[i])
        ALL_FINISH = False
        break

# %%

# =======================================
#                收尾工作
# =======================================

with open(output_dir / 'all_ref.bib', 'a+') as f:
    f.write('\n'.join(bibs))

with open(output_dir / 'title.txt', 'w') as f:
    f.write('\n'.join(cite_list))

with open(output_dir / 'fail_try.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fail_try))

with open(fail_ignore_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(fail_ignore))

if len(results) > 0:
    title_df = pd.DataFrame(results)
    if title_csv_path.exists():
        title_df_old = pd.read_csv(title_csv_path)
        title_df = pd.concat([title_df_old, title_df])
        title_df = title_df.drop_duplicates('cidx', keep='last')
    title_df_cidx = title_df.cidx.astype(int)
    title_df = title_df.drop('cidx', axis=1)
    title_df.insert(0, 'cidx', title_df_cidx)
    title_df = title_df.sort_values('cidx')
    title_df.to_csv(title_csv_path, index=False)

    with open(output_dir / "zotero.md", 'w') as f:
        f.write("\n".join([
            f"- [{row.cidx}: {row.title}](zotero://select/items/@{row.citekey})"
            for _, row in title_df.iterrows()
        ]))

shutil.rmtree('recent')
shutil.copytree(output_dir, 'recent')

# %%
base_df = pd.read_csv(base_all_csv_path)
base_df.citekey.fillna("", inplace=True)
new_cites = []
for cite in results:
    subdf = base_df[(base_df.citekey == cite.citekey)
                    & (base_df.title == cite.title)]
    if len(subdf) == 0:
        new_cites.append(
            dict(
                citekey=cite.citekey,
                title=cite.title,
                cite_count=1,
                cite_by=f'{CITEKEY}({cite.cidx})',
            ))
    else:  # cite exists
        idx = subdf.index[0]
        if CITEKEY in base_df.loc[idx, 'cite_by']:
            # cite is already recorded
            continue
        base_df.loc[idx, 'cite_by'] += f';{CITEKEY}({cite.cidx})'
        base_df.loc[idx, 'cite_count'] += 1
all_df = pd.concat([base_df, pd.DataFrame(new_cites)
                    ]).sort_values(['cite_count', 'citekey'], ascending=False)
all_df.to_csv(base_all_csv_path, index=False)

# %%

print("\n", "==" * 30, sep='')
print("CITEKEY", CITEKEY)
with open(base_dir / 'history.txt', 'a+') as f:
    f.write(CITEKEY + "\n")
# %%

if len(new_bibs) > 0:
    with open(output_dir / 'new_refs.bib', 'w') as f:
        f.write('\n'.join(bibs))
    subprocess.Popen(
        ["open", "-a", "Zotero.app",
         str(output_dir / 'new_refs.bib')]).wait()  # macOS
