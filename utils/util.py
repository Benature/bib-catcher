import re
import os
from bibtexparser.bwriter import BibTexWriter
import requests
from bs4 import BeautifulSoup as bs

from config import *
from .cprint import *


def check_environment():
    dirs = ['base', 'recent', 'output']
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
    if not os.path.exists(base_path):
        with open(base_path, "w") as f:
            f.write("citekey,cite_count,title,cite_by\n")


def parser(s):
    replace_pattern = r'[\{\} -\.\?\:]+'
    s = re.sub(r'\[\w\]', "", s)
    # s = re.findall(r'[^\]]+$', s)[0]
    for k, v in {"’": "'", 'ﬁ': 'fi'}.items():
        s = s.replace(k, v)
    s = re.sub(replace_pattern, '', s).lower()
    return s


def is_same_item(short, long, echo=False):
    if parser(short) in parser(long):
        return True
    elif echo:
        print('💢', parser(short))
        print('💥', parser(long))
    return False


def enrich_bib(bib_db):
    title = bib_db.entries[0]['title']
    if ':' in title:
        shorttitle = title.split(':')[0].strip(' ')
        if len(shorttitle.split(' ')) == 1:
            bib_db.entries[0]['shorttitle'] = shorttitle
    writer = BibTexWriter()
    return writer.write(bib_db)


def get_refs_from_url(url):
    if not url.startswith('http'):
        # then it would be a doi
        if 'doi' not in url:
            url = os.path.join("https://doi.org/", url)

    for _retry in range(10):
        try:
            response = requests.get(url)
        except requests.exceptions.ProxyError:
            print("Failed to get, try again later", end='')
            import time
            for i in range(10):
                time.sleep(1)
                print(end='.')
            continue
        print()
        if _retry >= 9:
            os._exit(1)
        break

    cite_list = []
    print(response.url)
    if 'dl.acm' in response.url:
        soup = bs(response.text, 'lxml')
        for i, ref in enumerate(soup.select('.references__item')):
            c = ref.select('.references__note')[0].contents[0]
            cite_list.append(f"[{i+1}] " + c)
    elif 'ieeexplore.ieee' in response.url:
        arnumber = response.url.split('/')[-2]
        ref_url = f"https://ieeexplore.ieee.org/xpl/dwnldReferences?arnumber={arnumber}"
        response = requests.get(ref_url)
        soup = bs(response.text, 'lxml')
        cite_list = soup.select('body')[0].text.replace('\t', '').replace(
            '\n\n', '').strip(' \n').split('\n')
        cite_list = list(
            map(
                lambda c: re.sub(r'^\d+\.', lambda x:
                                 f"[{x.group(0).rstrip('.')}] ", c).strip(),
                cite_list))
    return cite_list


def cprint(*args, c=30, s=Style.bright, b=None, sep=' ', end='\n'):
    '''color print'''
    string = sep.join(map(str, args))
    if isinstance(c, int):
        string = f"\033[1;{c}m" + string + "\033[0m"
    else:
        f = get_cprint_format(c, s, b)
        string = f.format(string)
    print(string, end=end)