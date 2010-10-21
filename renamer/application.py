"""
Renamer application logic.
"""
import itertools
import os
import string
import sys

from axiom.store import Store

from twisted.internet import defer
from twisted.python import usage, log, versions
from twisted.python.filepath import FilePath

from renamer import config, logging, plugin, util, version
from renamer.irenamer import IRenamingCommand
from renamer.history import History



class Options(usage.Options, plugin._CommandMixin):
    optFlags = [
        ('glob',            'g',  'Expand arguments as UNIX-style globs.'),
        ('one-file-system', 'x',  "Don't cross filesystems."),
        ('no-act',          'n',  'Perform a trial run with no changes made.'),
        ('link-src',        None, 'Create a symlink at the source.'),
        ('link-dst',        None, 'Create a symlink at the destination.')]


    optParameters = [
        ('config', 'c', '~/.renamer/renamer.conf',
         'Configuration file path.'),
        ('name',   'e', None,
         'Formatted filename.', string.Template),
        ('prefix', 'p', None,
         'Formatted path to prefix to files before renaming.', string.Template),
        ('concurrent', 'l',  10,
         'Maximum number of asynchronous tasks to perform concurrently.', int)]


    @property
    def subCommands(self):
        commands = itertools.chain(
            plugin.getRenamingCommands(), plugin.getCommands())
        for plg in commands:
            try:
                yield (
                    plg.name,
                    None,
                    config.defaultsFromConfigWrapper(self.config, plg),
                    plg.description)
            except AttributeError:
                raise RuntimeError('Malformed plugin: %r' % (plg,))


    def __init__(self, config):
        super(Options, self).__init__()
        self['verbosity'] = 1
        self.config = config


    @property
    def synopsis(self):
        return 'Usage: %s [options]' % (
            os.path.basename(sys.argv[0]),)


    def opt_verbose(self):
        """
        Increase output, use more times for greater effect.
        """
        self['verbosity'] = self['verbosity'] + 1

    opt_v = opt_verbose


    def opt_quiet(self):
        """
        Suppress output.
        """
        self['verbosity'] = self['verbosity'] - 1

    opt_q = opt_quiet


    def opt_version(self):
        """
        Display version information.
        """
        print versions.getVersionString(version)
        sys.exit(0)


    def parseArgs(self, *args):
        args = (self.decodeCommandLine(arg) for arg in args)
        if self['glob']:
            args = util.globArguments(args)
        self.args = (FilePath(arg) for arg in args)



class Renamer(object):
    """
    Renamer main logic.

    @type store: L{axiom.store.Store}
    @ivar store: Renamer database Store.

    @type history: L{renamer.history.History}
    @ivar history: Renamer history Item.

    @type options: L{renamer.application.Options}
    @ivar options: Parsed command-line options.

    @type command: L{renamer.irenamer.ICommand}
    @ivar command: Renamer command being executed.
    """
    def __init__(self):
        self._obs = logging.RenamerObserver()
        log.startLoggingWithObserver(self._obs.emit, setStdout=False)

        self.options = self.parseOptions()
        self.store = Store(os.path.expanduser('~/.renamer/renamer.axiom'))
        # XXX: One day there might be more than one History item.
        self.history = self.store.findOrCreate(History)

        self.args = getattr(self.options, 'args', [])
        self.command = self.getCommand(self.options)


    def parseOptions(self):
        """
        Parse configuration file and command-line options.
        """
        _options = Options({})
        _options.parseOptions()
        self._obs.verbosity = _options['verbosity']

        self._configFile = config.ConfigFile(
            FilePath(os.path.expanduser(_options['config'])))
        command = self.getCommand(_options)

        options = Options(self._configFile)
        # Apply global defaults.
        options.update(self._configFile.get('renamer', options))
        # Apply command-specific overrides for the global config.
        options.update(
            (k, v) for k, v in
            self._configFile.get(command.name, options).iteritems()
            if k in options)
        # Command-line options trump the config file.
        options.parseOptions()

        logging.msg(
            'Global options: %r' % (options,),
            verbosity=5)

        return options


    def getCommand(self, options):
        """
        Get the L{twisted.python.usage.Options} command that was invoked.
        """
        command = getattr(options, 'subOptions', None)
        if command is None:
            raise usage.UsageError('At least one command must be specified')

        while getattr(command, 'subOptions', None) is not None:
            command = command.subOptions

        return command


    def performRename(self, dst, src):
        """
        Perform a file rename.
        """
        if self.options['no-act']:
            logging.msg('Simulating: %s => %s' % (src.path, dst.path))
            return

        if src == dst:
            logging.msg('Skipping noop "%s"' % (src.path,), verbosity=2)
            return

        if self.options['link-dst']:
            self.changeset.do(
                self.changeset.newAction(u'symlink', src, dst),
                self.options)
        else:
            self.changeset.do(
                self.changeset.newAction(u'move', src, dst),
                self.options)
            if self.options['link-src']:
                self.changeset.do(
                    self.changeset.newAction(u'symlink', dst, src),
                    self.options)


    def runCommand(self, command):
        """
        Run a generic command.
        """
        logging.msg(
            'Using command "%s"' % (command.name,),
            verbosity=4)
        logging.msg(
            'Command options: %r' % (command,),
            verbosity=5)
        return defer.maybeDeferred(command.process, self, self.options)


    def runRenamingCommand(self, command):
        """
        Run a renaming command.
        """
        def _processOne(src):
            self.currentArgument = src
            d = self.runCommand(command)
            d.addCallback(self.performRename, src)
            return d

        self.changeset = self.history.newChangeset()
        logging.msg(
            'Running, doing at most %d concurrent operations' % (
                self.options['concurrent'],),
            verbosity=3)
        return util.parallel(
            self.args, self.options['concurrent'], _processOne)


    def run(self):
        """
        Begin processing commands.
        """
        if IRenamingCommand(type(self.command), None) is not None:
            d = self.runRenamingCommand(self.command)
        else:
            d = self.runCommand(self.command)
        d.addCallback(self.exit)
        return d


    def exit(self, ignored):
        """
        Perform the exit routine.
        """
        if not self.options['no-act']:
            self.history.pruneChangesets()
