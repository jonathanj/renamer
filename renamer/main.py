from twisted.internet import reactor

from renamer import application
from renamer.logging import RenamerObserver


def main():
    options = application.Options()
    options.parseOptions()

    obs = RenamerObserver(options['verbosity'])
    obs.start()

    r = application.Renamer(options)
    reactor.callWhenRunning(r.run)
    reactor.run()

    obs.stop()
