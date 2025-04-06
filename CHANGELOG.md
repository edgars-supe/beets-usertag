# Changelog

## v1.0.0 - 2025-04-06

### Added

* Added `-p`/`--prompt` flag to `addtag`, `rmtag`, `cleartags` to confirm changes before proceeding. (#4)
* Check if given tags are valid for `addtag` and `rmtag`, will abort if they are not. (#10)
* Display a message if there were no matching entries for the given query. (#10)
* Added the ability to automatically add tags to albums and items on import. See the
  [configuration](README.md#configuration) section of the README for more details. (#5)
* Added extra logs. (#15)
* Added `-i`/`--inherit` flag to perform album tag changes (add/remove) on its items. (#22)

### Fixed

* When tagging albums, it will no longer automatically tag the album's items with the same tags. (#6)