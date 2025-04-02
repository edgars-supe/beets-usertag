import unittest
from typing import Union

from beetsplug.usertag import UserTagsPlugin
from beets.library import Album, Item, LibModel
from beets.test.helper import TestHelper
from optparse import Values

_ITEM_TAG = 'item_tag'
_ALBUM_TAG = 'album_tag'

def _create_opts(album: bool, tags: [str], prompt: bool=False) -> Values:
    return Values({'album': album, 'tags': tags, 'prompt': prompt})

_ITEM_OPTS = _create_opts(album=False, tags=[_ITEM_TAG])
_ALBUM_OPTS = _create_opts(album=True, tags=[_ALBUM_TAG])

class UserTagsTest(TestHelper, unittest.TestCase):

    def setUp(self):
        super().setup_beets()
        self.subject = UserTagsPlugin()
        self._create_items()

    # region Add

    def test_adding_tag_item(self):
        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=[_ITEM_TAG])

    def test_adding_tag_album(self):
        self.subject.add_tags(self.lib, _ALBUM_OPTS, self.album.album)

        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=[_ALBUM_TAG])

    def test_adding_tag_to_item_does_not_change_album(self):
        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=[_ITEM_TAG])

        album = self.lib.get_album(item)
        self._assert_user_tags(album, expected=[])

    def test_adding_tag_to_album_does_not_change_item(self):
        self.subject.add_tags(self.lib, _ALBUM_OPTS, self.album.album)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=[])

        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=[_ALBUM_TAG])

    def test_adding_tag_item_multiple_times(self):
        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=[_ITEM_TAG])

        self.subject.remove_tags(self.lib, _ITEM_OPTS, self.item.title)

        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)
        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, [_ITEM_TAG])

    def test_invalid_tags_are_stripped_when_adding(self):
        item_opts = _create_opts(
            album=False, tags=['baa', '', 'bab', ' ', 'bac', '   ', 'bad', '\t', 'bae', '	', 'baf'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=['baa', 'bab', 'bac', 'bad', 'bae', 'baf'])

    def test_repeated_tags_are_ignored(self):
        item_opts = _create_opts(album=False, tags=['baa', 'bab', 'baa', 'bac', 'baa'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=['baa', 'bab', 'bac'])

    def test_adding_existing_tags(self):
        item_opts = _create_opts(album=False, tags=['baa', 'bab', 'bac'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)

        item_opts.tags = ['baa', 'bad', 'bae', 'bab']
        self.subject.add_tags(self.lib, item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=['baa', 'bab', 'bac', 'bad', 'bae'])

    # endregion

    # region Remove

    def test_removing_tag_item(self):
        self.subject.add_tags(self.lib, _ITEM_OPTS, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=[_ITEM_TAG])

        self.subject.remove_tags(self.lib, _ITEM_OPTS, self.item.title)
        item = self.lib.get_item(item.id)
        self._assert_user_tags(item, expected=[])

    def test_removing_tag_album(self):
        self.subject.add_tags(self.lib, _ALBUM_OPTS, self.album.album)

        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=[_ALBUM_TAG])

        self.subject.remove_tags(self.lib, _ALBUM_OPTS, self.album.album)
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=[])

    def test_removing_item_tag_does_not_change_album(self):
        item_opts = _create_opts(album=False, tags=['foo'])
        album_opts = _create_opts(album=True, tags=['foo'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)
        self.subject.add_tags(self.lib, album_opts, self.album.album)

        self.subject.remove_tags(self.lib, item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=[])
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=['foo'])

    def test_removing_album_tag_does_not_change_item(self):
        item_opts = _create_opts(album=False, tags=['foo'])
        album_opts = _create_opts(album=True, tags=['foo'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)
        self.subject.add_tags(self.lib, album_opts, self.album.album)

        self.subject.remove_tags(self.lib, album_opts, self.album.album)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=['foo'])
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=[])

    def test_removing_subset(self):
        item_opts = _create_opts(album=False, tags=['baa', 'bab', 'bac', 'bad'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)

        item_opts.tags = ['baa', 'bac']
        self.subject.remove_tags(self.lib, item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=['bab', 'bad'])

    def test_invalid_tags_are_stripped_when_removing(self):
        item_opts = _create_opts(
            album=False,
            tags=['baa', '', 'bab', ' ', 'bac', '   ', 'bad', '\t', 'bae', '	', 'baf'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=['baa', 'bab', 'bac', 'bad', 'bae', 'baf'])

    # endregion

    # region Clear

    def test_clearing_tags_item(self):
        item_opts = _create_opts(album=False, tags=['foo', 'bar'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)

        clear_opts = _create_opts(album=False, tags=[])
        self.subject.clear_tags(self.lib, clear_opts, self.item.title)
        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=[])

    def test_clearing_tags_album(self):
        album_opts = _create_opts(album=True, tags=['foo', 'bar'])
        self.subject.add_tags(self.lib, album_opts, self.album.album)

        clear_opts = _create_opts(album=True, tags=[])
        self.subject.clear_tags(self.lib, clear_opts, self.album.album)
        album = self.lib.get_item(self.album.id)
        self._assert_user_tags(album, expected=[])

    def test_clearing_item_tags_does_not_change_album(self):
        item_opts = _create_opts(album=False, tags=['foo', 'bar'])
        album_opts = _create_opts(album=True, tags=['foo', 'bar'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)
        self.subject.add_tags(self.lib, album_opts, self.album.album)

        clear_opts = _create_opts(album=False, tags=[])
        self.subject.clear_tags(self.lib, clear_opts, self.item.title)
        item = self.lib.get_item(self.item.id)
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(item, expected=[])
        self._assert_user_tags(album, expected=['bar', 'foo'])

    def test_clearing_album_tags_does_not_change_item(self):
        item_opts = _create_opts(album=False, tags=['foo', 'bar'])
        album_opts = _create_opts(album=True, tags=['foo', 'bar'])
        self.subject.add_tags(self.lib, item_opts, self.item.title)
        self.subject.add_tags(self.lib, album_opts, self.album.album)

        clear_opts = _create_opts(album=True, tags=[])
        self.subject.clear_tags(self.lib, clear_opts, self.album.album)
        item = self.lib.get_item(self.item.id)
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(item, expected=['bar', 'foo'])
        self._assert_user_tags(album, expected=[])

    # endregion

    def _create_items(self):
        self.item = self.add_item()
        self.album = self.lib.add_album([self.item])

    def _assert_user_tags(self, model: LibModel, expected: []):
        self.assertEqual(expected, UserTagsPlugin.get_tags(model))