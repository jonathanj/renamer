from epsilon.extime import Time

from twisted.python.components import registerAdapter
from twisted.python.filepath import FilePath

from axiom.attributes import reference, text, timestamp
from axiom.item import Item, transacted

from renamer import logging
from renamer.irenamer import IRenamingAction
from renamer.plugin import getActionByName



class History(Item):
    """
    Changeset management.
    """
    created = timestamp(doc="""
    Timestamp of when the history was first created.
    """, defaultFactory=lambda: Time())


    def getChangesets(self):
        """
        Get L{renamer.history.Changeset}s for this history.
        """
        return iter(self.store.query(
            Changeset,
            Changeset.history == self,
            sort=Changeset.modified.ascending))


    @transacted
    def pruneChangesets(self):
        """
        Prune empty changesets from the currently active changesets.
        """
        prunedChangesets = 0
        prunedActions = self.pruneActions()
        for cs in self.store.query(Changeset):
            if not cs.numActions:
                cs.deleteFromStore()
                prunedChangesets += 1
            elif cs.history is None:
                cs.history = self

        logging.msg(
            'Pruned %d changesets' % (prunedChangesets,),
            verbosity=3)

        return prunedChangesets, prunedActions


    @transacted
    def pruneActions(self):
        """
        Remove any L{renamer.history.Action}s that do not have references to a
        L{renamer.history.Changeset}. These are actions most likely created and
        never used, so there is no need to store them.
        """
        count = 0
        for action in self.store.query(Action, Action.changeset == None):
            action.deleteFromStore()
            count += 1

        logging.msg(
            'Pruned %d actions' % (count,),
            verbosity=3)

        return count


    def newChangeset(self):
        """
        Begin a new changeset.

        @rtype: L{renamer.history.Changeset}
        """
        return Changeset(
            store=self.store)



class Changeset(Item):
    """
    A history changeset containing at least one action.
    """
    created = timestamp(doc="""
    Timestamp of when the changeset was first created.
    """, defaultFactory=lambda: Time())


    modified = timestamp(doc="""
    Timestamp of when the changeset was last modified.
    """, defaultFactory=lambda: Time())


    history = reference(doc="""
    Parent history Item.
    """, reftype=History, whenDeleted=reference.CASCADE)


    def __repr__(self):
        return '<%s %d action(s) created=%r modified=%r>' % (
            type(self).__name__,
            self.numActions,
            self.created,
            self.modified)


    def getActions(self):
        """
        Get an iterable of L{renamer.history.Action}s for this changeset,
        sorted by ascending order of creation.
        """
        return iter(
            self.store.query(
                Action,
                Action.changeset == self,
                sort=Action.created.ascending))


    @property
    def numActions(self):
        """
        Number of actions contained in this changeset.
        """
        return self.store.query(Action, Action.changeset == self).count()


    def asHumanly(self):
        """
        Construct a human readable representation of the changeset.
        """
        return u'Changeset with %d action(s) (%s)' % (
            self.numActions,
            self.modified.asHumanly())


    def newAction(self, name, src, dst, verify=True):
        """
        Create a new L{renamer.history.Action}.
        """
        if verify:
            # Check that "name" is in fact a valid action.
            getActionByName(name)
        return Action(
            store=self.store,
            name=name,
            src=src.path,
            dst=dst.path)


    @transacted
    def do(self, action, options, _adapter=IRenamingAction):
        """
        Perform an action.

        @type  action: L{renamer.history.Action}

        @type  options: L{twisted.python.usage.Options}
        """
        renamingAction = _adapter(action)
        renamingAction.do(options)
        action.changeset = self
        self.modified = Time()


    @transacted
    def undo(self, action, options, _adapter=IRenamingAction):
        """
        Perform a reverse action.

        @type  action: L{renamer.irenamer.IRenamingAction}

        @type  options: L{twisted.python.usage.Options}
        """
        renamingAction = _adapter(action)
        renamingAction.undo(options)
        action.deleteFromStore()
        self.modified = Time()



class Action(Item):
    """
    A single action in a changeset.

    Can be adapted to L{renamer.irenamer.IRenamingAction}.
    """
    created = timestamp(doc="""
    Timestamp of when the action was first created.
    """, defaultFactory=lambda: Time())


    name = text(doc="""
    Action name, should be a value that can be passed to
    L{renamer.plugin.getActionByName}.
    """, allowNone=False)


    src = text(doc="""
    Path to the source file of the action.
    """, allowNone=False)


    dst = text(doc="""
    Path to the destination file of the action.
    """, allowNone=False)


    changeset = reference(doc="""
    Parent changeset Item.
    """, reftype=Changeset, whenDeleted=reference.CASCADE)


    def __repr__(self):
        return '<%s name=%r src=%r dst=%r created=%r>' % (
            type(self).__name__,
            self.name,
            self.src,
            self.dst,
            self.created)


    def asHumanly(self):
        """
        Construct a human readable representation of the action.
        """
        return u'%s: %s => %s (%s)' % (
            self.name.title(), self.src, self.dst, self.created.asHumanly())


    def toRenamingAction(self):
        """
        Create a L{renamer.irenamer.IRenamingAction} from this Item.
        """
        return getActionByName(self.name)(
            src=FilePath(self.src),
            dst=FilePath(self.dst))

registerAdapter(Action.toRenamingAction, Action, IRenamingAction)
