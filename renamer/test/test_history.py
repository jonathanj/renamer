import time
try:
    from xml.etree import ElementTree as etree
    etree # Ssssh, Pyflakes.
except ImportError:
    from elementtree import ElementTree as etree

from twisted.python.filepath import FilePath
from twisted.trial.unittest import TestCase

from renamer import history



def FakeOptions():
    return {}



class FakeAction(object):
    def do(self, options):
        pass


    def undo(self, options):
        pass


    def asElement(self):
        return etree.Element('test')


    @classmethod
    def fromElement(cls, elem):
        return cls()



class HistoryTests(TestCase):
    """
    Tests for L{renamer.history.History}.
    """
    def setUp(self):
        self.path = FilePath(__file__).parent()
        path = self.path.child('data').child('history.xml')
        self.history = history.History(path)


    def newHistory(self):
        """
        Create a new history instance.
        """
        path = FilePath(self.mktemp())
        return history.History(path)


    def test_readExisting(self):
        """
        Creating a new history instance with a path to an existing history file
        reads that data in and deserializes it.
        """
        self.assertEquals(len(self.history.changesets), 1)
        self.assertEquals(len(self.history.changesets[0].actions), 1)


    def test_newChangeset(self):
        """
        L{renamer.history.History.newChangeset} creates a new changeset
        instance and begins tracking it.
        """
        h = self.newHistory()
        self.assertEquals(len(h.changesets), 0)
        h.newChangeset()
        self.assertEquals(len(h.changesets), 1)


    def test_pruneChangesets(self):
        """
        L{renamer.history.History.pruneChangesets} removes empty changesets,
        changesets without any actions, from the list of currently active
        changesets.
        """
        h = self.newHistory()

        options = FakeOptions()
        action = FakeAction()
        cs = h.newChangeset()
        cs.do(action, options)

        self.assertEquals(h.changesets, [cs])
        self.assertEquals(len(cs.actions), 1)
        self.assertEquals(h.pruneChangesets(), [cs])

        cs.undo(action, options)
        self.assertEquals(h.changesets, [cs])
        self.assertEquals(len(cs.actions), 0)
        self.assertEquals(h.pruneChangesets(), [])



class ChangesetTests(TestCase):
    """
    Tests for L{renamer.history.Changeset}.
    """
    def setUp(self):
        self.path = FilePath(__file__).parent()
        path = self.path.child('data').child('history.xml')
        self.history = history.History(path)


    def test_repr(self):
        """
        L{renamer.history.Changeset.__repr__} returns a useful and accurate
        representation of a changeset.
        """
        cs = self.history.changesets[0]
        self.assertEquals(
            repr(cs),
            '<Changeset 1 action(s) timestamp=%s>' % (cs.timestamp,))


    def test_asHumanly(self):
        """
        L{renamer.history.Changeset.asHumanly} returns a human-readable and
        accurate representation of a changeset.
        """
        cs = self.history.changesets[0]
        t = time.asctime(time.localtime(cs.timestamp))
        self.assertEquals(
            cs.asHumanly(),
            'Changeset with 1 action(s) (%s)' % (t,))
