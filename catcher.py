# %%
import re
from collections import namedtuple
import pandas as pd
import os
import shutil
import traceback
import argparse
import time
import bibtexparser
import subprocess

from utils.util import *
from utils.google_scholar import crazy_query, QueryError

# %%

ALL_FINISH = True

parser = argparse.ArgumentParser()
parser.add_argument('source',
                    type=str,
                    default="",
                    nargs='?',
                    help="citekey or doi or url")
parser.add_argument('--max',
                    '-m',
                    type=int,
                    default=-1,
                    help="max index to search")
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

txt_file_path = ROOT_DIR / f'input/{source}.txt'
recent_dir = ROOT_DIR / 'recent'
if txt_file_path.exists():
    CITEKEY = source
    print(f'Reading reference list from file: {txt_file_path}')
    with open(txt_file_path, 'r') as f:
        cites = f.read()
        cites = cites.replace('\n', ' ').strip(' \n') + ' [00]'
        cite_list = re.findall(r'\[\d+\].*?(?= \[\d+\])', cites)
else:
    print('Getting reference list from url/doi')
    net_data = get_refs_from_url(source)
    cite_list = net_data["cite_list"]
    title_query_txt_path = recent_dir / "title_query.txt"
    with open(title_query_txt_path, 'w') as f:
        f.write("\n".join(cite_list))
    print(f"save title to {str(title_query_txt_path.relative_to(ROOT_DIR))}")

    # find citekey
    doi = source.replace("https://doi.org/", "")
    z_query = ZDF[ZDF.doi == doi]
    if len(z_query) > 0 and pd.notna(z_query.iloc[0].ID):
        CITEKEY = z_query.iloc[0].ID
        cprint(f"Paper citekey: {CITEKEY}", c=Color.red)
    else:
        for query_ in (source, net_data["title"]):
            bibs_query = crazy_query(net_data["title"])
            if len(bibs_query) > 0:
                for b in bibs_query:
                    print(b)
                break

        assert len(bibs_query) > 0, f"Cannot find paper {source}"
        bib_dict = bibtexparser.loads(bibs_query[0]).entries[0]
        CITEKEY = bib_dict['ID']
        cprint(f"Paper citekey: {CITEKEY} | {bib_dict['title']}", c=Color.red)
        input("check")
    # move file
    print(f"moving title.txt to input/{CITEKEY}.txt")
    title_query_txt_path.rename(ROOT_DIR / f"input/{CITEKEY}.txt")

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
BIBs = []
new_BIBs = []
fail_try, fail_ignore = last_fail_try, last_fail_ignore

if len(cite_list) == 0:
    cprint("No citation found. Exit.", c=Color.red)
    os._exit(1)

i = 0
# for i in range(len(cite_list)):
while i < len(cite_list):
    if args.max > 0 and i > args.max:
        cprint(f"Stop as required ({i}/{len(cite_list)})", c=Color.red)
        break
    try:
        cidx = int(re.findall(r'\[\d+\]', cite_list[i])[0].strip('[]'))
        cite = re.sub(r'\[\d+\]', '', cite_list[i]).strip()
        if cite == "":
            continue

        print(funny_enrich(f"{cidx}/{len(cite_list)} | {cite}"), end=" ")
        if not args.force and str(cidx) in known_idxs:
            cprint("[Passed as known]", c=Color.green, s=Style.faded)
            i += 1
            continue

        if "Website [online]" in cite:
            print("It is a website 😯")
            continue

        def try_url():
            # try if it is a url
            url_t = extract_url(cite)
            if url_t is not None:
                cprint("🔗 extracted url:", url_t, c=Color.gray)
                results.append(Cite("", cidx, url_t))

        if args.ignore_last_fail:
            if cite_list[i] in last_fail_ignore or cite_list[
                    i] in last_fail_try:
                cprint("[Passed as failed]",
                       c=Color.yellow,
                       s=Style.underline,
                       end=" (Ignore Mode)\n")
                try_url()
                i += 1
                continue
        print()

        # check whether the paper exists in base
        duplicate_cites = base_df[base_df.title.apply(
            lambda t: is_same_item(t, cite))]
        duplicate_cites = duplicate_cites[duplicate_cites.citekey.apply(
            lambda k: re.match("^[^\d]+", k).group() in cite.lower())]
        if len(duplicate_cites) != 0:
            dc = duplicate_cites.reset_index()
            # titles[cidx] = dc.title[0]
            results.append(Cite(dc.citekey[0], cidx, dc.title[0]))
            cprint("[Pass] bibtex is exist. 💾", c=Color.cyan, s=Style.faded)
            i += 1
            continue

        # query google scholar
        bibs_query = crazy_query(cite)

        if len(bibs_query) == 0:  # empty output
            cprint("😭 found nothing", c=Color.red)
            fail_try.append(cite_list[i])
            try_url()
            i += 1
            continue

        bib = bibs_query[0]
        bib_db = bibtexparser.loads(bib)
        bib_dict = bib_db.entries[0]

        if not is_same_item(bib_dict['title'], cite,
                            echo=True):  # not same item
            cprint("😢 different title", c=Color.red)
            fail_ignore.append(cite_list[i])
            try_url()
            i += 1
            continue

        BIBs.append(enrich_bib(bib_db))
        citekey = bib_dict['ID']
        results.append(Cite(citekey, cidx, bib_dict['title']))
        if ZDF is not None and len(ZDF[ZDF.ID == citekey]) == 0:
            new_BIBs.append(enrich_bib(bib_db))
        print("    ✅", citekey)

    except ConnectionResetError or requests.exceptions.ProxyError:
        print("Network Error, wait 10s.", flush=True)
        time.sleep(10)
        continue
    # except QueryError as e:
    #     print("😱😱😱", e)
    #     continue
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
    i += 1

# %%

# =======================================
#                收尾工作
# =======================================

with open(output_dir / 'all_ref.bib', 'a+') as f:
    f.write('\n'.join(BIBs))

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

if len(new_BIBs) > 0:
    with open(output_dir / 'new_refs.bib', 'w') as f:
        # f.write('\n'.join(bibs))
        f.write('\n'.join(new_BIBs))
    cprint(f"There are {len(new_BIBs)} new bibs", c=Color.green)
    subprocess.Popen(
        ["open", "-a", "Zotero.app",
         str(output_dir / 'new_refs.bib')]).wait()  # macOS
