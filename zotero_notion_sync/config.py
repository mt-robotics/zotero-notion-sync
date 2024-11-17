"""
Module Name: config.py
Description: This module handles the configuration settings for the Zotero to Notion 
synchronization project. It loads environment variables and sets the required 
credentials for accessing the Zotero and Notion APIs.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Zotero Credentials
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")

# Notion Credentials
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
