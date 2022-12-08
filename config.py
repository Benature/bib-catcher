import getpass
import os

root_dir = os.path.dirname(os.path.abspath(__file__))

# Basic
base_dir = os.path.join(root_dir, 'base')
base_path = os.path.join(base_dir, 'all.csv')

# Zotero
zotero_bib_path = '/Library/Zotero/Zotero.bib'

# Obsidian
obsidian_bse_path = f'/Users/{getpass.getuser()}/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/'
ob_citation_plugin_path = '.obsidian/plugins/obsidian-citation-plugin/data.json'
ob_note_path = 'Reading-notes'
