import glob, logging, optparse, os, sys, stat, time

from renamer.env import Environment


def sortByCtime(path):
    try:
        return time.localtime(os.stat(path)[stat.ST_CTIME])
    except OSError:
        return -1


def sortBySize(path):
    try:
        return os.stat(path)[stat.ST_SIZE]
    except OSError:
        return -1


def sortByName(path):
    return path


class Renamer(object):
    _sortMethods = {
        'created': sortByCtime,
        'size':    sortBySize,
        'name':    sortByName}

    def __init__(self):
        self.options, self.targets = self.parseOptions()

        self.setupLogging()

        if self.options.sort:
            self.targets.sort(key=self._sortMethods[self.options.sort])
        if self.options.reverse:
            self.targets.reverse()

        self.env = Environment(self.targets,
                               safemode=self.options.dryrun,
                               movemode=self.options.move,
                               verbosity=self.options.verbosity)

    def run(self):
        if self.options.script is not None:
            self.runScript()
        else:
            self.runInteractive()

    def runScript(self):
        # Run the script as many times as there are targets
        # XXX: this is a bit of hack
        for _ in self.targets:
            self.env.runScript(self.options.script)

    def runInteractive(self):
        try:
            while True:
                self.env.execute(raw_input('rn> '))
        except EOFError:
            print

    def parseOptions(self):
        parser = optparse.OptionParser(usage='%prog [options] input1 [input2 ...]')
        parser.add_option('-t', '--dry-run', dest='dryrun', action='store_true', help='Perform a dry-run')
        parser.add_option('-m', '--move', dest='move', action='store_true', help='Move files')
        parser.add_option('-s', '--script', dest='script', action='store', help='Command script to execute')
        parser.add_option('-v', action='count', dest='verbosity', default=0, help='Increase output verbosity')
        parser.add_option('-g', '--glob', dest='glob', action='store_true', help='Expand filenames as UNIX-style globs')
        parser.add_option('-S', '--sort', dest='sort', action='store', help='Sort filenames by criteria: created, name, size')
        parser.add_option('-R', '--reverse', dest='reverse', action='store_true', help='Reverse filename order')
        options, args = parser.parse_args()

        if options.script and len(args) < 1:
            parser.error('too few arguments')

        if options.glob:
            args = self.expandArgs(args)

        return options, list(args)

    def expandArgs(self, args):
        def _glob():
            return [arg for _arg in args for arg in glob.glob(_arg)]

        def _win32():
            _args = []
            for arg in args:
                if not os.path.exists(arg):
                    globbed = glob.glob(arg)
                    if globbed:
                        _args.extend(globbed)
                        continue

                _args.append(arg)
            return _args

        if sys.platform == 'win32':
            return _win32()

        return _glob()

    def setupLogging(self):
        verbosity = self.options.verbosity
        if verbosity == 0:
            logging.basicConfig(level=logging.WARNING)
        elif verbosity == 1:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.DEBUG)


def main():
    r = Renamer()
    r.run()
