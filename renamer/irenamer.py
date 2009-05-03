from zope.interface import Interface, Attribute


class IRenamerPlugin(Interface):
    name = Attribute("""
    Plugin name or C{None} to indicate a global plugin.
    """)
