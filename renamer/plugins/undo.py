from twisted.python import usage

from renamer import logging
from renamer.history import Action, Changeset
from renamer.plugin import Command, SubCommand



def getItem(store, storeID, acceptableTypes):
    """
    Get an Axiom Item from a store by ID and verify that it is an acceptable
    type.
    """
    try:
        storeID = int(storeID)
    except (ValueError, TypeError):
        raise usage.UsageError(
            'Identifier %r is not an integer' % (storeID,))
    else:
        item = store.getItemByID(storeID, default=None)
        if not isinstance(item, acceptableTypes):
            raise usage.UsageError(
                'Invalid identifier %r' % (storeID,))
        return item



class _UndoMixin(object):
    optFlags = [
        ('ignore-errors', None, 'Do not stop the process when encountering OS errors')]


    def undoActions(self, options, changeset, actions):
        """
        Undo specific actions from a changeset.
        """
        for action in actions:
            msg = 'Simulating undo'
            if not options['no-act']:
                msg = 'Undo'

            logging.msg('%s: %s' % (msg, action.asHumanly()), verbosity=3)
            if not options['no-act']:
                try:
                    changeset.undo(action, options)
                except OSError, e:
                    if not self['ignore-errors']:
                        raise e
                    logging.msg('Ignoring %r' % (e,), verbosity=3)



class UndoAction(SubCommand, _UndoMixin):
    name = 'action'


    synopsis = '[options] <actionID>'


    longdesc = """
    Undo a single action from a changeset. Consult "undo list" for action
    identifiers.
    """


    def parseArgs(self,  action):
        self['action'] = action


    def process(self, renamer, options):
        action = getItem(renamer.store, self['action'], Action)
        self.undoActions(options, action.changeset, [action])



class UndoChangeset(SubCommand, _UndoMixin):
    name = 'changeset'


    synopsis = '[options] <changesetID>'


    longdesc = """
    Undo an entire changeset. Consult "undo list" for changeset identifiers.
    """


    def parseArgs(self, changeset):
        self['changeset'] = changeset


    def process(self, renamer, options):
        changeset = getItem(renamer.store, self['changeset'], Changeset)
        logging.msg('Undoing: %s' % (changeset.asHumanly(),),
                    verbosity=3)
        actions = list(changeset.getActions())
        self.undoActions(options, changeset, reversed(actions))



class UndoList(SubCommand):
    name = 'list'


    longdesc = """
    List undoable changesets and actions.
    """


    def process(self, renamer, options):
        changesets = list(renamer.history.getChangesets())
        for cs in changesets:
            print 'Changeset ID=%d:  %s' % (cs.storeID, cs.asHumanly())
            for a in cs.getActions():
                print '   Action ID=%d:  %s' % (a.storeID, a.asHumanly())
            print

        if not changesets:
            print 'No changesets!'



class UndoForget(SubCommand):
    name = 'forget'


    synopsis = '<identifier>'


    longdesc = """
    Forget (permanently remove) an undo history action or entire changeset.
    Consult "undo list" for identifiers.
    """


    def parseArgs(self, identifier):
        self['identifier'] = identifier


    def process(self, renamer, options):
        item = getItem(renamer.store, self['identifier'], (Action, Changeset))
        if not options['no-act']:
            logging.msg('Forgetting: %s' % (item.asHumanly(),), verbosity=2)
            item.deleteFromStore()



class Undo(Command):
    name = 'undo'


    description = 'Undo previous Renamer actions'


    longdesc = """
    Every invocation of Renamer stores the actions taken as a changeset, this
    allows Renamer to undo entire changesets or previously performed individual
    actions.

    Undo actions are communicated by identifiers, which can be discovered by
    consulting "undo list".
    """


    subCommands = [
        ('action',    None, UndoAction,    'Undo a single action from a changeset'),
        ('changeset', None, UndoChangeset, 'Undo a whole changeset'),
        ('forget',    None, UndoForget,    'Forget an undo history item'),
        ('list',      None, UndoList,      'List changesets')]


    def parseArgs(self, *args):
        raise usage.UsageError('Issue an undo subcommand to perform')
