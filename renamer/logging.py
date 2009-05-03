import sys

from twisted.python import log


class RenamerObserver(object):
    """
    Twisted event log observer.
    """
    def __init__(self, verbosity):
        self.verbosity = verbosity

    def start(self):
        log.addObserver(self.emit)

    def stop(self):
        log.removeObserver(self.emit)

    def _formatEventMessage(self, message):
        return ' '.join(str(m) for m in message) + '\n'

    def _emitError(self, eventDict):
        if 'failure' in eventDict:
            text = eventDict['failure'].getTraceback()
        else:
            text = self._formatEventMessage(eventDict['message'])
        sys.stderr.write(text)
        sys.stderr.flush()

    def emit(self, eventDict):
        if eventDict['isError']:
            self._emitError(eventDict)
        else:
            if eventDict.get('source') == 'renamer':
                verbosity = eventDict.get('verbosity', 1)
                if self.verbosity >= verbosity:
                    sys.stdout.write(self._formatEventMessage(eventDict['message']))
                    sys.stdout.flush()


def msg(message, **kw):
    log.msg(message, source='renamer', **kw)

err = log.err
