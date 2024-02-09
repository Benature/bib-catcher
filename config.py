import getpass
import yaml
from pathlib import Path

ROOT_DIR = Path(__file__).parent

# Basic
base_dir = ROOT_DIR / 'base'
base_all_csv_path = base_dir / 'all.csv'

_config_path = ROOT_DIR / "config.yaml"

if not _config_path.exists():
    from shutil import copy
    copy(ROOT_DIR / "utils/config.sample.yaml", _config_path)

with open(_config_path) as f:
    CONFIG = yaml.safe_load(f.read())

# Zotero
zotero_bib_path = CONFIG["Zotero_path"]

# Obsidian
ob_note_path = CONFIG["Obsidian_note_path"]
obsidian_base_path = Path(CONFIG['Obsidian_base_path'].format(USER=getpass.getuser()))
ob_citation_plugin_path = obsidian_base_path / '.obsidian/plugins/obsidian-citation-plugin/data.json'
