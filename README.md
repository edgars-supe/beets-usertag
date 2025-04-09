# Usertag

A plugin for [beets](https://github.com/beetbox/beets) that provides the ability
to add custom tags for individual tracks and albums. Big thanks to
[igordetigor](https://github.com/igordertigor) for the original implementation!

This can be used to add additional metadata to your tracks and albums to help
categorize your music. For example, adding a tag for albums that you have not
listened to yet:

`beet addtag  -a Dire Straits Brothers In Arms -t listen`

And then, when you want to listen to something new, you can list them like this:

`beet ls -a usertags:listen`

Note that this metadata is not added to the actual files as tags, it only exists
in beets' database.

## Installation

First, install the package with `pip`:

```
pip install beets-usertag
```

Then, add `usertag` to the list of plugins in beets' `config.yaml` file. This is
described in more detail in the [beets documentation](https://beets.readthedocs.io/en/latest/plugins/index.html#using-plugins).

## Configuration

First, add the plugin to your beets configuration file.

```
plugins: [..] usertags
```

Then, add the configuration block. This is only required if you want to automatically add tags on import. The commands
will work regardless of the settings here.

```
usertag:
    auto: yes
    album_tags: foo bar
    item_tags: baz bax
```

The options are as follows:
* `auto` - whether to add tags to albums and tracks on import. Possible values: `yes`, `no`. Default: `no`.
* `album_tags` - list of tags to add to albums. Default: none.
* `item_tags` - list of tags to add to items (tracks). These will be added to individual items in albums as well as
     singleton items. Default: none.

## Usage

### Adding tags

```
beet addtag <query> -t <tag> [-t <other-tag>]
```

| Flag                      | Description                                                                                             |
|---------------------------|---------------------------------------------------------------------------------------------------------|
| `-t <tag>`, `--tag <tag>` | Tag(s) to add to items matching the given query. Additional tags require new flags.                     |
| `-a`, `--album`           | (Optional) Whether the query should match albums instead of tracks. Tracks will not be changed.         |
| `-p`, `--prompt`          | (Optional) If set, you will be shown the list of items that will be changed and asked for confirmation. |
| `-i`, `--inherit`         | (Optional) Used only if `-a` is set. If set, tags will be added to the album's items as well.           | 

This command also has an alias - `adt`.

### Removing tags

```
beet rmtag <query> -t <tag> [-t <other-tag>]
```

| Flag                      | Description                                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------|
| `-t <tag>`, `--tag <tag>` | Tag(s) to remove from items matching the given query. Additional tags require new flags.                    |
| `-a`, `--album`           | (Optional) Whether the query should match albums instead of tracks. Tracks will not be changed.             |
| `-p`, `--prompt`          | (Optional) If set, you will be shown the list of items that will be changed and asked for confirmation.     |
| `-i`, `--inherit`         | (Optional) Used only if `-a` is set. If set, the given tags will be removed from the album's items as well. |

This command also has an alias - `rmt`.

---

```
beet cleartags [-a] <query>
```

This command removes all tags on items/albums that match the given query.

| Flag                      | Description                                                                                             |
|---------------------------|---------------------------------------------------------------------------------------------------------|
| `-a`, `--album`           | (Optional) Whether the query should match albums instead of tracks. Tracks will not be changed.         |
| `-p`, `--prompt`          | (Optional) If set, you will be shown the list of items that will be changed and asked for confirmation. |

### Listing tags

```
beet listtags [-a] <query>
```

| Flag                      | Description                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------|
| `-a`, `--album`           | (Optional) Whether the query should match albums instead of tracks. Tracks will not be changed. |

Lists all user-defined tags added to the items matching the given query and the number of items that have each tag.

```
> beet listtags Artist
foo 1
bar 5
```

The output means that out of the tracks matching the query `Artist` one has the tag `foo` and five tracks have the tag
`bar`.

This command also has an alias - `lst`.

---

```
beet list [-a] usertags:<tag>
```

Query user tags as you would query any other field with the standard `list`
command. This will list all tracks/albums that have the given tag set. Add the `-a` flag to list user-tagged albums.

---

```
beet list <query> -f '$title - $usertags'
```

Using `list` like this will return the tracks matching `query` and print out their titles and the usertags that have
been set on them.
