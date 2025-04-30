"""
Copyright 2015 Ingo Fruend (github@ingofruend.net)
"""
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from optparse import OptionParser

import beets
from beets.library import LibModel, Item, Album, Library

from beets.plugins import BeetsPlugin
from beets.ui import Subcommand
from beets.dbcore import types

_DELIMITER = '|'

class UserTagsPlugin(BeetsPlugin):
    """UserTags plugin to support user defined tags"""
    FIELD = 'usertags'
    item_types = {'usertags': types.STRING}
    album_types = {'usertags': types.STRING}

    def __init__(self):
        super(UserTagsPlugin, self).__init__()
        self._addtag_cmd = self._create_add_command()
        self._rmtag_cmd = self._create_remove_command()
        self._cleartags_cmd = self._create_clear_command()
        self._listtags_cmd = self._create_list_command()
        self.config.add({'auto': False, 'album_tags': None, 'item_tags': None})
        self.register_listener('album_imported', self._on_album_imported)
        self.register_listener('item_imported', self._on_item_imported)

    def commands(self):
        return [self._addtag_cmd,
                self._rmtag_cmd,
                self._cleartags_cmd,
                self._listtags_cmd]

    @staticmethod
    def get_tags(model: LibModel) -> list[str]:
        if isinstance(model, Item):
            tags = model.get(UserTagsPlugin.FIELD, default=None, with_album=False)
        elif isinstance(model, Album):
            tags = model.get(UserTagsPlugin.FIELD, None)
        else:
            tags = None
        return tags.split(_DELIMITER) if tags else []

    def add_tags(self, lib, opts, args):
        new_tags = self._sanitize_tags(opts.tags or [])
        if not new_tags:
            self._log.error("Please specify at least one valid tag to add!\n")
            self._addtag_cmd.print_help()
            return

        models = self._get_models(lib, opts.album, args)
        if not self._check_models(models, opts.album): return

        if not self._prompt_if_required(
                opts.prompt, models,
                prompt_text="This will add the tag(s) {} to the following {}:"
                        .format(', '.join(new_tags), "album(s)" if opts.album else "track(s)"),
                default_text="Adding tag(s) {} to:".format(', '.join(new_tags))):
            return

        for model in models:
            self._add_tags(model, new_tags)
            if not opts.prompt: self._log.info("  {}".format(model))
            if opts.inherit and isinstance(model, Album):
                self._log.info(f"Adding tags {new_tags} to items of {model}")
                for item in model.items():
                    self._add_tags(item, new_tags)

    def remove_tags(self, lib, opts, args):
        remove_tags = self._sanitize_tags(opts.tags or [])
        if not remove_tags:
            self._log.warn("Please specify at least one valid tag to remove!\n")
            self._rmtag_cmd.print_help()
            return

        models = self._get_models(lib, opts.album, args)
        if not self._check_models(models, opts.album): return

        if not self._prompt_if_required(
                opts.prompt, models,
                prompt_text="This will remove the tag(s) {} from the following {}:"
                        .format(', '.join(remove_tags), "album(s)" if opts.album else "track(s)"),
                default_text="Removing tag(s) {} from:".format(', '.join(remove_tags))):
            return

        for model in models:
            self._remove_tags(model, remove_tags)
            if not opts.prompt: self._log.info('  {}'.format(model))
            if opts.inherit and isinstance(model, Album):
                self._log.info(f"Removing tags {remove_tags} from items of {model}")
                for item in model.items():
                    self._remove_tags(item, remove_tags)

    def clear_tags(self, lib, opts, args):
        models = self._get_models(lib, opts.album, args)
        if not self._check_models(models, opts.album): return

        if not self._prompt_if_required(
                opts.prompt, models,
                prompt_text="This will remove ALL tags from the following {}:"
                        .format("album(s)" if opts.album else "track(s)"),
                default_text="Removing ALL tags from:"):
            return

        for model in models:
            model.update({UserTagsPlugin.FIELD: None})
            self._update_model(model)
            if not opts.prompt: self._log.info("  {}".format(model))

    def list_tags(self, lib, opts, args):
        models = self._get_models(lib, opts.album, args)
        if not self._check_models(models, opts.album): return

        tags = []
        for model in models:
            tags += self.get_tags(model)
        for tag in sorted(set(tags)):
            print(tag, len([True for t in tags if t == tag]))

    def _create_add_command(self):
        cmd = Subcommand(
            'addtag',
            help='add user-defined tags',
            aliases=('adt',))
        cmd.func = self.add_tags
        self._add_tag_option(cmd.parser)
        self._add_prompt_option(cmd.parser)
        self._add_inherit_option(cmd.parser)
        cmd.parser.add_album_option()
        return cmd

    def _create_remove_command(self):
        cmd = Subcommand(
            'rmtag',
            help='remove user-defined tags',
            aliases=('rmt',))
        cmd.func = self.remove_tags
        self._add_tag_option(cmd.parser)
        self._add_prompt_option(cmd.parser)
        self._add_inherit_option(cmd.parser)
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
            aliases=('lst',))
        cmd.func = self.list_tags
        cmd.parser.add_album_option()
        return cmd

    def _on_album_imported(self, lib: Library, album: Album):
        if not self.config['auto']:
            return
        album_tags = self._sanitize_tags(self.config['album_tags'].as_str_seq())
        if album_tags:
            self._add_tags(album, album_tags)
            self._log.debug("Added tag(s) {} to album on import: {}".format(album_tags, album))
        item_tags = self._sanitize_tags(self.config['item_tags'].as_str_seq())
        if item_tags:
            for item in album.items():
                self._add_tags(item, item_tags)
                self._log.debug("Added tag(s) {} to item on import: {}".format(item_tags, item))

    def _on_item_imported(self, lib: Library, item: Item):
        if not self.config['auto']:
            return
        item_tags = self._sanitize_tags(self.config['item_tags'].as_str_seq())
        if item_tags:
            self._add_tags(item, item_tags)
            self._log.debug("Added tag(s) {} to item on import: {}".format(item_tags, item))

    def _add_tags(self, model: LibModel, new_tags: list[str]):
        tags = self.get_tags(model)
        tags.extend(new_tags)
        tags = sorted(list(set(tags)))
        model.update({UserTagsPlugin.FIELD: _DELIMITER.join(tags)})
        self._update_model(model)

    def _remove_tags(self, model, remove_tags):
        tags = self.get_tags(model)
        tags = [tag for tag in tags if tag not in remove_tags]
        tags_field = _DELIMITER.join(tags) if tags else None
        model.update({UserTagsPlugin.FIELD: tags_field})
        self._update_model(model)

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
    def _add_inherit_option(parser: OptionParser):
        parser.add_option(
            '--inherit', '-i',
            action='store_true', default=False,
            dest='inherit', help='when changing album tags, make the same changes for its items'
        )

    @staticmethod
    def _get_models(lib: Library, album: bool, args: list[str]) -> list[LibModel]:
        if album:
            return list(lib.albums(args))
        else:
            return list(lib.items(args))

    def _check_models(self, models: list[LibModel], album: bool) -> bool:
        if not models:
            self._log.info("Query returned no {}".format("albums" if album else "tracks"))
            return False
        else:
            return True

    @staticmethod
    def _update_model(model: LibModel) -> None:
        if isinstance(model, Item):
            model.store()
        elif isinstance(model, Album):
            model.store(inherit=False)

    @staticmethod
    def _sanitize_tags(tags: list[str]) -> list[str]:
        return [tag for tag in tags if UserTagsPlugin._is_tag_valid(tag)]

    @staticmethod
    def _is_tag_valid(tag: str) -> bool:
        return bool(tag.strip())

    def _prompt_if_required(self, prompt: bool, models: list[LibModel], prompt_text: str, default_text: str) -> bool:
        if prompt:
            self._log.info(prompt_text)
            for model in models:
                self._log.info("  {}".format(model))
            if not beets.ui.input_yn("Continue? (Y/n)"):
                self._log.info("No changes made.")
                return False
        else:
            self._log.info(default_text)
        return True