import sys

from twisted.python import log



class RenamerObserver(object):
    """
    Twisted event log observer for Renamer.
    """
    def __init__(self, verbosity=1):
        self.verbosity = verbosity


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
                    leader = '-' * (verbosity - 1)
                    if leader:
                        leader += ' '
                    sys.stdout.write(leader +
                        self._formatEventMessage(eventDict['message']))
                    sys.stdout.flush()



def msg(message, **kw):
    # Passing unicode to log.msg is not supported, don't do it.
    if isinstance(message, unicode):
        codec = (
            getattr(sys.stdout, 'encoding', None) or sys.getdefaultencoding())
        message = message.encode(codec, 'replace')
    log.msg(message, source='renamer', **kw)



err = log.err
