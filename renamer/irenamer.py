from zope.interface import Interface, Attribute



class IRenamerCommand(Interface):
    """
    """
    name = Attribute("""
    Command name.
    """)


    description = Attribute("""
    Brief description of the command.
    """)


    def processArgument(renamer, argument):
        """
        """
