"""
Module Name: main.py
Description: Entry point for synchronizing Zotero references with a Notion database.
This script imports configurations and initializes the `ZoteroToNotion` class to 
execute the `sync_zotero_to_notion` method, enabling seamless data transfer from 
Zotero to Notion.

Usage:
Run this module directly to initiate the synchronization process.
"""

from zotero_notion_sync import config
from zotero_notion_sync.zotero_to_notion import ZoteroToNotion

if __name__ == "__main__":
    # Create an instance of the ZoteroToNotion class with dependency injection
    zotero_to_notion = ZoteroToNotion(config)

    # Call the sync_zotero_to_notion method
    zotero_to_notion.sync_zotero_to_notion()
