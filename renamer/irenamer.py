from zope.interface import Interface, Attribute



class IRenamerCommand(Interface):
    """
    Renamer command.
    """
    name = Attribute("""
    Command name.
    """)


    description = Attribute("""
    Brief description of the command.
    """)


    defaultNameFormat = Attribute("""
    String template for the default name format to use if one is not supplied
    to Renamer.
    """)


    def processArgument(argument):
        """
        Process an argument.

        @rtype:  C{dict} mapping C{unicode} to C{unicode}
        @return: Mapping of keys to values to substitute info the name
            template.
        """
