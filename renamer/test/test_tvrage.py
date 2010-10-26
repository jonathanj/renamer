import cgi
import urllib

from twisted.internet.defer import succeed
from twisted.python.filepath import FilePath
from twisted.trial.unittest import TestCase

from renamer import errors
from renamer.plugins import tv



class DummyPluginParent(object):
    """
    Dummy plugin parent.
    """



class TVRageTests(TestCase):
    """
    Tests for L{renamer.plugins.tv.TVRage}.
    """
    cases = [
        ('Profiler - S01E01 - Insight.avi', 'Profiler', '01', '01', 'avi'),
        ('Heroes [1x01] - Genesis.avi', 'Heroes', '1', '01', 'avi'),
        ('Heroes S01E10 HDTV XviD.avi', 'Heroes', '01', '10', 'avi'),
        ('heroes.108.hdtv-lol.avi', 'heroes', '1', '08', 'avi'),
        ('arrested.development.302.avi', 'arrested development', '3', '02', 'avi'),
        ('Heroes.S01E11.HDTV.XviD-K4RM4.avi', 'Heroes', '01', '11', 'avi'),
        ('How I Met Your Mother - 101 - Pilot.avi', 'How I Met Your Mother', '1', '01', 'avi'),
        ('24.s6e4.dvdrip.xvid-aerial.avi', '24', '6', '4', 'avi'),
        ('harsh.realm.-.1x01.-.pilot.avi', 'harsh realm', '1', '01', 'avi'),
        ('DayBreak_S01E09.avi', 'DayBreak', '01', '09', 'avi'),
        ('Xena - 2x05 - Return of Callisto.avi', 'Xena', '2', '05', 'avi'),
        ('Sliders_-_4x22_Revelations_(divx).avi', 'Sliders', '4', '22', 'avi'),
        ('Xena_4x02_Adventures In The Sin Trade - Part 2.avi', 'Xena', '4', '02', 'avi'),
        ('Sliders 501 - The Unstuck Man.avi', 'Sliders', '5', '01', 'avi'),
        ('buffy.2x03.dvdrip.xvid-tns.avi', 'buffy', '2', '03', 'avi'),
        ('the.4400.1x05.avi', 'the 4400', '1', '05', 'avi'),
        ('flash.gordon.2007.s01e02.dvdrip.xvid-reward.avi', 'flash gordon 2007', '01', '02', 'avi'),
        ('Foo - 508 - The cat has 9 lives.avi', 'Foo', '5', '08', 'avi'),
        ('ReGenesis - 1x13.avi', 'ReGenesis', '1', '13', 'avi')]


    def setUp(self):
        self.dataPath = FilePath(__file__).sibling('data')
        self.plugin = tv.TVRage()
        self.plugin.parent = DummyPluginParent()
        self.plugin.postOptions()


    def fetcher(self, url):
        """
        "Fetch" TV rage data.
        """
        data = self.dataPath.child('tvrage').open().read()
        return succeed(data)


    def test_extractParts(self):
        """
        Extracting TV show information from filenames works correctly.
        """
        for case in self.cases:
            self.assertEquals(self.plugin.extractParts(case[0]), case[1:])

        self.assertRaises(errors.PluginError,
            self.plugin.extractParts, 'thiswillnotwork')


    def test_missingPyParsing(self):
        """
        Attempting to use the TV Rage plugin without PyParsing installed raises
        a L{renamer.errors.PluginError}.
        """
        self.patch(tv, 'pyparsing', None)
        plugin = tv.TVRage()
        plugin.parent = DummyPluginParent()
        e = self.assertRaises(errors.PluginError, plugin.postOptions)
        self.assertEquals(
            str(e), 'The "pyparsing" package is required for this command')


    def test_extractMetadata(self):
        """
        L{renamer.plugins.tv.TVRage.extractMetadata} extracts structured TV
        episode information from a TV Rage response.
        """
        d = self.plugin.lookupMetadata('Dexter', 1, 2, fetcher=self.fetcher)

        @d.addCallback
        def checkMetadata((series, season, episode, title)):
            self.assertEquals(series, u'Dexter')
            self.assertEquals(season, 1)
            self.assertEquals(episode, 2)
            self.assertEquals(title, u'Crocodile')

        return d


    def test_lookupMetadata(self):
        """
        L{renamer.plugins.tv.TVRage.lookupMetadata} requests structured TV
        episode information from TV Rage.
        """
        def fetcher(url):
            path, query = urllib.splitquery(url)
            query = cgi.parse_qs(query)
            self.assertEquals(
                query,
                dict(show=['Dexter'], ep=['1x02']))
            return self.fetcher(url)

        return self.plugin.lookupMetadata('Dexter', 1, 2, fetcher=fetcher)
