import os, sys

from twisted.python import failure, usage
from twisted.internet import defer, reactor

from renamer import application, logging



status = 0



def main():
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
        try:
            d = defer.succeed(application.Renamer())
        except SystemExit:
            d = defer.succeed(None)
        except:
            d = defer.fail(failure.Failure())
        else:
            d.addCallback(lambda r: r.run())
        d.addErrback(usageError)
        d.addErrback(logError)
        d.addBoth(lambda ign: reactor.stop())

    reactor.callWhenRunning(run)
    reactor.run()
    sys.exit(status)
