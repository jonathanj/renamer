import re
import urllib
from BeautifulSoup import BeautifulSoup

from renamer import plugins

@plugins.command
def find_tv_parts(env, src):
    patterns = [
        re.compile(r'(?P<series_name>.*?) - [sS](?P<season>\d+)[eE](?P<ep>\d+) - .*\.(?P<ext>.*?)$'), # Profiler - S01E01 - Insight.avi
        re.compile(r'(?P<series_name>.*?) \[(?P<season>\d+)x(?P<ep>\d{2})\] - .*\.(?P<ext>.*?)$'), # Heroes [1x01] - Genesis.avi
        re.compile(r'(?P<series_name>.*?) [sS](?P<season>\d+)[eE](?P<ep>\d{2}) .*\.(?P<ext>.*?)$'), # Heroes S01E10 HDTV XviD.avi
        re.compile(r'(?P<series_name>.*?)\.(?P<season>\d)(?P<ep>\d{2}).*\.(?P<ext>.*?)$'), # heroes.108.hdtv-lol.avi
        re.compile(r'(?P<series_name>.*?)\.(?P<season>\d)(?P<ep>\d{2})\.(?P<ext>.*?)$'), # arrested.development.302.avi
        re.compile(r'(?P<series_name>.*?)\.[sS](?P<season>\d+)[eE](?P<ep>\d{2}).*\.(?P<ext>.*?)$'), # Heroes.S01E11.HDTV.XviD-K4RM4.avi
        re.compile(r'(?P<series_name>.*?) - (?P<season>\d)(?P<ep>\d{2}).*\.(?P<ext>.*?)$'), # How I Met Your Mother - 101 - Pilot.avi
        re.compile(r'(?P<series_name>.*?)\.[sS](?P<season>\d+)[eE](?P<ep>\d+).*\.(?P<ext>.*?)$'), # 24.s6e4.dvdrip.xvid-aerial.avi
        re.compile(r'(?P<series_name>.*?)\.-\.(?P<season>\d)x(?P<ep>\d{2}).*\.(?P<ext>.*?)$'), # harsh.realm.-.1x01.-.pilot.avi
        re.compile(r'(?P<series_name>.*?)_[sS](?P<season>\d+)[eE](?P<ep>\d+).*\.(?P<ext>.*?)$'), # DayBreak_S01E09.avi
    ]

    for pattern in patterns:
        m = pattern.search(src)
        if m is not None:
            d = m.groupdict()
            return d['series_name'], d['season'], d['ep'], d['ext']

    raise plugins.PluginError('No patterns could be found in %r' % (src))

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
    url = 'http://www.tvrage.com/quickinfo.php?show=%s&ep=%s' % (showName, key)

    data = {}

    for line in urllib.urlopen(url):
        key, value = line.strip().split('@', 1)
        data[key] = value.split('^')

    return data['Episode Info'][1]
