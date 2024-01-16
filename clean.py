from config import *
import pandas as pd
from pathlib import Path
import sys

base_df = pd.read_csv(base_all_csv_path)

known_citekeys = [
    d.stem for d in (Path(__file__).parent / 'output').iterdir() if d.is_dir()
] + list(base_df.citekey.dropna().unique())

if __name__ == '__main__':
    del_key = sys.argv[1]

    assert del_key not in known_citekeys, f'{del_key} is an unknown citekey'

    base_all_csv_path.rename(base_all_csv_path.parent /
                             f"{base_all_csv_path.stem}.bk.csv")
    new_df = base_df.drop(
        base_df[(base_df.citekey == del_key) |
                (base_df.cite_by.str.contains(del_key))].index)
    new_df.to_csv(base_all_csv_path, index=False)
