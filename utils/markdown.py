from collections import OrderedDict
import yaml
from pathlib import Path
import re


class MarkdownMetadataHandler:

    def __init__(self, md_file_path, prekeys=None):
        self.md_file_path = Path(md_file_path)
        self.metadata_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n',
                                           re.MULTILINE | re.DOTALL)
        self.prekeys = [] if prekeys is None else prekeys

    def extract_metadata(self):
        with self.md_file_path.open('r', encoding='utf-8') as file:
            content = file.read()
            match = self.metadata_pattern.search(content)
            if match:
                metadata_str = match.group(1)
                return yaml.safe_load(metadata_str)
            else:
                return {}

    def sort_metadata(self, metadata):
        """Force some keys in custom order"""
        ordered_metadata = OrderedDict()
        for key in self.prekeys:
            if key in metadata:
                ordered_metadata[key] = metadata[key]
        for key, value in metadata.items():
            if key in ordered_metadata:
                continue
            ordered_metadata[key] = value
        return ordered_metadata

    def generate_metadata(self, new_metadata):
        """
        yaml.dump() 对缩进支持有问题，且对于文本没有使用引号包围（双括号`[[文本]]`需要）。
        因此造轮子
        """
        updated_metadata_str = "---\n"
        ordered_metadata = self.sort_metadata(new_metadata)
        for key, value in ordered_metadata.items():
            if isinstance(value, list):
                updated_metadata_str += f"{key}:\n"
                for item in value:
                    if isinstance(item, str) and '[' in item and ']' in item:
                        updated_metadata_str += f"  - \"{item}\"\n"
                    else:
                        updated_metadata_str += f"  - {item}\n"
            elif isinstance(value, str):
                value = "" if value == 'None' else value
                updated_metadata_str += f'{key}: "{value}"\n'
            else:
                updated_metadata_str += f'{key}: {value or ""}\n'
        updated_metadata_str += "---\n"
        return updated_metadata_str

    def update_metadata(self, new_metadata):
        with self.md_file_path.open('r', encoding='utf-8') as file:
            content = file.read()
        metadata_match = self.metadata_pattern.search(content)
        if metadata_match is None:
            return
        m_start = metadata_match.start()
        m_end = metadata_match.end()

        metadata_str = self.generate_metadata(new_metadata)

        content = content[:m_start] + metadata_str + content[m_end:]
        with self.md_file_path.open('w', encoding='utf-8') as file:
            file.write(content)
