# bib Catcher 🫳

[English | [中文](#bib-捕手-🫳)]

## Usage

```shell
pip install -r requirements.txt
```

Copy the **Reference** text from the paper and paste it into a file in `input/` folder. 
For example, I paste the followed text to `input/benson2010network.txt` ("benson2010network" is the citekey of the demo paper)

```txt
[1] M. Al-Fares, A. Loukissas, and A. Vahdat. A scalable, commodity data center network architecture. In SIGCOMM, pages 63–74, 2008.
[2] M. Al-Fares, S. Radhakrishnan, B. Raghavan, W. College, N. Huang, and A. Vahdat. Hedera: Dynamic flow scheduling for data center networks. In Proceedings of NSDI 2010, San Jose, CA, USA, April 2010. [3] T. Benson, A. Anand, A. Akella, and M. Zhang. Understanding Data Center Traffic Characteristics. In Proceedings of Sigcomm Workshop: Research on Enterprise Networks, 2009. 
[4] T. Benson, A. Anand, A. Akella, and M. Zhang. The case for fine-grained traffic engineering in data centers. In Proceedings of INM/WREN ’10, San Jose, CA, USA, April 2010. 
```

The text can be in only one line. Note that each reference should be separated with a space (` `), which is used to separate each reference by regular expression.

Run the cather to scrape the bibtex from Google Scholar.

```shell
python catcher.py benson2010network
```

After the catcher finished, there will be output files of benson2010network in `output/benson2010network/` and `recent/`.
- `ref.bib`: All the finded references' bibtex is saved here, which should be copied for later usage (in Zotero).
- `fail.txt`: The reference that is failed to find in Google Scholar. (May be it is just a webpage.)
- `title.txt`: The reference separated in each line, you can check whether the regular expression parse the **Reference** text as you want.
- `title.csv`: A table containing the index of reference in the paper and the reference's name. It may be helpful when you want to know what exactly reference the main boby cites, avoiding rolling back the end of paper (**Reference**).

---
# bib 捕手 🫳
[[English](#bib-catcher-🫳) | 中文]
### Notes

- There is a file (`base/all.csv`) that contains all caught reference in history, so that the code can avoid repeat searching same paper in Google Scholar.
- There is some `sleep()` in the code, so as to avoid being blocked by Google Scholar too soon.
- If the `output/` folder contains too many references, you can quickly get the output in `recent/`.


## 使用

```shell
pip install -r requirements.txt
```

复制文末的引用文献，黏贴到 `input/` 目录下的一个文件。比如我把下述文本粘贴在了 `input/benson2010network.txt` （“benson2010network” 是示例论文的 citekey）

```txt
[1] M. Al-Fares, A. Loukissas, and A. Vahdat. A scalable, commodity data center network architecture. In SIGCOMM, pages 63–74, 2008.
[2] M. Al-Fares, S. Radhakrishnan, B. Raghavan, W. College, N. Huang, and A. Vahdat. Hedera: Dynamic flow scheduling for data center networks. In Proceedings of NSDI 2010, San Jose, CA, USA, April 2010. [3] T. Benson, A. Anand, A. Akella, and M. Zhang. Understanding Data Center Traffic Characteristics. In Proceedings of Sigcomm Workshop: Research on Enterprise Networks, 2009. 
[4] T. Benson, A. Anand, A. Akella, and M. Zhang. The case for fine-grained traffic engineering in data centers. In Proceedings of INM/WREN ’10, San Jose, CA, USA, April 2010. 
```

这里的文本可以全在同一行，但是注意每一项引用都要有空格（` `）区分。否则正则表达式切分的时候会失败。

运行捕手，从谷歌学术中抓取对应文献的 bibtex。

```shell
python catcher.py benson2010network
```
运行结束后，benson2010network 的输出文件放在了 `output/benson2010network/` 和 `recent/` 目录下。
- `ref.bib`: 所有成功找到的文献 bibtex 都在这里。可以用来导入进 Zotero 中。
- `fail.txt`: 在谷歌学术中搜索失败的文献清单（可能那条文献只是一个网页）。
- `title.txt`: 正则表达式解析的结果，每行一项引用。可以在这里检查正则表达式的切分是否符合预期。
- `title.csv`: 一个表，存储了引用在文章的序号和对应的名字。当你在正文中想知道引用编号对应哪一个具体的文献时，可以直接看这个表，就不需要滚动到文末。

### 其他说明

- 有一个文件 `base/all.csv` 存储了所有的文献 bibtex 查找历史记录，这样可以避免在谷歌学术中重复搜索相同的已知文献。
- 代码中有 `sleep()` 函数，目的是防止太快被谷歌学术检测出是爬虫然后被拉黑。
- 如果 `output/` 目录放置了太多的文献资料，最近一次的输出信息可以直接在 `recent/` 中找到。