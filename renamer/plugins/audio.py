import mutagen

from zope.interface import classProvides

from twisted.plugin import IPlugin

from renamer.irenamer import IRenamerPlugin
from renamer.plugin import Plugin, command


class Audio(Plugin):
    classProvides(IPlugin, IRenamerPlugin)

    name = 'audio'

    def __init__(self, **kw):
        super(Audio, self).__init__(**kw)
        self.tagCache = {}

    def _getTag(self, filename, tagNames, default=None):
        """
        Get a metadata field by name.

        @type filename: C{str} or C{unicode}

        @type tagNames: C{str} or C{unicode}
        @param tagNames: A C{|} separated list of tag names to attempt when
            retrieving a value, the first successful result is returned

        @return: Tag value or C{default}
        """
        if filename not in self.tagCache:
            self.tagCache[filename] = mutagen.File(filename)

        tagNames = tagNames.split('|')
        for tagName in tagNames:
            try:
                return self.tagCache[filename][tag][0]
            except KeyError:
                pass

        return default

    @command
    def tags(self, filename, tagNames, default):
        """
        Retrieve a list of tag values.

        Multiple tags may be specified by delimiting the names with ",".
        Alternate tag names for a particular tag may be delimited with "|".

        For example: "title|TIT2,album" would retrieve a tag named "title"
        (or "TIT2" if "title" didn't exist) and then a tag named "album".
        """
        return [self._getTag(filename, tagName.strip(), default)
                for tagName in tagNames.split(',')]
