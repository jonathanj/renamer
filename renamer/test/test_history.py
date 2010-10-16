import time

from axiom.store import Store

from twisted.python.filepath import FilePath
from twisted.trial.unittest import TestCase

from renamer import errors, history, irenamer
from renamer.plugins.actions import SymlinkAction



def FakeOptions():
    return {}



class FakeAction(object):
    def do(self, options):
        pass


    def undo(self, options):
        pass



class HistoryTests(TestCase):
    """
    Tests for L{renamer.history.History}.
    """
    def setUp(self):
        self.store = Store()
        self.history = history.History(store=self.store)


    def test_newChangeset(self):
        """
        L{renamer.history.History.newChangeset} creates a new changeset
        instance and does not track it immediately.
        """
        cs = self.history.newChangeset()
        self.assertIdentical(type(cs), history.Changeset)
        self.assertEquals(list(self.history.getChangesets()), [])


    def test_pruneChangesets(self):
        """
        L{renamer.history.History.pruneChangesets} removes empty changesets
        (changesets without any actions) from the database.
        """
        cs = self.history.newChangeset()
        self.assertEquals(list(self.history.getChangesets()), [])

        action = cs.newAction(
            u'fake', FilePath(u'src'), FilePath(u'dst'), verify=False)

        # Unused action.
        cs.newAction(
            u'fake', FilePath(u'src'), FilePath(u'dst'), verify=False)

        self.assertEquals(list(cs.getActions()), [])
        self.assertEquals(cs.numActions, 0)

        def _adapter(action):
            return FakeAction()

        cs.do(action, FakeOptions(), _adapter=_adapter)

        self.assertEquals(
            list(cs.getActions()), [action])
        self.assertEquals(cs.numActions, 1)
        prunedChangesets, prunedActions = self.history.pruneChangesets()
        self.assertEquals(prunedChangesets, 0)
        self.assertEquals(prunedActions, 1)
        self.assertEquals(list(self.history.getChangesets()), [cs])

        cs.undo(action, FakeOptions(), _adapter=_adapter)
        self.assertEquals(list(cs.getActions()), [])
        self.assertEquals(cs.numActions, 0)
        prunedChangesets, prunedActions = self.history.pruneChangesets()
        self.assertEquals(prunedChangesets, 1)
        self.assertEquals(prunedActions, 0)
        self.assertEquals(list(self.history.getChangesets()), [])



class ChangesetTests(TestCase):
    """
    Tests for L{renamer.history.Changeset}.
    """
    def setUp(self):
        self.store = Store()
        self.history = history.History(store=self.store)


    def test_newInvalidAction(self):
        """
        L{renamer.history.Changeset.newAction} raises
        L{renamer.errors.NoSuchAction} if the action name specified does not
        refer to a valid action.
        """
        cs = self.history.newChangeset()
        self.assertRaises(errors.NoSuchAction,
            cs.newAction, 'THIS_IS_NOT_REAL', FilePath(u'a'), FilePath(u'b'))


    def test_representations(self):
        """
        L{renamer.history.Changeset.asHumanly} returns a human-readable and
        accurate representation of a changeset.

        L{renamer.history.Changeset.__repr__} returns a useful and accurate
        representation of a changeset.
        """
        cs = self.history.newChangeset()

        self.assertTrue(
            cs.asHumanly().startswith(
                u'Changeset with 0 action(s) ('))

        self.assertEquals(
            repr(cs),
            '<Changeset 0 action(s) created=%r modified=%r>' % (
                cs.created, cs.modified))

        action = cs.newAction(
            u'fake', FilePath(u'src'), FilePath(u'dst'), verify=False)

        def _adapter(action):
            return FakeAction()

        cs.do(action, FakeOptions(), _adapter=_adapter)

        self.assertTrue(
            cs.asHumanly().startswith(
                u'Changeset with 1 action(s) ('))

        self.assertEquals(
            repr(cs),
            '<Changeset 1 action(s) created=%r modified=%r>' % (
                cs.created, cs.modified))



class ActionTests(TestCase):
    """
    Tests for L{renamer.history.Action}.
    """
    def setUp(self):
        self.store = Store()
        self.history = history.History(store=self.store)


    def test_adaption(self):
        """
        Adapting a L{renamer.history.Action} object to
        L{renamer.irenamer.IRenamingAction} results in an object implementing
        C{IRenamingAction} that can perform forward and reverse actions.
        """
        cs = self.history.newChangeset()
        action = cs.newAction(u'symlink', FilePath(u'src'), FilePath(u'dst'))
        a = irenamer.IRenamingAction(action)
        self.assertIdentical(type(a), SymlinkAction)
        self.assertTrue(irenamer.IRenamingAction.providedBy(type(a)))


    def test_representations(self):
        """
        L{renamer.history.Action.asHumanly} returns a human-readable and
        accurate representation of an action.

        L{renamer.history.Action.__repr__} returns a useful and accurate
        representation of an action.
        """
        cs = self.history.newChangeset()
        src = FilePath(u'src')
        dst = FilePath(u'dst')
        action = cs.newAction(u'fake', src, dst, verify=False)

        self.assertTrue(
            action.asHumanly().startswith(
                u'Fake: %s => %s (' % (src.path, dst.path)))

        self.assertEquals(
            repr(action),
            '<Action name=%r src=%r dst=%r created=%r>' % (
                action.name, action.src, action.dst, action.created))
