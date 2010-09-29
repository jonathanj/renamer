from twisted.python import log
from twisted.internet import reactor

from renamer import application
from renamer.logging import RenamerObserver


def main():
    options = application.Options()
    options.parseOptions()

    obs = RenamerObserver(options['verbosity'])
    log.startLoggingWithObserver(obs.emit, setStdout=False)

    r = application.Renamer(options)
    reactor.callWhenRunning(r.run)
    reactor.run()
