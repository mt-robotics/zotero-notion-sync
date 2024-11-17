"""
Module Name: zotero_to_notion.py
Description: This module facilitates the synchronization of Zotero references with a Notion database.
It contains the `ZoteroToNotion` class and associated methods for:
- Fetching references and collections from Zotero.
- Formatting and validating data to match Notion's requirements.
- Adding or updating references in a Notion database.
- Ensuring the correct handling of date and author information.

The module supports seamless data integration, allowing for enhanced workflow management and research tracking between Zotero and Notion.
"""

import json
import logging
from datetime import datetime
import requests
from zotero_notion_sync.decorators import validate_reference_with_key, validate_creators
import zotero_notion_sync.logging_config  # pylint: disable=unused-import; Though unused, this is important to make the custom logging format work

# logging.basicConfig(level=logging.DEBUG) # We no longer use the default logging configuration but the upgraded one (upgraded on top of the logging module)

# Create a custom logger specifically for the current module (zotero_to_notion)
ztn_logger = logging.getLogger(__name__)
ztn_logger.setLevel(logging.DEBUG)


class ZoteroToNotion:
    """
    A class to synchronize Zotero references with a Notion database.

    This class provides methods to fetch references from Zotero, format data,
    and either add or update these references in a specified Notion database.
    It integrates with the Notion and Zotero APIs to facilitate the synchronization process.
    """

    def __init__(self, cfg):
        self.config = cfg
        self.zotero_headers = {"Zotero-API-Key": self.config.ZOTERO_API_KEY}
        self.notion_headers = {
            "Authorization": f"Bearer {self.config.NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def fetch_zotero_reference(self):
        """
        Fetch references from Zotero using the Zotero API.

        This method sends a GET request to the Zotero API to retrieve references
        for a specific user in JSON format. It logs the process of fetching data
        and checks if the response is valid.

        Returns:
            list or dict: A list of references if the request is successful, or an empty list if the status code is not 200. If the response cannot be parsed as JSON, an empty dictionary is returned.

        Raises:
            ValueError: If the response content cannot be parsed as JSON.

        Note:
            The method assumes the `ZOTERO_USER_ID` and `zotero_headers` are
            already defined in the class.

        Example:
            references = self.fetch_zotero_reference()
        """

        ztn_logger.debug("Fetching Zotero references...")
        url = f"https://api.zotero.org/users/{self.config.ZOTERO_USER_ID}/items"
        params = {"format": "json"}

        response = requests.get(
            url, headers=self.zotero_headers, params=params, timeout=30
        )

        # Check if the request returns a valid response
        try:
            response_data = response.json()
            ztn_logger.debug("References: %s", response_data)
        except ValueError:
            ztn_logger.error("Failed to parse response: %s", response.text)
            return {}

        return response_data if response.status_code == 200 else []

    def fetch_collections(self):
        """
        Fetch collections from Zotero using the Zotero API.

        This method sends a GET request to the Zotero API to retrieve collections
        for a specific user and constructs a dictionary with collection IDs as keys
        and their corresponding names as values.

        Returns:
            dict: A dictionary mapping collection IDs to their names. Returns an
                empty dictionary if the request fails, cannot be parsed as JSON,
                or receives an empty response.

        Raises:
            ValueError: If the response content cannot be parsed as JSON.

        Note:
            The method assumes the `ZOTERO_USER_ID` and `zotero_headers` are
            already defined in the class.

        Example:
            collections = self.fetch_collections()
        """

        url = f"https://api.zotero.org/users/{self.config.ZOTERO_USER_ID}/collections"
        response = requests.get(url, headers=self.zotero_headers, timeout=30)

        # Check if the request returns a valid response
        try:
            response_data = response.json()
            ztn_logger.debug("All Collections: %s", response_data)
        except ValueError:
            ztn_logger.error("Failed to parse JSON response: %s", response.text)
            return {}

        # Build a dictionary with collection ID as key and name as value
        collections = {}

        if response.status_code == 200 and response_data:
            for collection in response_data:
                logging.debug("Collection Key: %s", collection["key"])
                logging.debug("Collection Data: %s", collection["data"])
                logging.debug("Collection Name: %s", collection["data"]["name"])
                logging.debug("Response Data Type: %s", type(collection))
                logging.debug("Collection Data Type: %s", type(collection["data"]))

                if (
                    isinstance(collection, dict)
                    and "key" in collection
                    and "data" in collection
                    and isinstance(collection["data"], dict)
                    and "name" in collection["data"]
                ):
                    collections[collection["key"]] = collection["data"]["name"]
                    ztn_logger.debug("Collection: %s", collection)
                else:
                    ztn_logger.warning(
                        "Skipping invalid collection format: %s", collection
                    )
        else:
            ztn_logger.warning(
                "Failed to fetch collections or received an empty response."
            )

        return collections

    def parse_date(self, date_str):
        """
        Parse a date string and format it to "YYYY-MM-DD".

        This method attempts to parse an input date string using various date
        formats from the most to least specific. If parsing is successful, it
        returns the date in a format compatible with Notion ("YYYY-MM-DD"). If
        the input cannot be parsed using the supported formats or if it is empty,
        the method logs a warning and returns None.

        Args:
            date_str (str): The date string to be parsed.

        Returns:
            str or None: The formatted date as a string in "YYYY-MM-DD" format
                        if parsing is successful; None otherwise.

        Raises:
            ValueError: If the provided date string does not match any of the
                        supported formats.

        Example:
            formatted_date = self.parse_date("2023-05-15T13:34:41+00:00")
            # Output: "2023-05-15"

        Note:
            The method tries parsing the date string with the following formats:
            - Full ISO format with timezone ("%Y-%m-%dT%H:%M:%S%z")
            - "YYYY-MM-DD"
            - "YYYY/M"
            - "YYYY"
        """
        # Check for empty or Non date strings and return None immediately
        if not date_str:
            ztn_logger.warning("Date string is empty or None.")
            return None
        # Define the date format to try, from most to lease specific
        date_formats = [
            "%Y-%m-%dT%H:%M:%S%z",  # Full ISO format with timezone
            # (e.g., "2023-05-15T13:34:41+00:00")
            "%Y-%m-%d",  # Date in "YYYY-MM-DD" format
            "%Y/%m",  # Date in "YYYY/M" format
            "%Y",  # Year-only format (e.g., "2023")
        ]
        for date_format in date_formats:
            try:
                # Try to parse the date with the current format
                parsed_date = datetime.strptime(date_str, date_format)

                # Format the parsed date to "YYYY-MM-DD" for Notion compatibility
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                # If parsing fails, move to the next format
                continue
        # Log a warning if no formats match
        ztn_logger.warning("Failed to parse date: %s. No formats match!", date_str)

        # Return None if no formats match
        return None

    @validate_creators()
    def format_authors(self, creators):
        """
        Format author names from a list of creators into a comma-separated string.

        This method processes a list of creator dictionaries to extract and format
        author names. It handles cases where the creator is an organization or an
        individual with first and last names.

        Args:
            creators (list): A list of dictionaries representing creators, where each dictionary
                            may contain 'name' for organizational authors or 'firstName' and
                            'lastName' for individual authors.

        Returns:
            str: A formatted string of author names, joined by commas. If no authors are found,
                returns an empty string.

        Decorators:
            @validate_creators: Ensures that the input is a list of dictionaries with the
                                required keys.
        """

        authors = []

        for creator in creators:
            # if isinstance(creator, dict) and 'name' in creator and creator['name']:
            if "name" in creator and creator["name"]:
                # Organizational author or single name field
                authors.append(creator["name"])
            else:
                # Individual author with firstName and lastName
                fullname = (
                    f"{creator.get('firstName', '')} {creator.get('lastName', '')}"
                )
                authors.append(fullname)

        return ", ".join(authors)

    def format_collection_names(self, collection_ids, collections):
        """
        Format collection names based on a list of collection IDs and a dictionary of collections.

        This method takes a list of collection IDs and a dictionary mapping collection IDs to
        their respective names, converting the list of IDs into a list of corresponding names.
        It checks the validity of the inputs and logs information or warnings as needed.

        Args:
            collection_ids (list): A list of collection IDs to be converted into collection names.
            collections (dict): A dictionary where keys are collection IDs and values are collection names.

        Returns:
            list: A list of collection names corresponding to the provided collection IDs. Returns an
                empty list if the input is invalid or if no matching names are found.

        Logs:
            - Debug logs for the input collection IDs and collections dictionary.
            - Warning log if the input data is invalid or if the conversion fails.
        """

        # Check if collection_ids is a list containing values and collections is a dictionary
        if len(collection_ids) > 0 and isinstance(collections, dict):
            ztn_logger.debug("Collection IDs: %s", collection_ids)
            ztn_logger.debug("Collections: %s", collections)

            # Change the list of collection ids to that of collection names
            collection_names = [
                collections.get(collection_id, "") for collection_id in collection_ids
            ]

            return collection_names

        ztn_logger.warning(
            "Failed to format collection names. Collection IDs: %s, Collections: %s.",
            collection_ids,
            collections,
        )

        return []

    # Method to update a reference in Notion if it already exists
    @validate_reference_with_key()
    def update_reference_in_notion(self, page_id, reference, collection_names):
        """
        Update an existing reference in Notion with formatted data from Zotero.

        This method prepares and sends a PATCH request to update a page in Notion with data from a Zotero reference.
        The data includes formatted dates, authors, collection names, and various metadata such as tags, publisher,
        DOI, and abstract.

        Args:
            page_id (str): The ID of the Notion page to update.
            reference (dict): A dictionary containing data from a Zotero reference. The 'data' key must be present.
            collection_names (list): A list of collection names to be associated with the Notion entry.

        Returns:
            None

        Raises:
            ValueError: If the response cannot be parsed as JSON.
            KeyError: If expected keys are missing in the reference data (handled by the decorator).
            Exception: For unexpected errors during the request.

        Logs:
            - Logs information when a reference is successfully updated.
            - Logs an error if the update request fails or the response cannot be parsed.
            - Warnings and debug logs may be present from helper methods for specific data processing.
        """

        # Format Access Date and Publication Date to be compatible with Notion: YYYY-MM-DD
        access_date = self.parse_date(reference["data"].get("accessDate", ""))
        publication_date = self.parse_date(reference["data"].get("date", ""))

        # Format Authors (comma-separated string)
        authors = self.format_authors(reference["data"].get("creators", []))

        # Prepare data to upload in Notion
        data = {
            "properties": {
                "Collections": {
                    "multi_select": [
                        {"name": collection_name}
                        for collection_name in collection_names
                        if collection_name
                    ]
                },
                "Authors": {"rich_text": [{"text": {"content": authors}}]},
                "Source URL": {"url": reference["data"].get("URL", "")},
                "Tags": {
                    "multi_select": [
                        {"name": tag["tag"]}
                        for tag in reference["data"].get("tag", [])
                        if isinstance(tag, dict) and "tag" in tag
                    ]
                },
                "Item Type": {
                    "select": {"name": reference["data"].get("itemType", "")}
                },
                # Books generally have publishers
                "Publisher": {
                    "rich_text": [
                        {"text": {"content": reference["data"].get("publisher", "")}}
                    ]
                },
                # Besides books, Publisher is sometimes shown in the extra field (journalArticle type for example)
                "Extra": {
                    "rich_text": [
                        {"text": {"content": reference["data"].get("extra", "")}}
                    ]
                },
                "DOI": {
                    "rich_text": [
                        {"text": {"content": reference["data"].get("DOI", "")}}
                    ]
                },
                "Abstract": {
                    "rich_text": [
                        {"text": {"content": reference["data"].get("abstractNote", "")}}
                    ]
                },
            }
        }

        # Conditionally add date fields only if they have valid values
        if access_date:
            data["properties"]["Date Accessed"] = {"date": {"start": access_date}}
        if publication_date:
            data["properties"]["Publication Date"] = {
                "date": {"start": publication_date}
            }

        # Send update request to Notion
        url = f"https://api.notion.com/v1/pages/{page_id}"
        response = requests.patch(
            url, headers=self.notion_headers, data=json.dumps(data), timeout=30
        )

        # Check if the request returns a valid response
        try:
            response_data = response.json()
            # ztn_logger.debug(response_data)
        except ValueError:
            ztn_logger.error("Failed to parse response: %s", response.text)

        # Check if the request was successful
        if response.status_code == 200:
            ztn_logger.info("Updated '%s' in Notion.", reference["data"]["title"])
        else:
            ztn_logger.error(
                "Failed to update '%s': %s", reference["data"]["title"], response_data
            )

    @validate_reference_with_key()
    def add_reference_to_notion(self, reference, collection_names):
        """
        Adds a reference to the Notion database or updates it if it already exists.

        This method checks if a reference already exists in the specified Notion database
        by matching the title and collection names. If it exists, the reference is updated.
        If it does not exist, the method creates a new entry with formatted data, including
        authors, dates, and other metadata.

        Args:
            reference (dict): The reference data dictionary containing relevant metadata
                            (e.g., title, authors, date).
            collection_names (list): A list of collection names associated with the reference.

        Returns:
            None: The method performs operations and logs results but does not return any value.

        Raises:
            ValueError: If the response from the Notion API cannot be parsed.
            InvalidReferenceError: Raised by the decorator if the reference data is missing
                                the required key or format.
        """

        # Check if the reference already exists in Notion by retrieving its ID (a.k.a, page ID)
        page_id = self.find_reference_in_notion(
            reference["data"]["title"], collection_names
        )

        # Initialize variables
        authors = ""
        access_date = None
        publication_date = None

        if page_id:
            # If it exists, update the entry
            self.update_reference_in_notion(page_id, reference, collection_names)
            return

        # If it doesn't exist, create a new entry
        # Format Access Data and Publication Date to be compatible with Notion: YYYY-MM-DD
        access_date = self.parse_date(reference["data"].get("accessDate", ""))
        publication_date = self.parse_date(reference["data"].get("date", ""))

        # Format Authors (comma-separated string)
        authors = self.format_authors(reference["data"].get("creators", []))

        # Prepare the data for Notion
        data = {
            "parent": {"database_id": self.config.NOTION_DATABASE_ID},
            "properties": {
                "Title": {"title": [{"text": {"content": reference["data"]["title"]}}]},
                "Collections": {
                    "multi_select": [
                        {"name": collection_name}
                        for collection_name in collection_names
                        if collection_name
                    ]
                },
                "Authors": {"rich_text": [{"text": {"content": authors}}]},
                "Source URL": {"url": reference["data"].get("url", "")},
                "Tags": {
                    "multi_select": [
                        {"name": tag["tag"]}
                        for tag in reference["data"].get("tags", [])
                        if isinstance(tag, dict) and "tag" in tag
                    ]
                },
                "Item Type": {
                    "select": {"name": reference["data"].get("itemType", "")}
                },
                # Books generally have publishers
                "Publisher": {
                    "rich_text": [
                        {"text": {"content": reference["data"].get("publisher", "")}}
                    ]
                },
                # Besides books, Publisher is sometimes shown in the extra field (journalArticle type for example)
                "Extra": {
                    "rich_text": [
                        {"text": {"content": reference["data"].get("extra", "")}}
                    ]
                },
                "DOI": {
                    "rich_text": [
                        {"text": {"content": reference["data"].get("DOI", "")}}
                    ]
                },
                "Abstract": {
                    "rich_text": [
                        {"text": {"content": reference["data"].get("abstractNote", "")}}
                    ]
                },
                # Set a default value for the Status and Category field
                "Status": {"status": {"name": "Not started"}},
                "Category": {"select": {"name": "Academic"}},
            },
        }

        # Conditionally add date fields only if they have valid values
        if access_date:
            data["properties"]["Date Accessed"] = {"date": {"start": access_date}}
        if publication_date:
            data["properties"]["Publication Date"] = {
                "date": {"start": publication_date}
            }

        # Send data to Notion
        url = "https://api.notion.com/v1/pages"

        response = requests.post(
            url, headers=self.notion_headers, data=json.dumps(data), timeout=30
        )

        # Check if the request returns a valid response
        try:
            response_data = response.json()
            # ztn_logger.debug(response_data)
        except ValueError:
            ztn_logger.error("Failed to parse response: %s", response.text)
            return

        # Check if the request was successful
        if response.status_code == 200:
            ztn_logger.info("Added '%s' to Notion.", reference["data"]["title"])
        else:
            ztn_logger.error(
                "Failed to add '%s': %s", reference["data"]["title"], response_data
            )

    def find_reference_in_notion(self, title, collection_names):
        """
        Finds a reference in the Notion database based on the title and collection names.

        This method constructs a query payload and sends a request to the Notion API
        to search for a specific reference by matching the title and, optionally, the
        collection names. If multiple matches are found, a warning is logged and the
        first match is returned.

        Args:
            title (str): The title of the reference to search for.
            collection_names (list): A list of collection names to filter the search by.

        Returns:
            str or None: The page ID of the found reference if it exists; None if no match is found.

        Raises:
            ValueError: If the response from the Notion API cannot be parsed.
            Exception: Logs and raises any unexpected errors during the search process.

        Logs:
            - Debug logs for the search URL and the results returned by the Notion API.
            - Warning logs if multiple entries are found with the same title and collection names.
            - Error logs if the response parsing fails or if there are unexpected issues.

        """

        search_url = f"https://api.notion.com/v1/databases/{self.config.NOTION_DATABASE_ID}/query"
        ztn_logger.debug("Search URL: %s", search_url)

        # Construct filters for each collection name
        collection_filters = []

        if collection_names:
            collection_filters = [
                {"property": "Collections", "multi_select": {"contains": name}}
                for name in collection_names
                if name
            ]
            ztn_logger.debug("Collection filters: %s", collection_filters)

        # Build the payload to check for a title match and at least one collection match
        search_payload = {
            "filter": {
                "and": [
                    {"property": "Title", "title": {"equals": title}},
                ]
            }
        }

        # Add the collections filter only if necessary
        if collection_filters:
            search_payload["filter"]["and"].append({"or": collection_filters})

        ztn_logger.debug("Search payload: %s", search_payload)

        response = requests.post(
            search_url,
            headers=self.notion_headers,
            data=json.dumps(search_payload),
            timeout=30,
        )

        # Check if the request returns a valid response
        try:
            response_data = response.json()
            ztn_logger.debug("Response data parsed: %s", response_data)
        except ValueError:
            ztn_logger.error("Failed to parse response: %s", response.text)
            return None

        if response.status_code == 200 and response_data:
            # Check if the result is a dictionary and has the required keys
            if (
                isinstance(response_data, dict)
                and "results" in response_data
                and isinstance(response_data["results"], list)
            ):
                results = response_data["results"]
                ztn_logger.debug("Search Results: %s", results)

            # Log a warning in case there are more than one result for the same title and collections
            if len(results) > 1:
                ztn_logger.warning(
                    "Multiple entries found for title: '%s' and collections: '%s'. Returning the first match.",
                    title,
                    collection_names,
                )

            # If a result is found, return the page ID for updating using the update_reference_in_notion method
            if results:
                ztn_logger.debug("Page ID: %s", results[0]["id"])
                return results[0][
                    "id"
                ]  # Generally, there shouldn't be duplicated entries, so there should only be one match (hence choosing the first match)
        return None

    def sync_zotero_to_notion(self):
        """
        Synchronizes references from Zotero to a Notion database.

        This method retrieves references from the Zotero library and associated collections.
        It checks if each reference already exists in the Notion database by matching the title and associated collections.
        If a match is found, the method skips adding the reference. If no match is found, it adds the reference to Notion.

        Steps:
        1. Fetch references from Zotero.
        2. Fetch collections from Zotero.
        3. Iterate through each reference:
        - Format the collection names based on the IDs found in the reference.
        - Check if the reference exists in Notion.
        - If it exists, log that it is skipped.
        - If it does not exist, add it to the Notion database.

        Returns:
            None: This function does not return any values. It performs operations to sync data between Zotero and Notion.
        """

        references = self.fetch_zotero_reference()
        ztn_logger.debug("References: %s", references)

        collections = self.fetch_collections()
        ztn_logger.debug("Collections: %s", collections)

        for reference in references:

            if reference is None:
                continue

            if (
                "data" in reference
                and isinstance(reference["data"], dict)
                and "title" in reference["data"]
            ):
                title = reference["data"]["title"]
                # Format Collections (list of collections)
                collection_names = self.format_collection_names(
                    reference["data"].get("collections", []), collections
                )
                logging.debug("Collection names of '%s': %s", title, collection_names)

                if self.find_reference_in_notion(title, collection_names):
                    ztn_logger.debug(
                        "Reference: '%s' with Collection names: %s already exists in Notion. Skipping.",
                        title,
                        collection_names,
                    )
                else:
                    self.add_reference_to_notion(reference, collection_names)


# Temporary main function for testing
if __name__ == "__main__":
    from zotero_notion_sync import config

    # Create an instance of the ZoteroToNotion class with dependency injection
    zotero_to_notion = ZoteroToNotion(config)

    # zotero_to_notion.fetch_zotero_reference()

    # zotero_to_notion.fetch_collections()

    # zotero_to_notion.find_reference_in_notion('A Review of the Role of Artificial Intelligence in Healthcare', [])

    # print(zotero_to_notion.notion_headers)
    # result = zotero_to_notion.find_reference_in_notion("AI-Driven Privacy in Elderly Care: Developing a Comprehensive Solution for Camera-Based Monitoring of Older Adults")
    # print(result)

    # references = zotero_to_notion.fetch_zotero_reference()
    # zotero_to_notion.add_reference_to_notion(references[0])
