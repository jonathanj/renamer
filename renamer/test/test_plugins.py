from twisted.trial.unittest import TestCase

from renamer.plugins.tv import find_tv_parts

class TVTests(TestCase):
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
        ('ReGenesis - 1x13.avi', 'ReGenesis', '1', '13', 'avi'),
        ]

    def test_parts(self):
        for case in self.cases:
            self.assertEqual(find_tv_parts(None, case[0]), case[1:])
