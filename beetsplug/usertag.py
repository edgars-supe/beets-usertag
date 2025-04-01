"""
UserTags is a plugin for beets that allows users to mark songs in their library
by personalized tags. These usertags can in turn be used to filter the library
and as a form of virtual folder system.

The UserTags plugin defines a flexible attribute "usertags" for beets items.
usertags can be added from the command line interface by

beet addtag <id> <usertag>[|<usertag>]

Individual tags can be removed in a similar way by

beet rmtag <id> <usertag>

Removing multiple tags is currently not supported.

Filtering the library by tag works in the exact same way as with other fields:

beet ls usertags:<filtertag>

copyright 2015 by Ingo Fruend (github@ingofruend.net)
"""
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from beets.library import LibModel, Item, Album, Library

from beets.plugins import BeetsPlugin
from beets.ui import Subcommand
from beets.dbcore import types

def clear_usertags(lib, opts, args):
    """Clear all usertags"""
    items = _get_items(lib, opts, args)
    for item in items:
        item.update({'usertags': None})
        if isinstance(item, Item):
            item.store()
        elif isinstance(item, Album):
            item.store(inherit=False)
clear_tags_command = Subcommand('cleartags',
                                help='remove ALL user-defined tags from tracks')
clear_tags_command.parser.add_option(
    '--album', '-a',
    action='store_true', default=False,
    dest='album', help='remove user-defined tags from albums'
)
clear_tags_command.func = clear_usertags


def list_usertags(lib, opts, args):
    items = _get_items(lib, opts, args)
    alltags = []
    for item in items:
        usertags = item.get('usertags', None)
        if usertags:
            alltags += usertags.split('|')
    for tag in sorted(set(alltags)):
        print(tag, len([True for t in alltags if t == tag]))
list_tags_command = Subcommand('listtags',
                               help='list all user-defined tags on tracks',
                               aliases=('lst',))
list_tags_command.parser.add_option(
    '--album', '-a',
    action='store_true', default=False,
    dest='album', help='list all user-defined tags on albums'
)
list_tags_command.func = list_usertags


def _get_items(lib, opts, args) -> [LibModel]:
    if opts.album:
        return lib.albums(args)
    else:
        return lib.items(args)


class UserTagsPlugin(BeetsPlugin):
    """UserTags plugin to support user defined tags"""
    FIELD = 'usertags'
    item_types = {'usertags': types.STRING}

    def __init__(self):
        super(UserTagsPlugin, self).__init__()

    def commands(self):
        return [self._create_add_command(),
                self._create_remove_command(),
                clear_tags_command,
                list_tags_command]

    def add_tags(self, lib, opts, args):
        models = self._get_models(lib, opts.album, args)
        new_tags = self._sanitize_tags(opts.tags)
        print("Adding tag(s) {} to:".format(', '.join(new_tags)))
        for model in models:
            tags = self._get_tags(model)
            tags.extend(new_tags)
            tags = sorted(list(set(tags)))
            model.update({UserTagsPlugin.FIELD: '|'.join(tags)})
            self._update_model(model)
            print("\t{}".format(model))

    def remove_tags(self, lib, opts, args):
        models = self._get_models(lib, opts.album, args)
        remove_tags: [str] = self._sanitize_tags(opts.tags)
        print("Removing tag(s) {} from:".format(', '.join(remove_tags)))
        for model in models:
            tags = self._get_tags(model)
            tags = [tag for tag in tags if tag not in remove_tags]
            tags_field = '|'.join(tags) if tags else None
            model.update({UserTagsPlugin.FIELD: tags_field})
            self._update_model(model)
            print('\t{}'.format(model))

    def _create_add_command(self):
        cmd = Subcommand(
            'addtag',
            help='add user-defined tags',
            aliases='adt')
        cmd.func = self.add_tags
        cmd.parser.add_option(
            '--tag', '-t',
            action='append', dest='tags',
            help='tag to add; one tag per flag')
        cmd.parser.add_option(
            '--album', '-a',
            action='store_true', default=False,
            dest='album', help='tag only albums'
        )
        return cmd

    def _create_remove_command(self):
        cmd = Subcommand(
            'rmtag',
            help='remove user-defined tags',
            aliases='rmt')
        cmd.func = self.remove_tags
        cmd.parser.add_option(
            '--tag', '-t',
            action='append', dest='tags',
            help='tag to remove; one tag per flag')
        cmd.parser.add_option(
            '--album', '-a',
            action='store_true', default=False,
            dest='album', help='remove tag only from albums'
        )
        return cmd

    @staticmethod
    def _get_models(lib: Library, album: bool, args: [str]) -> [LibModel]:
        if album:
            return lib.albums(args)
        else:
            return lib.items(args)

    @staticmethod
    def _update_model(model: LibModel) -> None:
        if isinstance(model, Item):
            model.store()
        elif isinstance(model, Album):
            model.store(inherit=False)

    def _get_tags(self, model: LibModel) -> [str]:
        tags = model.get(self.FIELD, None)
        return tags.split('|') if tags else []

    @staticmethod
    def _sanitize_tags(tags: [str]) -> [str]:
        return [tag for tag in tags if UserTagsPlugin._is_tag_valid(tag)]

    @staticmethod
    def _is_tag_valid(tag: str) -> bool:
        return bool(tag.strip())