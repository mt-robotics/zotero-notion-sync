"""
Module Name: custom_exceptions.py
Description: This module defines custom exceptions used in the Zotero to Notion synchronization project.


This module allows for more readable and specific error reporting, improving the maintainability and debugging of the code.
"""


class InvalidReferenceError(Exception):
    """Exception raised for invalid references."""

    def __init__(self, message="Invalid reference provided"):
        super().__init__(message)
