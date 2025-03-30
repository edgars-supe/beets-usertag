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
pip install git+https://github.com/edgars-supe/beets-usertag.git
```

Then, add `usertag` to the list of plugins in beets' `config.yaml` file. This is
described in more detail in the [beets documentation](https://beets.readthedocs.io/en/latest/plugins/index.html#using-plugins).

## Usage

### Adding tags

```
beet addtag [-a] <query> -t <usertag> [-t <other-usertag>]
```

Adds one (or more) usertags to the tracks matching the given query. Use the `-a`
flag to tag albums instead. Tracks in the album will not be tagged.

This command also has an alias - `adt`.

### Removing tags

```
beet rmtag [-a] <query> -t <usertag>[ -t <other-usertag>]
```

Removes a usertag from the tracks matching the given query. Use the `-a` flag to
remove a tag from an album. Tracks in the album will not be affected.

This command also has an alias - `rmt`.

```
beet cleartags [-a] <query>
```

Strips all usertags from the tracks matching the given query. Use the `-a` flag
to strip all usertags from matching albums.

### Listing tags

```
beet listtags [-a]
```

Lists all user-defined tags and a count of tracks that used those tags. Use the 
`-a` flag to return user-defined tags and count for albums.

This command also has an alias - `lst`.

```
beet list [-a] usertags:<tag>
```

Query user tags as you would query any other field with the standard `list`
command. Add the `-a` flag to list user-tagged albums.
