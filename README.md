<a href="https://github.com/Benature/bib-catcher"><img src="https://i.328888.xyz/2022/12/10/f9HqU.png" height="150" align="right"></a>

# bib Catcher π«³

## Features

- Catch bibtex
    ```shell
    python catcher.py <citekey/doi>
    ```

- Convert reference index to citekey in wikilink format
    `<citekey>` is optional. If no citekey is provided, it will load the last caught paper.
    ```shell
    python converter.py <citekey>
    ```
    example:
    ```diff
    - Another line of recent work focuses on designing compact data structures [19,27,44] with tradeoffs between accuracy and resource footprints. 
    - Next, we compare the total storage overhead of SyNDB to that of NetSight [32]. 
    - Recent studies [65] have observed high utilization only across a few switch ports during congestion events.
    + Another line of recent work focuses on designing compact data structures ([[al2008scalable]], [[ghorbani2017drill]], [[li2019deter]]) with tradeoffs between accuracy and resource footprints. 
    + Next, we compare the total storage overhead of SyNDB to that of [[handigol2014know|NetSight]]. 
    + Recent studies ([[zhang2017high]]) have observed high utilization only across a few switch ports during congestion events.
    ```

- Rest API server *(via Flask)*
    ```shell
    python api.py
    ```

- Generate reference relationship graph
    ```shell
    python pyecharts.py
    ```

## Usage

[English | [δΈ­ζ](#bib-ζζ-π«³)]

```shell
pip install -r requirements.txt
```

Copy the **Reference** text from the paper and paste it into a file in `input/` folder. 
For example, I paste the followed text to `input/benson2010network.txt` ("benson2010network" is the citekey of the demo paper)

```txt
[1] M. Al-Fares, A. Loukissas, and A. Vahdat. A scalable, commodity data center network architecture. In SIGCOMM, pages 63β74, 2008.
[2] M. Al-Fares, S. Radhakrishnan, B. Raghavan, W. College, N. Huang, and A. Vahdat. Hedera: Dynamic flow scheduling for data center networks. In Proceedings of NSDI 2010, San Jose, CA, USA, April 2010. [3] T. Benson, A. Anand, A. Akella, and M. Zhang. Understanding Data Center Traffic Characteristics. In Proceedings of Sigcomm Workshop: Research on Enterprise Networks, 2009. 
[4] T. Benson, A. Anand, A. Akella, and M. Zhang. The case for fine-grained traffic engineering in data centers. In Proceedings of INM/WREN β10, San Jose, CA, USA, April 2010. 
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

### Notes

- There is a file (`base/all.csv`) that contains all caught reference in history, so that the code can avoid repeat searching same paper in Google Scholar.
- If the `output/` folder contains too many references, you can quickly get the output in `recent/`.


---
# bib ζζ π«³
[[English](#bib-catcher-π«³) | δΈ­ζ]

## δ½Ώη¨

```shell
pip install -r requirements.txt
```

ε€εΆζζ«ηεΌη¨ζη?οΌι»θ΄΄ε° `input/` η?ε½δΈηδΈδΈͺζδ»Άγζ―ε¦ζζδΈθΏ°ζζ¬η²θ΄΄ε¨δΊ `input/benson2010network.txt` οΌβbenson2010networkβ ζ―η€ΊδΎθ?Ίζη citekeyοΌ

```txt
[1] M. Al-Fares, A. Loukissas, and A. Vahdat. A scalable, commodity data center network architecture. In SIGCOMM, pages 63β74, 2008.
[2] M. Al-Fares, S. Radhakrishnan, B. Raghavan, W. College, N. Huang, and A. Vahdat. Hedera: Dynamic flow scheduling for data center networks. In Proceedings of NSDI 2010, San Jose, CA, USA, April 2010. [3] T. Benson, A. Anand, A. Akella, and M. Zhang. Understanding Data Center Traffic Characteristics. In Proceedings of Sigcomm Workshop: Research on Enterprise Networks, 2009. 
[4] T. Benson, A. Anand, A. Akella, and M. Zhang. The case for fine-grained traffic engineering in data centers. In Proceedings of INM/WREN β10, San Jose, CA, USA, April 2010. 
```

θΏιηζζ¬ε―δ»₯ε¨ε¨εδΈθ‘οΌδ½ζ―ζ³¨ζζ―δΈι‘ΉεΌη¨ι½θ¦ζη©Ίζ ΌοΌ` `οΌεΊεγε¦εζ­£εθ‘¨θΎΎεΌεεηζΆεδΌε€±θ΄₯γ

θΏθ‘ζζοΌδ»θ°·ζ­ε­¦ζ―δΈ­ζεε―ΉεΊζη?η bibtexγ

```shell
python catcher.py benson2010network
```
θΏθ‘η»ζεοΌbenson2010network ηθΎεΊζδ»ΆζΎε¨δΊ `output/benson2010network/` ε `recent/` η?ε½δΈγ
- `ref.bib`: ζζζεζΎε°ηζη? bibtex ι½ε¨θΏιγε―δ»₯η¨ζ₯ε―Όε₯θΏ Zotero δΈ­γ
- `fail.txt`: ε¨θ°·ζ­ε­¦ζ―δΈ­ζη΄’ε€±θ΄₯ηζη?ζΈεοΌε―θ½ι£ζ‘ζη?εͺζ―δΈδΈͺη½ι‘΅οΌγ
- `title.txt`: ζ­£εθ‘¨θΎΎεΌθ§£ζηη»ζοΌζ―θ‘δΈι‘ΉεΌη¨γε―δ»₯ε¨θΏιζ£ζ₯ζ­£εθ‘¨θΎΎεΌηεεζ―ε¦η¬¦ει’ζγ
- `title.csv`: δΈδΈͺθ‘¨οΌε­ε¨δΊεΌη¨ε¨ζη« ηεΊε·εε―ΉεΊηεε­γε½δ½ ε¨ζ­£ζδΈ­ζ³η₯ιεΌη¨ηΌε·ε―ΉεΊεͺδΈδΈͺε·δ½ηζη?ζΆοΌε―δ»₯η΄ζ₯ηθΏδΈͺθ‘¨οΌε°±δΈιθ¦ζ»ε¨ε°ζζ«γ

### εΆδ»θ―΄ζ

- ζδΈδΈͺζδ»Ά `base/all.csv` ε­ε¨δΊζζηζη? bibtex ζ₯ζΎεε²θ?°ε½οΌθΏζ ·ε―δ»₯ιΏεε¨θ°·ζ­ε­¦ζ―δΈ­ιε€ζη΄’ηΈεηε·²η₯ζη?γ
- ε¦ζ `output/` η?ε½ζΎη½?δΊε€ͺε€ηζη?θ΅ζοΌζθΏδΈζ¬‘ηθΎεΊδΏ‘ζ―ε―δ»₯η΄ζ₯ε¨ `recent/` δΈ­ζΎε°γ