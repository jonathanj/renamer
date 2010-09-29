import string
import urllib

from twisted.web.client import getPage

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



class TVRage(RenamerCommand):
    name = 'tvrage'


    description = 'Rename TV episodes with TV Rage metadata.'


    longdesc = """
    Extract TV episode information from filenames and rename them based on the
    correct information from TV Rage <http://tvrage.com/>.

    Available placeholders for templates are:

    series, season, padded_season, episode, padded_episode, title
    """


    defaultNameTemplate = string.Template(
        '$series [${season}x${padded_episode}] - $title')


    def postOptions(self):
        super(TVRage, self).postOptions()
        self.filenameParsers = [self._createParser(strict=True),
                                self._createParser(strict=False)]


    def _createParser(self, strict=False):
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

        strict_episode = ( season + L('x') + epnum
                         | L('[') + season + L('x') + epnum + L(']')
                         | L('S') + season + L('E') + epnum
                         | L('s') + season + L('e') + epnum)

        if strict:
            episode = strict_episode
        else:
            episode = ( strict_episode
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


    def buildMapping(self, (seriesName, season, episode, episodeName)):
        return dict(
            series=seriesName,
            season=season,
            padded_season=u'%02d' % (season,),
            episode=episode,
            padded_episode=u'%02d' % (episode,),
            title=episodeName)


    def extractParts(self, filename):
        """
        Get TV episode information from a filename.
        """
        for parser in self.filenameParsers:
            try:
                parse = parser.parseString(filename)
                return parse.series_name, parse.season, parse.ep, parse.ext
            except ParseException, e:
                pass
        raise PluginError(
            'No patterns could be found in %r (%r)' % (filename, e))


    def lookupMetadata(self, seriesName, season, episode):
        """
        Look up TV episode metadata on TV Rage.
        """
        ep = '%dx%02d' % (int(season), int(episode))
        qs = urllib.urlencode({'show': seriesName, 'ep': ep})
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


    # IRenamerCommand

    def processArgument(self, arg):
        # XXX: why does our pattern care about the extension?
        seriesName, season, episode, ext = self.extractParts(arg.basename())
        d = self.lookupMetadata(seriesName, season, episode)
        d.addCallback(self.buildMapping)
        return d
