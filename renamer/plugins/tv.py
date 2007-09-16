import re
import urllib
from string import printable

from BeautifulSoup import BeautifulSoup

from pyparsing import (alphanums, nums, Word, Literal, ParseException, SkipTo,
    FollowedBy, ZeroOrMore, Combine, NotAny, Optional, StringStart, StringEnd)

from renamer import plugins

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

filename = series + separator + episode + Optional(separator + title) + extension


@plugins.command
def find_tv_parts(env, src):
    try:
        parse = filename.parseString(src)
    except ParseException, e:
        raise plugins.PluginError('No patterns could be found in %r (%r)' % (src, e))
    else:
        return parse.series_name, parse.season, parse.ep, parse.ext

_epg_cache = {}

@plugins.command
def epguides(env, key, urlSegment):
    URL = 'http://epguides.com/'
    url = URL + urlSegment.replace(' ', '')

    def gatherKeys(url):
        epKeyExpr = re.compile(r'\s+(?:\d+\.)?\s+(?P<key>[\dSP]-(?:(?: \d)|(?:\d{2})))(?:\s+)?\d+')
        soup = BeautifulSoup(urllib.urlopen(url))
        keys = {}
        contents = soup.pre.contents

        while contents:
            line = contents[0]
            if isinstance(line, basestring):
                match = epKeyExpr.search(line)
                if match:
                    key = match.groupdict()['key'].lower()
                    contents.pop(0)
                    keys[key] = contents[0].contents[0]

            contents.pop(0)

        return keys

    keys = _epg_cache.get(url, None)
    if keys is None:
        keys = _epg_cache[url] = gatherKeys(url)

    key = key.lower()
    try:
        return keys[key]
    except KeyError:
        if key == '1- 1':
            return keys['p- 1']
        else:
            raise

@plugins.command
def tvrage(env, key, showName):
    qs = urllib.urlencode([('show', showName), ('ep', key)])
    url = 'http://www.tvrage.com/quickinfo.php?%s' % (qs,)

    data = {}

    for line in urllib.urlopen(url):
        key, value = line.strip().split('@', 1)
        data[key] = value.split('^')

    return data['Episode Info'][1]
