from twisted.python.filepath import FilePath
from twisted.trial.unittest import TestCase

from renamer import errors
from renamer.application import Options
from renamer.plugins import actions



class _ActionTestMixin(object):
    actionType = None


    def setUp(self):
        self.path = FilePath(self.mktemp())
        self.path.makedirs()
        self.options = Options(None)
        self.src, self.dst = self.createFiles()


    def createFiles(self):
        """
        Create paths for source and destination files.
        """
        return self.path.child('src'), self.path.child('dst')


    def createAction(self, src=None, dst=None):
        """
        Create an action from L{actionType}.
        """
        if src is None:
            src = self.src
        if dst is None:
            dst = self.dst
        return self.actionType(src, dst)


    def test_do(self):
        """
        Perform the action.
        """


    def test_doWithSubdirs(self):
        """
        Performing an action involving a subdirectory results in that
        subdirectory being created if it didn't already exist.
        """
        self.dst = self.path.child('subdir').child('dst')
        parent = self.dst.parent()
        self.assertFalse(parent.exists())
        self.test_do()
        self.assertTrue(parent.exists())
        self.assertEquals(parent.listdir(), ['dst'])


    def test_doClobber(self):
        """
        Performing an action raises L{renames.errors.NoClobber} when the
        destination file already exists.
        """
        self.dst.touch()
        action = self.createAction()
        self.assertRaises(
            errors.NoClobber, action.do, self.options)


    def test_undo(self):
        """
        Perform the reverse action.
        """


    def test_undoWithSubdirs(self):
        """
        Performing a reverse action does not remove existing directories.
        """
        self.dst = self.path.child('subdir').child('dst')
        parent = self.dst.parent()
        parent.makedirs()
        self.assertTrue(parent.exists())
        self.test_undo()
        self.assertTrue(parent.exists())
        self.assertEquals(parent.listdir(), [])


    def test_undoClobber(self):
        """
        Performing a reverse action raises L{renames.errors.NoClobber} when the
        destination file already exists.
        """
        self.src.touch()
        action = self.createAction()
        self.assertRaises(
            errors.NoClobber, action.undo, self.options)



class MoveActionTests(_ActionTestMixin, TestCase):
    """
    Tests for L{renamer.plugins.actions.MoveAction}.
    """
    actionType = actions.MoveAction


    def test_do(self):
        self.src.touch()

        self.assertTrue(self.src.exists())
        self.assertFalse(self.dst.exists())

        action = self.createAction()
        action.do(self.options)

        self.assertFalse(self.src.exists())
        self.assertTrue(self.dst.exists())


    def test_undo(self):
        self.dst.touch()

        self.assertFalse(self.src.exists())
        self.assertTrue(self.dst.exists())

        action = self.createAction()
        action.undo(self.options)

        self.assertTrue(self.src.exists())
        self.assertFalse(self.dst.exists())



class SymlinkActionTests(_ActionTestMixin, TestCase):
    """
    Tests for L{renamer.plugins.actions.SymlinkAction}.
    """
    actionType = actions.SymlinkAction


    def test_do(self):
        self.src.touch()

        self.assertTrue(self.src.exists())
        self.assertFalse(self.dst.exists())

        action = self.createAction()
        action.do(self.options)

        self.assertTrue(self.src.exists())
        self.assertTrue(self.dst.exists())
        self.assertTrue(self.dst.islink())


    def test_undo(self):
        self.src.touch()
        self.src.linkTo(self.dst)

        self.assertTrue(self.src.exists())
        self.assertTrue(self.dst.exists())
        self.assertTrue(self.dst.islink())

        action = self.createAction()
        action.undo(self.options)

        self.assertTrue(self.src.exists())
        self.assertFalse(self.dst.exists())


    def test_undoClobber(self):
        """
        Undoing a symlink cannot raise L{renamer.errors.NoClobber}.
        """
