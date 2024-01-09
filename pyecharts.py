# %%
from pyecharts import options as opts
from pyecharts.charts import Graph
import pandas as pd
import re

from config import *

# %%
categories = [
    opts.GraphCategory(name="reference", symbol='circle'),
    opts.GraphCategory(name="paper", symbol='rect'),
]

# %%
df = pd.read_csv(base_all_csv_path)

# %%
nodes, links = [], []

papers = set(
    map(lambda x: re.sub(r"\(\d+\)$", '', x),
        ";".join(df.cite_by.tolist()).split(';')))
for paper in papers:
    cite_df = df[df.cite_by.str.contains(paper)]
    nodes.append(
        opts.GraphNode(name=paper,
                       category='paper',
                       symbol_size=(len(cite_df))))

for i, row in df.iterrows():
    if row.citekey not in papers:
        nodes.append(
            opts.GraphNode(name=row.citekey,
                           category='reference',
                           value=row.title,
                           symbol_size=row.cite_count * 10))
    for paper in row.cite_by.split(';'):
        paper = re.sub(r"\(\d+\)$", '', paper)
        links.append(opts.GraphLink(source=paper, target=row.citekey))

# %%
c = (
    Graph(init_opts=opts.InitOpts(
        # width="700px", height="500px",
        bg_color="#ffffff")).add(
            "",
            nodes,
            links,
            categories,
            repulsion=1000,
            edge_label=opts.LabelOpts(is_show=False,
                                      position="middle",
                                      formatter="{c}"),
            is_selected=True,
            is_draggable=True).set_global_opts(title_opts=opts.TitleOpts(
                title="References")))
c.render_notebook()
c.render('index.html')

# %%
