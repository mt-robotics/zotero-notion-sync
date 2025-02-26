from zotero_notion_sync.decorators import validate_reference_with_key
from zotero_notion_sync.zotero_to_notion import ZoteroToNotion
from zotero_notion_sync import config

zotero_to_notion = ZoteroToNotion(config)

references = zotero_to_notion.fetch_zotero_reference()


class TestClass:
    @validate_reference_with_key()
    def test_function(self, reference):
        print("Test function called with reference:", reference)


test_class = TestClass()
test_class.test_function(references[0])
