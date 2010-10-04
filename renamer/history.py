import time
from StringIO import StringIO
try:
    from xml.etree import ElementTree as etree
    etree # Ssssh, Pyflakes.
except ImportError:
    from elementtree import ElementTree as etree

from renamer import logging
from renamer.irenamer import IRenamingAction



class Changeset(object):
    """
    A single history changeset containing at least one action.

    @type actions: C{list} of L{renamer.irenamer.IRenamingAction}
    @ivar actions: Changeset actions.

    @type timestamp: C{float}
    @ivar timestamp: Timestamp indicating when this changeset was created.
    """
    def __init__(self, actions=None, timestamp=None):
        if actions is None:
            actions = []
        self.actions = actions
        if timestamp is None:
            timestamp = time.time()
        self.timestamp = timestamp


    def __repr__(self):
        return '<%s %d action(s) timestamp=%r>' % (
            type(self).__name__,
            len(self.actions),
            self.timestamp)


    def asHumanly(self):
        """
        Construct a human readable representation of the changeset.

        @rtype: C{unicode}
        """
        return u'Changeset with %s action(s) (%s)' % (
            len(self.actions),
            time.asctime(time.localtime(self.timestamp)),)


    @classmethod
    def fromElement(cls, elem):
        """
        Deserialize and create a changeset from an ElementTree element.

        @type  elem: L{xml.etree.ElementTree.Element}

        @rtype: L{renamer.history.Changeset}
        """
        actions = map(IRenamingAction, elem.getiterator('action'))
        return cls(
            actions=actions,
            timestamp=float(elem.get('timestamp')))


    def asElement(self):
        """
        Serialize a changeset to an ElementTree element.

        @rtype: L{xml.etree.ElementTree.Element}
        """
        elem = etree.Element(
            'changeset', timestamp=unicode(self.timestamp))
        for action in self.actions:
            elem.append(action.asElement())
        return elem


    def do(self, action, options):
        """
        Perform an action.

        @type  action: L{renamer.irenamer.IRenamingAction}

        @type  options: L{twisted.python.usage.Options}
        """
        action.do(options)
        self.actions.append(action)


    def undo(self, action, options, faux=False):
        """
        Perform a reverse action.

        @type  action: L{renamer.irenamer.IRenamingAction}

        @type  options: L{twisted.python.usage.Options}

        @type  faux: C{bool}
        @param faux: Only remove the action without undoing it?
        """
        if not faux:
            action.undo(options)
        self.actions.remove(action)



class History(object):
    """
    Changeset management.

    @type historyPath: L{twisted.python.filepath.FilePath}
    @ivar historyPath: Path to history file.

    @type changesets: C{list} of L{renamer.history.Changeset}
    @ivar changesets: Currently active changesets.
    """
    def __init__(self, historyPath):
        self.historyPath = historyPath
        tree = self._createOrOpen()
        self.changesets = list(self._getChangesets(tree))


    def _newTree(self):
        """
        Create a new history L{xml.etree.ElementTree.ElementTree}.
        """
        return etree.ElementTree(etree.Element('history'))


    def _createOrOpen(self):
        """
        Create a new history file or open an existing one.
        """
        if not self.historyPath.exists():
            return self._newTree()
        return etree.parse(self.historyPath.path)


    def _getChangesets(self, tree):
        """
        Deserialize all changesets in a history ElementTree.
        """
        for elem in tree.getroot().getiterator('changeset'):
            yield Changeset.fromElement(elem)


    def pruneChangesets(self):
        """
        Prune invalid or empty changesets from the currently active changesets.
        """
        newcs = []
        for cs in self.changesets:
            if cs.actions:
                newcs.append(cs)

        logging.msg(
            'Pruned %d changesets' % (
                len(self.changesets) - len(newcs)),
            verbosity=3)

        return newcs


    def newChangeset(self):
        """
        Begin a new changeset.

        @rtype: L{renamer.history.Changeset}
        """
        cs = Changeset()
        self.changesets.append(cs)
        return cs


    def save(self):
        """
        Serialize the currently active changesets and write them to the history
        file.
        """
        parent = self.historyPath.parent()
        if not parent.exists():
            parent.makedirs()

        self.changesets = self.pruneChangesets()

        logging.msg(
            'Saving %d changesets to history "%s"' % (
                len(self.changesets), self.historyPath.path,),
            verbosity=3)

        tree = self._newTree()
        root = tree.getroot()
        for cs in self.changesets:
            root.append(cs.asElement())

        fd = StringIO()
        tree.write(fd, encoding='utf-8')
        self.historyPath.setContent(fd.getvalue())
