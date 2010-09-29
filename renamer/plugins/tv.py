import os
import string
import urllib

from twisted.web.client import getPage
from twisted.python.filepath import FilePath

from renamer.plugin import RenamerCommand

try:
    import pyparsing
    from pyparsing import (
        alphanums, nums, Word, Literal, ParseException, SkipTo, FollowedBy,
        ZeroOrMore, Combine, NotAny, Optional, StringEnd)
    pyparsing # Ssssh, Pyflakes.
except ImportError:
    pyparsing = None

from renamer.errors import PluginError



DEFAULT_NAME_FORMAT = string.Template(
    '$series [${season}x${padded_episode}] - $title')



class TVRage(RenamerCommand):
    name = 'tvrage'

    description = 'TV episode renamer'

    longdesc = """
    Extract TV episode information from filenames and rename them based on the
    correct information from TV Rage <http://tvrage.com/>.
    """

    optParameters = [
        ('prefix', 'p', None,
         'Formatted path to prefix to files before renaming', string.Template),
        ('name',   'n', None,
         'Formatted filename', string.Template)]


    def _createParser(self):
        """
        Create the filename parser.
        """
        if pyparsing is None:
            raise PluginError(
                'The "pyparsing" package is required for this command')

        def L(value):
            return Literal(value).suppress()

        number = Word(nums)
        digit = Word(nums, exact=1)

        separator = ( Literal('_-_')
                    | Literal(' - ')
                    | Literal('.-.')
                    | Literal('-')
                    | Literal('.')
                    | Literal('_')
                    | Literal(' '))
        separator = separator.suppress().leaveWhitespace()

        season = number.setResultsName('season')
        exact_season = Word(nums, exact=2).setResultsName('season')
        short_season = digit.setResultsName('season')
        epnum = number.setResultsName('ep')
        exact_epnum = Word(nums, exact=2).setResultsName('ep')
        episode = ( season + L('x') + epnum
                  | L('[') + season + L('x') + epnum + L(']')
                  | L('S') + season + L('E') + epnum
                  | L('s') + season + L('e') + epnum
                  | exact_season + exact_epnum
                  | short_season + exact_epnum)

        series_word = Word(alphanums)
        series = ZeroOrMore(
            series_word + separator + NotAny(episode + separator)) + series_word
        series = Combine(series, joinString=' ').setResultsName('series_name')

        extension = '.' + Word(alphanums).setResultsName('ext') + StringEnd()

        title = SkipTo(FollowedBy(extension))

        return (series + separator + episode + Optional(separator + title) +
                extension)


    def postOptions(self):
        super(TVRage, self).postOptions()
        self.filenameParser = self._createParser()
        # Handle the default value.
        if self['name'] is None:
            self['name'] = DEFAULT_NAME_FORMAT


    def buildPath(self, (seriesName, season, episode, episodeName), arg):
        mapping = dict(
            series=seriesName,
            season=season,
            padded_season=u'%02d' % (season,),
            episode=episode,
            padded_episode=u'%02d' % (episode,),
            title=episodeName)

        prefix = self.get('prefix')
        if prefix is not None:
            prefix = prefix.safe_substitute(mapping)
        else:
            prefix = arg.dirname()

        prefix = os.path.expanduser(prefix)
        filename = self['name'].safe_substitute(mapping)
        ext = arg.splitext()[-1]
        return FilePath(prefix).child(filename).siblingExtension(ext)


    def processArgument(self, renamer, arg):
        # XXX: why does our pattern care about the extension?
        seriesName, season, episode, ext = self.extractParts(arg.basename())
        fqe = '%dx%02d' % (int(season), int(episode))
        d = self.lookupMetadata(seriesName, fqe)
        d.addCallback(self.buildPath, arg)
        return d


    def extractParts(self, filename):
        """
        Get TV episode information from a filename.
        """
        try:
            parse = self.filenameParser.parseString(filename)
        except ParseException, e:
            raise PluginError(
                'No patterns could be found in %r (%r)' % (filename, e))
        else:
            return parse.series_name, parse.season, parse.ep, parse.ext


    def lookupMetadata(self, seriesName, episode):
        """
        Look up TV episode metadata on TV Rage.
        """
        qs = urllib.urlencode({'show': seriesName, 'ep': episode})
        url = 'http://services.tvrage.com/tools/quickinfo.php?%s' % (qs,)

        def getParams(page):
            data = {}
            for line in page.splitlines():
                key, value = line.strip().split('@', 1)
                data[key] = value.split('^')

            showName = data['Show Name'][0]
            season, epNumber = map(int, data['Episode Info'][0].split('x'))
            epName = data['Episode Info'][1]
            return showName, season, epNumber, epName

        return getPage(url).addCallback(getParams)
