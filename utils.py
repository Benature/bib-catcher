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

all_title_path = 'base/all.csv'


def check_environment():
    dirs = ['base', 'recent', 'output']
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
    if not os.path.exists(all_title_path):
        with open(all_title_path, "w") as f:
            f.write("citekey,cite_count,title,cite_by\n")


def is_same_item(short, long, echo=False):
    replace_pattern = r'[\{\} -]'

    def parser(s):
        s = re.findall(r'[^\]]+$', s)[0]
        for k, v in {"’": "'", 'ﬁ': 'fi'}.items():
            s = s.replace(k, v)
        return re.sub(replace_pattern, '', s).lower()
    if parser(short) in parser(long):
        return True
    elif echo:
        print('💢', parser(short))
        print('💥', parser(long))
    return False


def check_block(soup):
    warning_text = 'Our systems have detected unusual traffic from your computer network.'

    title2warn = {
        'Google 學術搜尋': '請證明您不是自動程式',
        'Google Scholar': warning_text,
    }
    title = soup.head.title.text
    if title not in title2warn:
        if warning_text in soup.text:
            return True
    if title2warn[title] in soup.text:
        return True

    return False
