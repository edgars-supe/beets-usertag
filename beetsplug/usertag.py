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

from optparse import OptionParser

import beets
from beets.library import LibModel, Item, Album, Library

from beets.plugins import BeetsPlugin
from beets.ui import Subcommand
from beets.dbcore import types


class UserTagsPlugin(BeetsPlugin):
    """UserTags plugin to support user defined tags"""
    FIELD = 'usertags'
    item_types = {'usertags': types.STRING}

    def __init__(self):
        super(UserTagsPlugin, self).__init__()
        self._addtag_cmd = self._create_add_command()
        self._rmtag_cmd = self._create_remove_command()
        self._cleartags_cmd = self._create_clear_command()
        self._listtags_cmd = self._create_list_command()

    def commands(self):
        return [self._addtag_cmd,
                self._rmtag_cmd,
                self._cleartags_cmd,
                self._listtags_cmd]

    @staticmethod
    def get_tags(model: LibModel) -> [str]:
        if isinstance(model, Item):
            tags = model.get(UserTagsPlugin.FIELD, default=None, with_album=False)
        elif isinstance(model, Album):
            tags = model.get(UserTagsPlugin.FIELD, None)
        else:
            tags = None
        return tags.split('|') if tags else []

    def add_tags(self, lib, opts, args):
        new_tags = self._sanitize_tags(opts.tags or [])
        if not new_tags:
            print("Please specify at least one valid tag to add!\n")
            self._addtag_cmd.print_help()
            return

        models = self._get_models(lib, opts.album, args)

        if not self._prompt_if_required(
                opts, models,
                prompt_text="This will add the tag(s) {} to the following {}:"
                        .format(', '.join(new_tags), "album(s)" if opts.album else "track(s)"),
                default_text="Adding tag(s) {} to:".format(', '.join(new_tags))):
            return

        for model in models:
            tags = self.get_tags(model)
            tags.extend(new_tags)
            tags = sorted(list(set(tags)))
            model.update({UserTagsPlugin.FIELD: '|'.join(tags)})
            self._update_model(model)
            if not opts.prompt: print("  {}".format(model))

    def remove_tags(self, lib, opts, args):
        remove_tags: [str] = self._sanitize_tags(opts.tags or [])
        if not remove_tags:
            print("Please specify at least one valid tag to remove!\n")
            self._rmtag_cmd.print_help()
            return

        models = self._get_models(lib, opts.album, args)

        if not self._prompt_if_required(
                opts, models,
                prompt_text="This will remove the tag(s) {} from the following {}:"
                        .format(', '.join(remove_tags), "album(s)" if opts.album else "track(s)"),
                default_text="Removing tag(s) {} from:".format(', '.join(remove_tags))):
            return

        for model in models:
            tags = self.get_tags(model)
            tags = [tag for tag in tags if tag not in remove_tags]
            tags_field = '|'.join(tags) if tags else None
            model.update({UserTagsPlugin.FIELD: tags_field})
            self._update_model(model)
            if not opts.prompt: print('  {}'.format(model))

    def clear_tags(self, lib, opts, args):
        models = self._get_models(lib, opts.album, args)

        if not self._prompt_if_required(
                opts, models,
                prompt_text="This will remove ALL tags from the following {}:"
                        .format("album(s)" if opts.album else "track(s)"),
                default_text="Removing ALL tags from:"):
            return

        for model in models:
            model.update({UserTagsPlugin.FIELD: None})
            self._update_model(model)
            if not opts.prompt: print("  {}".format(model))

    def list_tags(self, lib, opts, args):
        models = self._get_models(lib, opts.album, args)
        tags = []
        for model in models:
            tags += self.get_tags(model)
        for tag in sorted(set(tags)):
            print(tag, len([True for t in tags if t == tag]))

    def _create_add_command(self):
        cmd = Subcommand(
            'addtag',
            help='add user-defined tags',
            aliases='adt')
        cmd.func = self.add_tags
        self._add_tag_option(cmd.parser)
        self._add_prompt_option(cmd.parser)
        cmd.parser.add_album_option()
        return cmd

    def _create_remove_command(self):
        cmd = Subcommand(
            'rmtag',
            help='remove user-defined tags',
            aliases='rmt')
        cmd.func = self.remove_tags
        self._add_tag_option(cmd.parser)
        self._add_prompt_option(cmd.parser)
        cmd.parser.add_album_option()
        return cmd

    def _create_clear_command(self):
        cmd = Subcommand(
            'cleartags',
            help='remove ALL user-defined tags from tracks')
        cmd.func = self.clear_tags
        self._add_prompt_option(cmd.parser)
        cmd.parser.add_album_option()
        return cmd

    def _create_list_command(self):
        cmd = Subcommand(
            'listtags',
            help='list all user-defined tags on tracks',
            aliases='lst')
        cmd.func = self.list_tags
        cmd.parser.add_album_option()
        return cmd

    @staticmethod
    def _add_tag_option(parser: OptionParser):
        parser.add_option(
            '--tag', '-t',
            action='append', dest='tags',
            help='tag to add/remove; one tag per flag')

    @staticmethod
    def _add_prompt_option(parser: OptionParser):
        parser.add_option(
            '--prompt', '-p',
            action='store_true', default=False,
            dest='prompt', help='prompt user for confirmation before making changes'
        )

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

    @staticmethod
    def _sanitize_tags(tags: [str]) -> [str]:
        return [tag for tag in tags if UserTagsPlugin._is_tag_valid(tag)]

    @staticmethod
    def _is_tag_valid(tag: str) -> bool:
        return bool(tag.strip())

    @staticmethod
    def _prompt_if_required(opts, models: [LibModel], prompt_text: str, default_text: str) -> bool:
        if opts.prompt:
            print(prompt_text)
            for model in models:
                print("  {}".format(model))
            if not beets.ui.input_yn("Continue? (Y/n)"):
                return False
        else:
            print(default_text)
        return True