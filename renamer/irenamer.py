from zope.interface import Interface, Attribute



class ICommand(Interface):
    """
    Generic Renamer command.
    """
    name = Attribute("""
    Command name.
    """)


    description = Attribute("""
    Brief description of the command.
    """)


    def process(renamer):
        """
        Called once command line parsing is complete.
        """



class IRenamingCommand(ICommand):
    """
    Command that performs renaming on one argument at a time.
    """
    defaultNameTemplate = Attribute("""
    String template for the default name format to use if one is not supplied.
    """)


    defaultPrefixTemplate = Attribute("""
    String template for the default prefix format to use if one is not
    supplied.
    """)


    def processArgument(argument):
        """
        Process an argument.

        @rtype:  C{dict} mapping C{unicode} to C{unicode}
        @return: Mapping of keys to values to substitute info the name
            template.
        """



class IRenamingAction(Interface):
    """
    An action that performs some renaming-related function and is undoable.
    """
    src = Attribute("""
    L{twisted.python.filepath.FilePath} to the source file.
    """)


    dst = Attribute("""
    L{twisted.python.filepath.FilePath} to the destination file.
    """)


    def do(options):
        """
        Perform the action.

        @type  options: L{twisted.python.usage.Options}
        """


    def undo(options):
        """
        Perform the reverse action.

        @type  options: L{twisted.python.usage.Options}
        """
