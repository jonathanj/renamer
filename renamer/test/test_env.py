from twisted.trial.unittest import TestCase

from renamer.errors import StackError
from renamer.env import Stack


class StackTests(TestCase):
    def makeStack(self):
        stack = Stack()
        for arg in [u'arg1', u'arg2', u'arg3']:
            stack.push(arg)

        return stack

    def test_pushPopPeek(self):
        """
        Pushing, popping and peeking for the stack behave as intended.
        """
        stack = Stack()

        self.assertRaises(StackError, stack.pop)

        stack.push(1)
        self.assertEqual(stack.pop(), 1)

        stack.push(u'a')
        stack.push(u'b')
        self.assertEqual(stack.pop(), u'b')
        self.assertEqual(stack.pop(), u'a')

        stack.push(u'c')
        self.assertEqual(stack.peek(), u'c')
        self.assertEqual(stack.size(), 1)

    def test_popArgs(self):
        """
        Values popped for use as function arguments appear in the correct order.
        """
        self.assertEqual(self.makeStack().popArgs(1), [u'arg3'])
        self.assertEqual(self.makeStack().popArgs(2), [u'arg2', u'arg3'])
        self.assertEqual(self.makeStack().popArgs(3), [u'arg1', u'arg2', u'arg3'])

    def test_prettyFormat(self):
        """
        Pretty-formatting the stack results in correctly formatted output.
        """
        stack = self.makeStack()
        format = u'''\
--> u'arg3'
    u'arg2'
    u'arg1'
'''
        self.assertEqual(stack.prettyFormat(), format)
