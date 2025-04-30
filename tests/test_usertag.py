import unittest

import beets

from beetsplug.usertag import UserTagsPlugin
from beets.library import LibModel, Library
from beets.test.helper import TestHelper
from optparse import Values
from unittest.mock import patch

_ITEM_TAG = 'item_tag'
_ALBUM_TAG = 'album_tag'

def _create_opts(album: bool, tags: list[str], prompt: bool=False, inherit: bool=False) -> Values:
    return Values({'album': album, 'tags': tags, 'prompt': prompt, 'inherit': inherit})

_ITEM_OPTS = _create_opts(album=False, tags=[_ITEM_TAG])
_ITEM_OPTS_PROMPT = _create_opts(album=False, tags=[_ITEM_TAG], prompt=True)
_ALBUM_OPTS = _create_opts(album=True, tags=[_ALBUM_TAG])

def with_item_tags(*tags: str):
    def decorator(func):
        func._item_tags = list(tags)
        return func
    return decorator

def with_album_tags(*tags: str):
    def decorator(func):
        func._album_tags = list(tags)
        return func
    return decorator

class UserTagsTest(TestHelper, unittest.TestCase):

    def setUp(self):
        super().setup_beets()
        self.subject = UserTagsPlugin()
        self._create_items()
        test_method = getattr(self, self._testMethodName)
        item_tags = getattr(test_method, "_item_tags", None)
        if item_tags:
            self.subject._add_tags(self.item, item_tags)
        album_tags = getattr(test_method, "_album_tags", None)
        if album_tags:
            self.subject._add_tags(self.album, album_tags)

    # region Add

    def test_adding_tag_item(self):
        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)
        self._assert_item_tags(expected=[_ITEM_TAG])

    def test_adding_tag_album(self):
        self.subject.add_tags(self.lib, _ALBUM_OPTS, self.album.album)
        self._assert_album_tags(expected=[_ALBUM_TAG])

    def test_adding_tag_to_item_does_not_change_album(self):
        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)
        self._assert_item_tags(expected=[_ITEM_TAG])
        self._assert_album_tags(expected=[])

    def test_adding_tag_to_album_does_not_change_item(self):
        self.subject.add_tags(self.lib, _ALBUM_OPTS, self.album.album)
        self._assert_item_tags(expected=[])
        self._assert_album_tags(expected=[_ALBUM_TAG])

    def test_adding_tag_to_album_updates_items_when_inherit(self):
        opts = _create_opts(album=True, tags=[_ALBUM_TAG], inherit=True)
        self.subject.add_tags(self.lib, opts, self.album.album)
        self._assert_item_tags(expected=[_ALBUM_TAG])
        self._assert_album_tags(expected=[_ALBUM_TAG])

    @with_item_tags('baa', 'bab')
    def test_adding_tag_to_album_with_inherit_does_not_change_other_tags_on_item(self):
        opts = _create_opts(album=True, tags=[_ALBUM_TAG], inherit=True)
        self.subject.add_tags(self.lib, opts, self.album.album)
        self._assert_item_tags(expected=[_ALBUM_TAG, 'baa', 'bab'])
        self._assert_album_tags(expected=[_ALBUM_TAG])

    def test_adding_tag_item_multiple_times(self):
        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)
        self._assert_item_tags(expected=[_ITEM_TAG])

        self.subject.remove_tags(self.lib, _ITEM_OPTS, self.item.title)

        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)
        self._assert_item_tags(expected=[_ITEM_TAG])

    def test_invalid_tags_are_stripped_when_adding(self):
        item_opts = _create_opts(
            album=False, tags=['baa', '', 'bab', ' ', 'bac', '   ', 'bad', '\t', 'bae', '	', 'baf'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)
        self._assert_item_tags(expected=['baa', 'bab', 'bac', 'bad', 'bae', 'baf'])

    def test_repeated_tags_are_ignored(self):
        item_opts = _create_opts(album=False, tags=['baa', 'bab', 'baa', 'bac', 'baa'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)
        self._assert_item_tags(expected=['baa', 'bab', 'bac'])

    @with_item_tags('baa', 'bab', 'bac')
    def test_adding_existing_tags(self):
        item_opts = _create_opts(album=False, tags=['baa', 'bad', 'bae', 'bab'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)
        self._assert_item_tags(expected=['baa', 'bab', 'bac', 'bad', 'bae'])

    @patch('beets.ui.input_yn', return_value=True)
    def test_adding_prompt_yes(self, mock):
        self.subject.add_tags(self.lib, _ITEM_OPTS_PROMPT, self.item.title)
        self._assert_item_tags(expected=[_ITEM_TAG])

    @patch('beets.ui.input_yn', return_value=False)
    def test_adding_prompt_no(self, mock):
        self.subject.add_tags(self.lib, _ITEM_OPTS_PROMPT, self.item.title)
        self._assert_item_tags(expected=[])

    @patch.object(Library, 'items')
    def test_check_valid_tags_when_adding(self, mock_items_query):
        item_opts = _create_opts(album=False, tags=['', ' ', '   ', '\t', '	'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)
        mock_items_query.assert_not_called()

    def test_adding_tag_twice(self):
        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)
        self._assert_item_tags(expected=[_ITEM_TAG])

        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)
        self._assert_item_tags(expected=[_ITEM_TAG])

    # endregion

    # region Remove

    @with_item_tags(_ITEM_TAG)
    def test_removing_tag_item(self):
        self.subject.remove_tags(self.lib, _ITEM_OPTS, self.item.title)
        self._assert_item_tags(expected=[])

    @with_album_tags(_ALBUM_TAG)
    def test_removing_tag_album(self):
        self.subject.remove_tags(self.lib, _ALBUM_OPTS, self.album.album)
        self._assert_album_tags(expected=[])

    @with_item_tags('foo')
    @with_album_tags('foo')
    def test_removing_item_tag_does_not_change_album(self):
        item_opts = _create_opts(album=False, tags=['foo'])
        self.subject.remove_tags(self.lib, item_opts, self.item.title)

        self._assert_item_tags(expected=[])
        self._assert_album_tags(expected=['foo'])

    @with_item_tags('foo')
    @with_album_tags('foo')
    def test_removing_album_tag_does_not_change_item(self):
        album_opts = _create_opts(album=True, tags=['foo'])
        self.subject.remove_tags(self.lib, album_opts, self.album.album)

        self._assert_item_tags(expected=['foo'])
        self._assert_album_tags(expected=[])

    @with_item_tags('baa', 'bab')
    @with_album_tags('baa', 'bab')
    def test_removing_tag_from_album_updates_items_when_inherit(self):
        opts = _create_opts(album=True, tags=['baa', 'bab'], inherit=True)
        self.subject.remove_tags(self.lib, opts, self.album.album)
        self._assert_item_tags(expected=[])
        self._assert_album_tags(expected=[])

    @with_item_tags('baa', 'bab', 'bac')
    @with_album_tags('baa', 'bab')
    def test_removing_tag_from_album_with_inherit_does_not_change_other_tags_on_item(self):
        opts = _create_opts(album=True, tags=['bab'], inherit=True)
        self.subject.remove_tags(self.lib, opts, self.album.album)
        self._assert_item_tags(expected=['baa', 'bac'])
        self._assert_album_tags(expected=['baa'])

    @with_item_tags('baa', 'bab', 'bac', 'bad')
    def test_removing_subset(self):
        item_opts = _create_opts(album=False, tags=['baa', 'bac'])
        self.subject.remove_tags(self.lib, item_opts, self.item.title)

        self._assert_item_tags(expected=['bab', 'bad'])

    @with_item_tags('baa', 'bab', 'bac', 'bad', 'bae', 'baf')
    def test_invalid_tags_are_stripped_when_removing(self):
        item_opts = _create_opts(
            album=False,
            tags=['baa', '', 'bab', ' ', 'bac', '   ', 'bad', '\t', 'bae', '	', 'baf'])
        self.subject.remove_tags(self.lib, item_opts, self.item.title)

        self._assert_item_tags(expected=[])

    @with_item_tags(_ITEM_TAG)
    @patch('beets.ui.input_yn', return_value=True)
    def test_removing_prompt_yes(self, mock):
        self.subject.remove_tags(self.lib, _ITEM_OPTS_PROMPT, self.item.title)
        self._assert_item_tags(expected=[])

    @with_item_tags(_ITEM_TAG)
    @patch('beets.ui.input_yn', return_value=False)
    def test_removing_prompt_no(self, mock):
        self.subject.remove_tags(self.lib, _ITEM_OPTS_PROMPT, self.item.title)
        self._assert_item_tags(expected=[_ITEM_TAG])

    @patch.object(Library, 'items')
    def test_check_valid_tags_when_removing(self, mock_items_query):
        item_opts = _create_opts(album=False, tags=['', ' ', '   ', '\t', '	'])
        self.subject.remove_tags(self.lib, item_opts, self.item.title)
        mock_items_query.assert_not_called()

    # endregion

    # region Clear

    @with_item_tags('foo', 'bar')
    def test_clearing_tags_item(self):
        clear_opts = _create_opts(album=False, tags=[])
        self.subject.clear_tags(self.lib, clear_opts, self.item.title)
        self._assert_item_tags(expected=[])

    @with_album_tags('foo', 'bar')
    def test_clearing_tags_album(self):
        clear_opts = _create_opts(album=True, tags=[])
        self.subject.clear_tags(self.lib, clear_opts, self.album.album)
        self._assert_album_tags(expected=[])

    @with_item_tags('foo', 'bar')
    @with_album_tags('foo', 'bar')
    def test_clearing_item_tags_does_not_change_album(self):
        clear_opts = _create_opts(album=False, tags=[])
        self.subject.clear_tags(self.lib, clear_opts, self.item.title)
        self._assert_item_tags(expected=[])
        self._assert_album_tags(expected=['bar', 'foo'])

    @with_item_tags('foo', 'bar')
    @with_album_tags('foo', 'bar')
    def test_clearing_album_tags_does_not_change_item(self):
        clear_opts = _create_opts(album=True, tags=[])
        self.subject.clear_tags(self.lib, clear_opts, self.album.album)
        self._assert_item_tags(expected=['bar', 'foo'])
        self._assert_album_tags(expected=[])

    @with_item_tags('foo', 'bar')
    @patch('beets.ui.input_yn', return_value=True)
    def test_clearing_prompt_yes(self, mock):
        clear_opts = _create_opts(album=False, tags=[], prompt=True)
        self.subject.clear_tags(self.lib, clear_opts, self.item.title)
        self._assert_item_tags(expected=[])

    @with_item_tags('foo', 'bar')
    @patch('beets.ui.input_yn', return_value=False)
    def test_clearing_prompt_no(self, mock):
        clear_opts = _create_opts(album=False, tags=[], prompt=True)
        self.subject.clear_tags(self.lib, clear_opts, self.item.title)
        self._assert_item_tags(expected=['bar', 'foo'])

    # endregion

    # region Import

    def test_album_tags_added_on_import(self):
        self._init_config(auto = True, album_tags = ['baa', 'bab'], item_tags = ['bac', 'bad'])
        self.subject._on_album_imported(self.lib, self.album)

        self._assert_album_tags(expected=['baa', 'bab'])

    def test_album_tags_not_added_on_import(self):
        self._init_config(auto = False, album_tags = ['foo'])
        self.subject._on_album_imported(self.lib, self.album)

        self._assert_album_tags(expected=[])

    def test_item_tags_added_on_import(self):
        self._init_config(auto = True, album_tags = ['baa', 'bab'], item_tags = ['bac', 'bad'])
        self.subject._on_item_imported(self.lib, self.item)

        self._assert_item_tags(expected=['bac', 'bad'])

    def test_item_tags_not_added_on_import(self):
        self._init_config(auto=False, item_tags=['foo'])
        self.subject._on_item_imported(self.lib, self.item)

        self._assert_item_tags(expected=[])

    def test_item_tags_added_when_album_imported(self):
        self._init_config(auto = True, album_tags = ['baa', 'bab'], item_tags = ['bac', 'bad'])
        self.subject._on_album_imported(self.lib, self.album)

        self._assert_item_tags(expected=['bac', 'bad'])

    # endregion

    @staticmethod
    def _init_config(auto: bool, album_tags: list[str] = None, item_tags: list[str] = None):
        beets.config['usertag'].set({'auto': auto, 'album_tags': album_tags or [], 'item_tags': item_tags or []})

    def _create_items(self):
        self.item = self.add_item()
        self.album = self.lib.add_album([self.item])

    def _assert_item_tags(self, expected: list[str]):
        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected)

    def _assert_album_tags(self, expected: list[str]):
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected)

    def _assert_user_tags(self, model: LibModel, expected: list[str]):
        self.assertEqual(expected, UserTagsPlugin.get_tags(model))