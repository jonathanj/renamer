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
        self._metadataCache = {}

    def _getMetadata(self, filename):
        """
        Get file metadata.
        """
        if filename not in self._metadataCache:
            self._metadataCache[filename] = mutagen.File(filename)
        return self._metadataCache[filename]

    def _getTag(self, filename, tagNames, default=None):
        """
        Get a metadata field by name.

        @type filename: C{str} or C{unicode}

        @type tagNames: C{str} or C{unicode}
        @param tagNames: A C{|} separated list of tag names to attempt when
            retrieving a value, the first successful result is returned

        @return: Tag value as C{unicode} or C{default}
        """
        md = self._getMetadata(filename)

        tagNames = tagNames.split('|')
        for tagName in tagNames:
            try:
                return unicode(md[tagName][0])
            except KeyError:
                pass

        return default

    @command
    def gettags(self, filename, tagNames, default):
        """
        Retrieve a list of tag values.

        Multiple tags may be specified by delimiting the names with ",".
        Alternate tag names for a particular tag may be delimited with "|".

        For example: "title|TIT2,album" would retrieve a tag named "title"
        (or "TIT2" if "title" didn't exist) and then a tag named "album".
        """
        return [self._getTag(filename, tagName.strip(), default)
                for tagName in tagNames.split(',')]

    _extensions = {
        'audio/x-flac': '.flac'}

    @command
    def extension(self, filename):
        md = self._getMetadata(filename)
        for mimeType in md.mime:
            ext = self._extensions.get(mimeType)
            if ext is not None:
                return ext

        return '.' + md.mime[0].split('/', 1)[1]
