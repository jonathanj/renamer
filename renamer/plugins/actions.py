from renamer import logging, util
from renamer.plugin import RenamingAction



class MoveAction(RenamingAction):
    """
    File move action.

    If the source and destination are on different logical devices a
    copy-delete will be used, unless the C{'one-file-system'} option is
    specified.
    """
    name = 'move'


    def _move(self, src, dst, options):
        self.prepare(dst, options)
        logging.msg('Move: %s => %s' % (src.path, dst.path))
        util.rename(src, dst, oneFileSystem=options['one-file-system'])


    # IRenamingAction

    def do(self, options):
        self._move(self.src, self.dst, options)


    def undo(self, options):
        self._move(self.dst, self.src, options)



class SymlinkAction(RenamingAction):
    """
    Symlink action.
    """
    name = 'symlink'


    # IRenamingAction

    def do(self, options):
        self.prepare(self.dst, options)
        logging.msg('Symlink: %s => %s' % (self.src.path, self.dst.path))
        util.symlink(self.src, self.dst)


    def undo(self, options):
        if self.dst.islink():
            logging.msg('Symlink: Removing %s' % (self.dst.path,))
            self.dst.remove()
