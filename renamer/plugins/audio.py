import string
from functools import partial

try:
    import mutagen
    mutagen # Ssssh, Pyflakes.
except ImportError:
    mutagen = None

from renamer.plugin import RenamerCommand
from renamer.errors import PluginError



class Audio(RenamerCommand):
    name = 'audio'


    description = 'Rename audio files with their metadata.'


    longdesc = """
    Rename audio files based on their own metadata.

    Available placeholders for templates are:

    artist, album, title, date, tracknumber
    """


    defaultPrefixTemplate = string.Template(
        '${artist}/${album} (${date})')


    defaultNameTemplate = string.Template(
        '${tracknumber}. ${title}')


    def postOptions(self):
        if mutagen is None:
            raise PluginError(
                'The "mutagen" package is required for this command')
        super(Audio, self).postOptions()
        self._metadataCache = {}


    def _getMetadata(self, filename):
        """
        Get file metadata.
        """
        if filename not in self._metadataCache:
            self._metadataCache[filename] = mutagen.File(filename)
        return self._metadataCache[filename]


    def getTag(self, path, tagNames, default=u'UNKNOWN'):
        """
        Get a metadata field by name.

        @type filename: L{twisted.python.filepath.FilePath}

        @type tagNames: C{list} of C{unicode}
        @param tagNames: A C{|} separated list of tag names to attempt when
            retrieving a value, the first successful result is returned

        @return: Tag value as C{unicode} or C{default}
        """
        md = self._getMetadata(path.path)
        for tagName in tagNames:
            try:
                return unicode(md[tagName][0])
            except KeyError:
                pass

        return default

    def _saneTracknumber(self, tracknumber):
        if u'/' in tracknumber:
            tracknumber = tracknumber.split(u'/')[0]
        return int(tracknumber)


    # IRenamerCommand

    def processArgument(self, arg):
        T = partial(self.getTag, arg)
        return dict(
            artist=T([u'artist', u'TPE1']),
            album=T([u'album', u'TALB']),
            title=T([u'title', u'TIT2']),
            date=T([u'date', u'year', u'TDRC']),
            tracknumber=self._saneTracknumber(T([u'tracknumber', u'TRCK'])))
