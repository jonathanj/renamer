from twisted.python import usage

from renamer import logging
from renamer.plugin import Command, SubCommand



class _UndoMixin(object):
    optFlags = [
        ('forget',        None, 'Forget the changeset/action without undoing anything, use with caution!'),
        ('ignore-errors', None, 'Do not stop the process when encountering OS errors')]


    def parseNumeric(self, name, arg):
        try:
            return int(arg)
        except (ValueError, TypeError):
            raise usage.UsageError('"%s" must be an integer' % (name,))


    def validIdentifier(self, name, limit):
        value = self[name]
        if not (0 <= value < limit):
            raise usage.UsageError(
                'Invalid %s identifier, consult the "undo list" command' % (
                    name,))
        return value


    def undoActions(self, renamer, changeset, actions, faux=False):
        """
        Undo actions from a changeset.
        """
        for action in reversed(actions):
            if not faux:
                logging.msg('Undo: %s' % (action.asHumanly(),), verbosity=3)
            try:
                changeset.undo(action, renamer.options, faux=faux)
            except OSError, e:
                if not self['ignore-errors']:
                    raise e
                logging.msg('Ignoring %r' % (e,), verbosity=3)



class UndoAction(SubCommand, _UndoMixin):
    name = 'action'
    synopsis = '[options] <changeset> <action>'


    longdesc = """
    Undo a single action from a changeset. Consult "undo list" for changeset
    and action identifiers.
    """


    def parseArgs(self, changeset, action):
        self['changeset'] = self.parseNumeric('changeset', changeset) - 1
        self['action'] = self.parseNumeric('action', action) - 1


    def process(self, renamer):
        changeset = self.validIdentifier(
            'changeset', len(renamer.history.changesets))
        changeset = renamer.history.changesets[changeset]

        action = self.validIdentifier(
            'action', len(changeset.actions))
        actions = [changeset.actions[action]]

        faux = self['forget']
        verb = ('Undoing', 'Forgetting')[faux]
        logging.msg('%s %d action(s) from: %s' % (
            verb, len(actions), changeset.asHumanly(),),
            verbosity=3)
        self.undoActions(renamer, changeset, actions, faux=faux)



class UndoChangeset(SubCommand, _UndoMixin):
    name = 'changeset'
    synopsis = '[options] <changeset>'


    longdesc = """
    Undo an entire changeset. Consult "undo list" for changeset identifiers.
    """


    def parseArgs(self, changeset):
        self['changeset'] = self.parseNumeric('changeset', changeset) - 1


    def process(self, renamer):
        changeset = self.validIdentifier(
            'changeset', len(renamer.history.changesets))
        changeset = renamer.history.changesets[changeset]
        actions = changeset.actions

        faux = self['forget']
        verb = ('Undoing', 'Forgetting')[faux]
        logging.msg('%s: %s' % (verb, changeset.asHumanly()),
                    verbosity=3)
        self.undoActions(renamer, changeset, actions, faux=faux)



class UndoList(SubCommand):
    name = 'list'


    longdesc = """
    List undoable changesets and actions.
    """


    def process(self, renamer):
        for i, changeset in enumerate(renamer.history.changesets):
            print 'Changeset #%d:  %s' % (i + 1, changeset.asHumanly())
            for j, action in enumerate(changeset.actions):
                print '   Action #%d:  %s' % (j + 1, action.asHumanly())
            print



class Undo(Command):
    name = 'undo'


    description = 'Undo previous Renamer actions'


    longdesc = """
    Every invocation of Renamer stores actions taken as a changeset in a
    history file, allowing renamer to undo previously performed actions or
    entire changesets.

    Undo actions are communicated by identifiers, which can be discovered by
    consulting "undo list".
    """


    subCommands = [
        ('action',    None, UndoAction,    'Undo a single action from a changeset'),
        ('changeset', None, UndoChangeset, 'Undo a whole changeset'),
        ('list',      None, UndoList,      'List changesets')]


    def parseArgs(self, *args):
        raise usage.UsageError('Issue an undo subcommand to perform')
