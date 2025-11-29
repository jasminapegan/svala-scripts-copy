import os.path

from lxml import etree


def validate_xml(file_path: str):
    try:
        parser = etree.XMLParser(dtd_validation=True)
        schema_root = etree.parse(file_path)
        return True
    except Exception as e:
        print(f"Invalid xml {file_path}: {e}")
        return False
