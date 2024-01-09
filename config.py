import getpass
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent

# Basic
base_dir = ROOT_DIR / 'base'
base_all_csv_path = base_dir / 'all.csv'

# Zotero
zotero_bib_path = '/Library/Zotero/Zotero.bib'

# Obsidian
obsidian_base_path = Path(
    f'/Users/{getpass.getuser()}/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/'
)
ob_citation_plugin_path = obsidian_base_path / '.obsidian/plugins/obsidian-citation-plugin/data.json'
ob_note_path = 'Reading-notes'
