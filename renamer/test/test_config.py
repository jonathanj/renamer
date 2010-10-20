from twisted.python.filepath import FilePath
from twisted.trial.unittest import TestCase

from renamer import config, plugin



class TestCommand(plugin.Command):
    name = 'test'


    optParameters = [
        ('aardvark',  'a', None, 'desc'),
        ('bobcat',    'b', 5,    'desc', int),
        ('chocolate', 'c', None, 'desc')]


    optFlags = [
        ('donut', 'd', 'desc')]



class ConfigTests(TestCase):
    """
    Tests for L{renamer.config}.
    """
    def setUp(self):
        path = FilePath(__file__).sibling('data').child('test.conf')
        self.config = config.ConfigFile(path)


    def test_flag(self):
        """
        L{renamer.config.flag} returns C{True} for true flag values such as
        C{'yes'}, C{'true'}, C{'1'} and otherwise C{False}.
        """
        truths = [
            'yes', u'yes', 'YES', u'true', '1', 1]
        for value in truths:
            self.assertTrue(config.flag(value))

        falsehoods = [
            'no', u'NO', 'arst', 0, []]
        for value in falsehoods:
            self.assertFalse(config.flag(value))


    def test_transformersFromOptions(self):
        """
        L{renamer.config.transformersFromOptions} extracts coercion functions
        from a L{renamer.irenamer.ICommand} provider.
        """
        expected = {
            'aardvark':  config._identity,
            'bobcat':    int,
            'chocolate': config._identity,
            'donut':     config.flag}
        res = dict(config.transformersFromOptions(TestCommand()))
        self.assertEquals(expected, res)


    def test_defaultsFromConfigWrapper(self):
        """
        L{renamer.config.defaultsFromConfigWrapper} creates a wrapper function
        around a L{renamer.irenamer.ICommand} that, when called, instantiates
        the L{renamer.irenamer.ICommand} and sets default values from a config
        file from a section with a name matched
        L{renamer.irenamer.ICommand.name}. Options that are explicitly provided
        to the command trump values from the config file.
        """
        wrapper = config.defaultsFromConfigWrapper(self.config, TestCommand)
        cmd = wrapper()
        cmd.parseOptions([])
        self.assertEquals(cmd['aardvark'], u'hello')
        self.assertEquals(cmd['bobcat'], 3)
        self.assertIdentical(cmd['chocolate'], None)
        self.assertEquals(cmd['donut'], False)

        cmd = wrapper()
        cmd.parseOptions(['--bobcat=7', '--donut'])
        self.assertEquals(cmd['aardvark'], u'hello')
        self.assertEquals(cmd['bobcat'], 7)
        self.assertIdentical(cmd['chocolate'], None)
        self.assertEquals(cmd['donut'], True)



class ConfigFileTests(TestCase):
    """
    Tests for L{renamer.config.ConfigFile}.
    """
    def setUp(self):
        path = FilePath(__file__).sibling('data').child('test.conf')
        self.config = config.ConfigFile(path)


    def test_nonexistentConfig(self):
        """
        Specifying a nonexistent path to L{renamer.config.ConfigFile} results
        in an empty config object.
        """
        conf = config.ConfigFile(FilePath('no_such_config'))
        self.assertEquals(conf.sections, {})


    def test_getNoCoercion(self):
        """
        Getting a config section without specifying an C{'options'} argument
        simply returns a mapping of strings to strings.
        """
        expected = {
            'bar': u'1',
            'baz': u'apple'}
        self.assertEquals(expected, self.config.get('foo'))


    def test_getCoercion(self):
        """
        Specifying an C{'options'} argument when getting a config section will
        coerce recognized options to their corresponding type in the
        C{'options'} argument.
        """
        expected = {
            'aardvark': u'hello',
            'bobcat':   3,
            'donut':    False}
        self.assertEquals(expected, self.config.get('test', TestCommand))
