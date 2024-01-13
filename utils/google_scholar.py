import gscholar
from urllib.error import HTTPError

scholarly_used = False
config = None


class QueryError(Exception):
    """Fail to query"""


def gscholar_query(text):
    bibs = gscholar.query(text)
    return bibs


def my_gscholar_query(text):
    global config
    if config is None:
        from .gscholar_local.gscholar import gscholar as my_gscholar
        import yaml
        from pathlib import Path
        with open(Path(__file__).parent.parent / "config.yaml") as f:
            config = yaml.safe_load(f.read())
    bibs = my_gscholar.query(text, cookie=config['cookie'])
    return bibs


def scholarly_query(text):
    global scholarly_used
    if not scholarly_used:
        from scholarly import scholarly, ProxyGenerator
        from scholarly._proxy_generator import MaxTriesExceededException
        pg = ProxyGenerator()
        success = pg.FreeProxies()
        print("FreeProxies", success)
        scholarly.use_proxy(pg)
        scholarly_used = True
    bibs = []
    q = scholarly.search_pubs(text)
    gs_rt = q._soup.select(".gs_rt")
    if len(gs_rt) == 0:
        return bibs
    query_item = gs_rt[0]
    title = query_item.text
    pub_q = scholarly.search_pubs(title)
    pub = next(pub_q)

    bib = scholarly.bibtex(pub)
    bibs.append(bib)
    return bibs


def crazy_query(text):
    try:
        return gscholar_query(text)
    except HTTPError as e:
        print("😱 gscholar: ", e)

    try:
        return scholarly_query(text)
    except MaxTriesExceededException as e:
        print("😱 scholarly:", e)

    try:
        return my_gscholar_query(text)
    except Exception as e:
        print(e)
        import traceback
        traceback.print_exc()
    raise QueryError


if __name__ == '__main__':
    cite = 'S. Chole, A. Fingerhut, S. Ma, A. Sivaraman, S. Vargaftik, A. Berger, G. Mendelson, M. Alizadeh, S.-T. Chuang, I. Keslassy, A. Orda, T. Edsall, DRMT: Disaggregated Programmable Switching, in: ACM SIGCOMM Conference, 2017, p. 1–14.'
    scholarly_query(cite)
