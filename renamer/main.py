import os, sys

from twisted.python import usage
from twisted.internet import defer, reactor

from renamer import application, logging



def main():
    status = 0

    def logError(f):
        logging.err(f)
        global status
        status = 1

    def usageError(f):
        f.trap(usage.UsageError)
        prog = os.path.basename(sys.argv[0])
        sys.stderr.write('%s: %s\n' % (prog, f.value))
        sys.stderr.write('Consult --help for usage information\n')
        global status
        status = 1

    def run():
        d = defer.maybeDeferred(application.Renamer)
        d.addCallback(lambda r: r.run())
        d.addErrback(usageError)
        d.addErrback(logError)
        d.addBoth(lambda ign: reactor.stop())

    reactor.callWhenRunning(run)
    reactor.run()
    sys.exit(status)
