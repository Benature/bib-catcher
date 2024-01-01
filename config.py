import getpass
import os
from pathlib import Path

root_dir = Path(__file__).parent

# Basic
base_dir = os.path.join(root_dir, 'base')
base_path = os.path.join(base_dir, 'all.csv')

# Zotero
zotero_bib_path = '/Library/Zotero/Zotero.bib'

# Obsidian
obsidian_base_path = f'/Users/{getpass.getuser()}/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/'
ob_citation_plugin_path = '.obsidian/plugins/obsidian-citation-plugin/data.json'
ob_note_path = 'Reading-notes'
