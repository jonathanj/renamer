import string

from twisted.python.filepath import FilePath
from twisted.trial.unittest import TestCase

from renamer import config
from renamer.application import Options



class OptionsTests(TestCase):
    """
    Tests for L{renamer.application.Options}.
    """
    def setUp(self):
        path = FilePath(__file__).sibling('data').child('test.conf')
        self.config = config.ConfigFile(path)
        self.options = Options(self.config)


    def test_parsePrefix(self):
        """
        Prefix options are decoded to C{unicode} before being wrapped in
        C{string.Template}.
        """
        self.options.parseOptions(['--prefix=foo'])
        self.assertIdentical(string.Template, type(self.options['prefix']))
        self.assertIdentical(unicode, type(self.options['prefix'].template))


    def test_parseName(self):
        """
        Name options are decoded to C{unicode} before being wrapped in
        C{string.Template}.
        """
        self.options.parseOptions(['--name=foo'])
        self.assertIdentical(string.Template, type(self.options['name']))
        self.assertIdentical(unicode, type(self.options['name'].template))
