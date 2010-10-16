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
    An action that performs some renaming-related action and is undoable.
    """
    def asHumanly():
        """
        Construct a human readable representation of the action.

        @rtype: C{unicode}
        """


    def do(src, dst, options):
        """
        Perform the action.

        @type  src: L{twisted.python.filepath.FilePath}
        @param src: Source path.

        @type  dst: L{twisted.python.filepath.FilePath}
        @param src: Destination path.

        @type  options: L{twisted.python.usage.Options}
        """


    def undo(src, dst, options):
        """
        Perform the reverse action.

        @type  src: L{twisted.python.filepath.FilePath}
        @param src: Source path.

        @type  dst: L{twisted.python.filepath.FilePath}
        @param src: Destination path.

        @type  options: L{twisted.python.usage.Options}
        """


    def fromElement(elem):
        """
        Deserialize and create the action from an ElementTree element.

        @type  elem: L{xml.etree.ElementTree.Element}

        @rtype: L{renamer.irenamer.IRenamingAction}
        """


    def asElement():
        """
        Serialize an action to an ElementTree element.

        @rtype: L{xml.etree.ElementTree.Element}
        """
