import sys

from twisted.trial.unittest import TestCase

from renamer import plugin



class RenamerCommandTests(TestCase):
    """
    Tests for Renamer command mixins in L{renamer.plugin}.
    """
    def test_decodeCommandLine(self):
        """
        L{renamer.plugin.RenamerSubCommandMixin.decodeCommandLine} turns a byte
        string from the command line into a unicode string.
        """
        decodeCommandLine = plugin.RenamerSubCommandMixin().decodeCommandLine

        class MockFile(object):
            pass

        mf = MockFile()
        self.patch(sys, 'stdin', mf)

        mf.encoding = 'utf-8'
        self.assertEquals(
            decodeCommandLine(u'\u263a'.encode('utf-8')),
            u'\u263a')

        mf.encoding = None
        self.assertEquals(
            decodeCommandLine(u'hello'.encode(sys.getdefaultencoding())),
            u'hello')
