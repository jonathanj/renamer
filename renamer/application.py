"""
Renamer application logic.
"""
import errno, glob, os, sys

from twisted.internet import reactor
from twisted.python import usage
from twisted.python.filepath import FilePath

from renamer import logging, plugin, util



class Options(usage.Options, plugin.RenamerSubCommandMixin):
    synopsis = '[options] command argument [argument ...]'


    optFlags = [
        ('glob',            'g',  'Expand arguments as UNIX-style globs.'),
        ('one-file-system', 'x',  "Don't cross filesystems."),
        ('dry-run',         'n',  'Perform a dry-run.'),
        ('link-src',        None, 'Create a symlink at the source.'),
        ('link-dst',        None, 'Create a symlink at the destination.')]


    optParameters = [
        ('concurrent', 'l',  10,
         'Maximum number of concurrent tasks to perform at a time', int)]


    def subCommands():
        def get(self):
            for plg in plugin.getPlugins():
                try:
                    yield plg.name, None, plg, plg.description
                except AttributeError:
                    raise RuntimeError('Malformed plugin: %r' % (plg,))
        return (get,)

    subCommands = property(*subCommands())


    def __init__(self):
        usage.Options.__init__(self)
        self['verbosity'] = 1


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


    def glob(self, args):
        """
        Glob arguments.
        """
        def _glob():
            return (arg
                for _arg in args
                for arg in glob.glob(_arg))

        def _globWin32():
            for arg in args:
                if not os.path.exists(arg):
                    globbed = glob.glob(arg)
                    if globbed:
                        for a in globbed:
                            yield a
                        continue
                yield arg

        if sys.platform == 'win32':
            return _globWin32()
        return _glob()


    def parseArgs(self, *args):
        args = (FilePath(self.decodeCommandLine(a)) for a in args)
        if self['glob']:
            args = self.glob(args)
        self.args = list(args)



class Renamer(object):
    """
    Renamer main logic.

    @type options: L{renamer.application.Options}
    @ivar options: Parsed command-line options
    """
    def __init__(self, options):
        self.options = options


    def rename(self, src, dst):
        options = self.options

        if options['dry-run']:
            logging.msg('Dry-run: %s => %s' % (src.path, dst.path))
            return

        if dst.exists():
            logging.msg('Refusing to clobber existing file "%s"' % (
                dst.path,))
            return

        parent = dst.parent()
        if not parent.exists():
            logging.msg('Creating directory structure for "%s"' % (
                parent.path,), verbosity=2)
            parent.makedirs()

        # Linking at the destination requires no moving.
        if options['link-dst']:
            logging.msg('Symlink: %s => %s' % (src.path, dst.path))
            src.linkTo(dst)
        else:
            logging.msg('Move: %s => %s' % (src.path, dst.path))
            util.rename(src, dst, oneFileSystem=options['one-file-system'])
            if options['link-src']:
                logging.msg('Symlink: %s => %s' % (dst.path, src.path))
                dst.linkTo(src)


    def _processOne(self, src):
        d = self.options.command.processArgument(self, src)
        d.addCallback(lambda dst: self.rename(src, dst))
        return d


    def run(self):
        d = util.parallel(
            self.options.args, self.options['concurrent'], self._processOne)
        d.addErrback(logging.err)
        d.addBoth(lambda ignored: reactor.stop())
        return d
