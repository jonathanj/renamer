import re, urllib
from BeautifulSoup import BeautifulSoup

from zope.interface import classProvides

from twisted.plugin import IPlugin

from renamer.irenamer import IRenamerPlugin
from renamer.plugin import Plugin, command

from pyparsing import (alphanums, nums, Word, Literal, ParseException, SkipTo,
    FollowedBy, ZeroOrMore, Combine, NotAny, Optional, StringStart, StringEnd)

from renamer.errors import PluginError
from renamer.util import Replacer


class TV(Plugin):
    classProvides(IPlugin, IRenamerPlugin)

    name = 'tv'

    def __init__(self, **kw):
        super(TV, self).__init__(**kw)
        self.filename = self._createParser()
        self.replacer = Replacer()

        fd = self.openFile('shownames')
        if fd is not None:
            self.replacer.addFromStrings(fd)
            fd.close()

    def _createParser(self):
        def L(value):
            return Literal(value).suppress()

        number = Word(nums)
        digit = Word(nums, exact=1)

        separator = Literal('_-_') | Literal(' - ') | Literal('.-.') | Literal('-') | Literal('.') | Literal('_') | Literal(' ')
        separator = separator.suppress().leaveWhitespace()

        season = number.setResultsName('season')
        short_season = digit.setResultsName('season')
        epnum = number.setResultsName('ep')
        exact_epnum = Word(nums, exact=2).setResultsName('ep')
        episode = ( season + L('x') + epnum
                  | L('[') + season + L('x') + epnum + L(']')
                  | L('S') + season + L('E') + epnum
                  | L('s') + season + L('e') + epnum
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
        try:
            parse = self.filename.parseString(src)
        except ParseException, e:
            raise PluginError('No patterns could be found in %r (%r)' % (src, e))
        else:
            return parse.series_name, parse.season, parse.ep, parse.ext

    @command
    def tvrage(self, key, showName):
        qs = urllib.urlencode([('show', showName), ('ep', key)])
        url = 'http://www.tvrage.com/quickinfo.php?%s' % (qs,)

        data = {}

        for line in urllib.urlopen(url):
            key, value = line.strip().split('@', 1)
            data[key] = value.split('^')

        showName = self.replacer.replace(data['Show Name'][0])
        season, epNumber = map(int, data['Episode Info'][0].split('x'))
        epName = data['Episode Info'][1]

        return showName, season, epNumber, epName
