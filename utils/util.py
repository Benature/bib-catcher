import re
import os
from bibtexparser.bwriter import BibTexWriter
import requests
from bs4 import BeautifulSoup as bs

from config import *
from .cprint import *


def check_environment():
    [(ROOT_DIR / d).mkdir(exist_ok=True) for d in ['base', 'recent', 'output']]
    if not base_all_csv_path.exists():
        with open(base_all_csv_path, "w") as f:
            f.write("citekey,cite_count,title,cite_by\n")


def parser(s):
    s = re.sub(r'\[\w\]', "", s)
    # s = re.findall(r'[^\]]+$', s)[0]
    for k, v in {"’": "'", 'ﬁ': 'fi'}.items():
        s = s.replace(k, v)
    s = re.sub(r'[\$\s\{\}\-\.\?\:\\\(\)]', '', s).lower()
    return s


def is_same_item(short, long, echo=False):
    if parser(short) in parser(long):
        return True
    elif echo:
        print('💢', short)
        print('💥', long)
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
            cprint(url, c=Color.blue, s=Style.underline)
            response = requests.get(url)
        except requests.exceptions.ProxyError:
            print("Failed to get, try again later", end='', flush=True)
            import time
            for i in range(10):
                time.sleep(1)
                print(end='.', flush=True)
            continue
        print()
        if _retry >= 9:
            os._exit(1)
        break

    cite_list = []
    cprint(response.url, c=Color.blue, s=Style.underline)
    if 'dl.acm' in response.url:
        soup = bs(response.text, 'lxml')
        for i, ref in enumerate(soup.select('.references__item')):
            # c = ref.select('.references__note')[0].contents[0]
            # cite_list.append(f"[{i+1}] " + c)
            cite_list.append(ref.select('.references__note')[0].text)
    elif 'ieeexplore.ieee' in response.url:
        arnumber = response.url.split('/')[-2]
        ref_url = f"https://ieeexplore.ieee.org/xpl/dwnldReferences?arnumber={arnumber}"
        cprint(ref_url, c=Color.blue, s=Style.underline)
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.41",
        }
        response = requests.get(ref_url, headers=headers)
        if response.status_code == 200:
            soup = bs(response.text, 'lxml')
            cite_list = soup.select('body')[0].text.replace('\t', '').replace(
                '\n\n', '').strip(' \n').split('\n')
            cite_list = list(
                map(
                    lambda c: re.sub(r'^\d+\.', lambda x:
                                     f"[{x.group(0).rstrip('.')}] ", c).strip(
                                     ), cite_list))
        else:
            print(response.status_code)
            # print(response.text)
        print()
    elif "elsevier" in response.url:
        print("Not support yet: elsevier")
    title = soup.title.text

    return dict(cite_list=cite_list, title=title)


def extract_url(text):
    known_domain = r"https?://(github)"
    urls = re.findall(r"(https?://[\w\%\-\+\~/\.\s\&\=\?]*?)\s?(?:$|/\.|,)",
                      text)
    if urls:
        url = urls[0].rstrip(".").replace(" ", "")
        if len(url) < 50 and re.match(known_domain,
                                      url) is None:  # if the url is too short
            cprint(f"🔗 maybe it is a short link? : {url}", c=Color.gray)
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    url = r.url
            except Exception as e:
                cprint(f"[ERROR] Failed to load url", c=Color.red)
                pass
        return url
    return None


def cprint(*args, c=30, s=Style.bright, b=None, sep=' ', end='\n', **kwargs):
    '''colorfully print'''
    string = sep.join(map(str, args))
    if isinstance(c, int):
        string = f"\033[1;{c}m" + string + "\033[0m"
    else:
        f = get_cprint_format(c, s, b)
        string = f.format(string)
    print(string, end=end, flush=True, **kwargs)


def funny_enrich(string):
    findall = re.findall(r"^(.*?)(19[5-9]\d|20[0-3]\d)(.*?)$", string)
    if findall:
        fa = findall[0]
        f_gf = get_cprint_format(color=Color.white, style=Style.faded)
        f_g = get_cprint_format(color=Color.gray)
        return f_gf.format(fa[0]) + f_g.format(fa[1]) + f_gf.format(fa[2])
    return string


def notify(message: str,
           title: str,
           subtitle: str = '',
           sound: str = 'Hero',
           method: str = '',
           open: str = '',
           activate: str = '',
           icon: str = '',
           contentImage: str = '',
           sender: str = '',
           terminal_notifier_path: str = 'terminal-notifier') -> None:
    """Send notification
    
    Args:
        message  (str): Message
        title    (str): Title of notification
        subtitle (str): Subtitle of notification
        sound    (str): Sound of notification
                        (Valid sound names located in `/System/Library/Sounds`, `~/Library/Sounds`)
        method   (str): Method to send notification 
                        (For macOS: `osascript` and `terminal-notifier`)
        
        (Args below Only valid for `terminal-notifier`)
        
        open         (str): Click to open application or url
                            e.g. 'https://github.com/Benature' 
        activate     (str): activate in `terminal-notifier`
        icon         (str): Icon of notification (url)
                            e.g. 'https://i.loli.net/2020/12/06/inPGAIkvbyK7SNJ.png'
        contentImage (str): Image of notification (url)
                            e.g. 'https://raw.githubusercontent.com/Benature/WordReview/ben/WordReview/static/media/muyi.png'
        sender       (str): Using sender's icon as notification's icon
                            e.g. 'com.apple.automator.Confluence'
        terminal_notifier_path (str): Specific `terminal-notifier` exec path
    
    Limitation:
        Only support macOS for now, issue to let me know if you have a need in Windows or Linux.
    """
    import platform
    sysstr = platform.system()

    if sysstr == 'Darwin':  # macOS
        if method == 'terminal-notifier':
            '''https://github.com/julienXX/terminal-notifier'''

            t = f'-title "{title}"'
            m = f'-message "{message}"'
            s = f'-subtitle "{subtitle}"'
            sound = f'-sound "{sound}"'

            icon = f'-appIcon "{icon}"'
            sender = f'-sender "{sender}"'
            contentImage = f'-contentImage "{contentImage}"'

            activate = '' if activate == '' else f'-activate "{activate}"'
            open = '' if open == '' else f'-open "{open}"'

            args = ' '.join(
                [m, t, s, icon, activate, open, sound, sender, contentImage])
            os.system(f'{terminal_notifier_path} {args}')
        else:
            sound = f'sound name "{sound}"' if sound else ''
            os.system(
                f"""osascript -e 'display notification "{message}" with title "{title}" subtitle "{subtitle}" {sound}'"""
            )
    elif sysstr == "Windows":
        print('TODO: windows notification')
    elif sysstr == "Linux":
        print('TODO: Linux notification')
