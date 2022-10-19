# bib Catcher 🫳

## Usage

```shell
pip install -r requirements.txt
```

Copy the **Reference** text from the paper and paste it into a file in `input/` folder. 
For example, I paste the followed text to `input/benson2010network.txt` ("benson2010network" is the citekey of the demo paper)

```txt
[1] M. Al-Fares, A. Loukissas, and A. Vahdat. A scalable, commodity data center network architecture. In SIGCOMM, pages 63–74, 2008. [2] M. Al-Fares, S. Radhakrishnan, B. Raghavan, W. College, N. Huang, and A. Vahdat. Hedera: Dynamic flow scheduling for data center networks. In Proceedings of NSDI 2010, San Jose, CA, USA, April 2010. 
```

The text can be in only one line. Note that each reference should be separated with a space (` `), which is used to separate each reference by regular expression.

Run the cather to scrape the bibtex from Google Scholar.

```shell
python catcher.py -i benson2010network
```

After the catcher finished, there will be output files of benson2010network in `output/benson2010network/` and `recent/`.
- `ref.bib`: All the finded references' bibtex is saved here, which should be copied for later usage (in Zotero).
- `fail.txt`: The reference that is failed to find in Google Scholar. (May be it is just a webpage.)
- `title.txt`: The reference separated in each line, you can check whether the regular expression parse the **Reference** text as you want.
- `title.csv`: A table containing the index of reference in the paper and the reference's name. It may be helpful when you want to know what exactly reference the main boby cites, avoiding rolling back the end of paper (**Reference**).