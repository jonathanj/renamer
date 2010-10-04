import os, sys

from twisted.python import usage
from twisted.internet import defer, reactor

from renamer import application, logging



def main():
    def _run():
        d = defer.maybeDeferred(r.run)
        d.addErrback(logging.err)
        d.addBoth(lambda ignored: reactor.stop())
        return d

    try:
        r = application.Renamer()
    except usage.UsageError, e:
        prog = os.path.basename(sys.argv[0])
        print '%s: %s' % (prog, e)
        print '%s: Consult --help for usage details' % (prog)
        sys.exit(1)
    else:
        reactor.callWhenRunning(_run)
        reactor.run()
