"""
Module Name: decorators.py
Description: This module contains custom Python decorators designed for validating function input in the context of a 
Zotero-to-Notion synchronization application. The decorators help ensure that certain conditions are met before 
executing the wrapped function, raising custom exceptions or logging errors when validation fails.
"""

import logging
from functools import wraps
from zotero_notion_sync.custom_exceptions import InvalidReferenceError


def validate_key(reference, required_key):
    """
    Validate that the reference is a dictionary and contains the required key.

    Args:
        reference (dict): The reference data to validate.
        required_key (str): The key that must be present in the reference.

    Returns:
        bool: True if valid, False otherwise.
    """
    return isinstance(reference, dict) and required_key in reference


def validate_creators_list(creators):
    """
    Validate that the creators argument is a list of dictionaries with necessary keys.

    Args:
        creators (list): A list of creator dictionaries.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(creators, list):
        return False
    for creator in creators:
        if not isinstance(creator, dict) or (
            "name" not in creator
            and "lastName" not in creator
            and "firstName" not in creator
        ):
            return False
    return True


def validate_reference_with_key(required_key="data"):
    """
    Decorator to validate the `reference` argument of a method for the presence of a specified key.

    This decorator ensures that the `reference` argument passed to the decorated method is a dictionary
    containing the required key. If the `reference` is not a dictionary or the key is missing, an
    `InvalidReferenceError` is raised and the method execution is halted. Any exceptions during the
    validation or method execution are logged as errors.

    Args:
        required_key (str): The key that must be present in the `reference` dictionary. Defaults to "data".

    Returns:
        function: The wrapped function with the added validation.

    Raises:
        InvalidReferenceError: If `reference` is not a dictionary or the `required_key` is not found in it.

    Example:
        @validate_reference_with_key("data")
        def process_reference(self, reference):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, reference, *args, **kwargs):
            try:
                if not validate_key(reference, required_key):
                    raise InvalidReferenceError(
                        f"Missing key '{required_key}' in reference."
                    )
                return func(self, reference, *args, **kwargs)
            except InvalidReferenceError as e:
                logging.error("Validation error: %s", e)
                return None
            except Exception as e:
                logging.error("An error occurred: %s", e)
                raise

        return wrapper

    return decorator


def validate_creators():
    """
    Decorator to validate the `creators` argument of a method.

    This decorator ensures that the `creators` argument passed to the decorated method
    is a list of dictionaries, each containing at least one of the required keys: 'name',
    'lastName', or 'firstName'. If the validation fails, an `InvalidReferenceError` is raised,
    logged, and the decorated method is not executed.

    Returns:
        function: The wrapped function with the added validation.

    Raises:
        InvalidReferenceError: If the `creators` argument is not a list or if any item in the list
        is not a dictionary containing the required keys.

    Example:
        @validate_creators()
        def format_authors(self, creators):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, creators, *args, **kwargs):
            try:
                if not validate_creators_list(creators):
                    raise InvalidReferenceError(
                        "Creators should be a list of dictionaries with 'name', 'lastName', or 'firstName' keys."
                    )

                return func(self, creators, *args, **kwargs)
            except InvalidReferenceError as e:
                logging.error("Validation error: %s", e)
                return None  # Ensure a safe return after the error
            except Exception as e:
                logging.error("An unexpected error occurred: %s", e)
                raise

        return wrapper

    return decorator
