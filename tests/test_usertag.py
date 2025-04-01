import unittest
from typing import Union

from beetsplug.usertag import UserTagsPlugin, clear_usertags, remove_usertag
from beets.library import Album, Item, LibModel
from beets.test.helper import TestHelper
from optparse import Values

class UserTagsTest(TestHelper, unittest.TestCase):
    _ITEMTAG = 'itemtag'
    _ALBUMTAG = 'albumtag'

    item_opts = Values({'album': False, 'tags': [_ITEMTAG]})
    album_opts = Values({'album': True, 'tags': [_ALBUMTAG]})

    def setUp(self):
        super().setup_beets()
        self.subject = UserTagsPlugin()
        self._create_items()

    # region Add

    def test_adding_tag_item(self):
        self.subject.add_tags(self.lib, self.item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, self._ITEMTAG)

    def test_adding_tag_album(self):
        self.subject.add_tags(self.lib, self.album_opts, self.album.album)

        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=self._ALBUMTAG)

    def test_adding_tag_to_item_does_not_change_album(self):
        self.subject.add_tags(self.lib, self.item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=self._ITEMTAG)

        album = self.lib.get_album(item)
        self._assert_user_tags(album, expected=None)

    def test_adding_tag_to_album_does_not_change_item(self):
        self.subject.add_tags(self.lib, self.album_opts, self.album.album)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=None)

        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=self._ALBUMTAG)

    def test_adding_tag_item_multiple_times(self):
        self.subject.add_tags(self.lib, self.item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, self._ITEMTAG)

        remove_usertag(self.lib, self.item_opts, self.item.title)

        self.subject.add_tags(self.lib, self.item_opts, self.item.title)
        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, self._ITEMTAG)

    def test_invalid_tags_are_stripped_when_adding(self):
        _item_opts = Values(
            {'album': False, 'tags': ['baa', '', 'bab', ' ', 'bac', '   ', 'bad', '\t', 'bae', '	', 'baf']})
        self.subject.add_tags(self.lib, _item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected='baa|bab|bac|bad|bae|baf')


    # endregion

    # region Remove

    def test_removing_tag_item(self):
        self.subject.add_tags(self.lib, self.item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=self._ITEMTAG)

        remove_usertag(self.lib, self.item_opts, self.item.title)
        item = self.lib.get_item(item.id)
        self._assert_user_tags(item, expected=None)

    def test_removing_tag_album(self):
        self.subject.add_tags(self.lib, self.album_opts, self.album.album)

        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=self._ALBUMTAG)

        remove_usertag(self.lib, self.album_opts, self.album.album)
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=None)

    def test_removing_item_tag_does_not_change_album(self):
        _item_opts = Values({'album': False, 'tags': ['foo']})
        _album_opts = Values({'album': True, 'tags': ['foo']})
        self.subject.add_tags(self.lib, _item_opts, self.item.title)
        self.subject.add_tags(self.lib, _album_opts, self.album.album)

        remove_usertag(self.lib, _item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=None)
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected='foo')

    def test_removing_album_tag_does_not_change_item(self):
        _item_opts = Values({'album': False, 'tags': ['foo']})
        _album_opts = Values({'album': True, 'tags': ['foo']})
        self.subject.add_tags(self.lib, _item_opts, self.item.title)
        self.subject.add_tags(self.lib, _album_opts, self.album.album)

        remove_usertag(self.lib, _album_opts, self.album.album)

        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected='foo')
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(album, expected=None)

    # endregion

    # region Clear

    def test_clearing_tags_item(self):
        _item_opts = Values({'album': False, 'tags': ['foo', 'bar']})
        self.subject.add_tags(self.lib, _item_opts, self.item.title)

        item = self.lib.get_item(self.item.id)
        self.assertIsNotNone(item.get(UserTagsPlugin.FIELD, default=None))

        _clear_opts = Values({'album': False})
        clear_usertags(self.lib, _clear_opts, self.item.title)
        item = self.lib.get_item(self.item.id)
        self._assert_user_tags(item, expected=None)

    def test_clearing_tags_album(self):
        _album_opts = Values({'album': True, 'tags': ['foo', 'bar']})
        self.subject.add_tags(self.lib, _album_opts, self.album.album)

        album = self.lib.get_album(self.album.id)
        self.assertIsNotNone(album.get(UserTagsPlugin.FIELD, default=None))

        _clear_opts = Values({'album': True})
        clear_usertags(self.lib, _clear_opts, self.album.album)
        album = self.lib.get_item(self.album.id)
        self._assert_user_tags(album, expected=None)

    def test_clearing_item_tags_does_not_change_album(self):
        _item_opts = Values({'album': False, 'tags': ['foo', 'bar']})
        _album_opts = Values({'album': True, 'tags': ['foo', 'bar']})
        self.subject.add_tags(self.lib, _item_opts, self.item.title)
        self.subject.add_tags(self.lib, _album_opts, self.album.album)

        _clear_opts = Values({'album': False})
        clear_usertags(self.lib, _clear_opts, self.item.title)
        item = self.lib.get_item(self.item.id)
        album = self.lib.get_album(self.album.id)
        self._assert_user_tags(item, expected=None)
        self.assertIsNotNone(album.get(UserTagsPlugin.FIELD, default=None))

    def test_clearing_album_tags_does_not_change_item(self):
        _item_opts = Values({'album': False, 'tags': ['foo', 'bar']})
        _album_opts = Values({'album': True, 'tags': ['foo', 'bar']})
        self.subject.add_tags(self.lib, _item_opts, self.item.title)
        self.subject.add_tags(self.lib, _album_opts, self.album.album)

        _clear_opts = Values({'album': True})
        clear_usertags(self.lib, _clear_opts, self.album.album)
        item = self.lib.get_item(self.item.id)
        album = self.lib.get_album(self.album.id)
        self.assertIsNotNone(item.get(UserTagsPlugin.FIELD, default=None))
        self._assert_user_tags(album, expected=None)

    # endregion

    def _create_items(self):
        self.item = self.add_item()
        self.album = self.lib.add_album([self.item])

    def _assert_user_tags(self, item: LibModel, expected: Union[str, None]):
        if isinstance(item, Item):
            self.assertEqual(expected, item.get(UserTagsPlugin.FIELD, default=None, with_album=False))
        elif isinstance(item, Album):
            self.assertEqual(expected, item.get(UserTagsPlugin.FIELD, default=None))