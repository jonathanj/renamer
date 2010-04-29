import urllib

from zope.interface import classProvides

from twisted.plugin import IPlugin
from twisted.web.client import getPage

from renamer.irenamer import IRenamerPlugin
from renamer.plugin import Plugin, command

try:
    import pyparsing
    from pyparsing import (alphanums, nums, Word, Literal, ParseException, SkipTo,
        FollowedBy, ZeroOrMore, Combine, NotAny, Optional, StringEnd)
except ImportError:
    pyparsing = None

from renamer.errors import PluginError
from renamer.util import Replacement, ConditionalReplacer


class TV(Plugin):
    classProvides(IPlugin, IRenamerPlugin)

    name = 'tv'

    def __init__(self, **kw):
        if pyparsing is None:
            raise PluginError('"pyparsing" package is required for this plugin')
        super(TV, self).__init__(**kw)
        self.filename = self._createParser()
        self.repl = {
            'show': Replacement.fromIterable(self.openFile('shownames')),
            'ep':   Replacement.fromIterable(self.openFile('epnames'), ConditionalReplacer)}

    def _createParser(self):
        """
        Create the filename parser.
        """
        def L(value):
            return Literal(value).suppress()

        number = Word(nums)
        digit = Word(nums, exact=1)

        separator = Literal('_-_') | Literal(' - ') | Literal('.-.') | Literal('-') | Literal('.') | Literal('_') | Literal(' ')
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
                  | short_season + exact_epnum
                  )

        series_word = Word(alphanums)
        series = ZeroOrMore(series_word + separator + NotAny(episode + separator)) + series_word
        series = Combine(series, joinString=' ').setResultsName('series_name')

        extension = '.' + Word(alphanums).setResultsName('ext') + StringEnd()

        title = SkipTo(FollowedBy(extension))

        return series + separator + episode + Optional(separator + title) + extension

    @command
    def find_parts(self, src):
        """
        Get TV episode information from a filename.
        """
        try:
            parse = self.filename.parseString(src)
        except ParseException, e:
            raise PluginError('No patterns could be found in %r (%r)' % (src, e))
        else:
            return parse.series_name, parse.season, parse.ep, parse.ext

    @command
    def tvrage(self, key, showName):
        """
        Look up TV episode information on TV Rage.
        """
        qs = urllib.urlencode([('show', showName), ('ep', key)])
        url = 'http://services.tvrage.com/tools/quickinfo.php?%s' % (qs,)

        def getParams(page):
            data = {}
            for line in page.splitlines():
                key, value = line.strip().split('@', 1)
                data[key] = value.split('^')

            showName = self.repl['show'].replace(data['Show Name'][0])
            season, epNumber = map(int, data['Episode Info'][0].split('x'))
            epName = self.repl['ep'].replace(data['Episode Info'][1], showName)

            return showName, season, epNumber, epName

        return getPage(url).addCallback(getParams)
