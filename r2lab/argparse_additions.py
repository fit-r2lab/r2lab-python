#!/usr/bin/env python3

"""
The classes in this module extend the argparse ecosystem.

Purpose is to enable the creation of CLI options that would behave a bit like
``action=append``, but with a check on choices, that is to say:

* **accumulative** : *dest* holds a list of strings - it's possible to use the type system as well
* **restrictive** : all elements in the list must be in *choices*
* optionnally **reset-able** : it should be possible for add_argument to specify a non-void default
    and in this case we need a means for the CLI to explicitly void the value

In practical terms, we want to specify one or several values for a parameter
that is itself constrained, like an antenna mask that must be among '1', '3' and '7'

As of this writing at least, using 'append' as an action won't work
it is possible to write a code that uses
action=append, choices=['a', 'b', 'c'] and default=['a', 'b']
but then defaults are always returned...

**Resetting**

The actual syntax offered by your CLI for actually resetting the target list may vary from one need to another

As an example, let us consider a use case where we have 2 physical
phones, and we want to be able to select any number of them. Let us
further imagine that the code expects that selection to be expressed as a
list of integers in the *1-2* range. 

So we'd like to say e.g.:

``parser.add_argument("-p", "--phones", default=[1], choices=(1, 2), type=int, ...)``

And with that in place, we'd like to have

* no option: results in ``phones = [1]``
* ``-p 2``:      ``phones = [2]``
* ``-p 1 -p 2``: ``phones = [1, 2]``
* ``-p 0``:      ``phones = []``

Now, it is **not possible** to adopt a convention where e.g.

* ``-p none`` would mean ``phones = []`` 

because we have this ``type = int`` setting to ``add_argument``, which
causes the string ``"none"`` to be rejected as an input.

"""

import argparse


class ListOfChoices(argparse.Action):

    """
    The generic class assumes there is a means_resetting method
    that is used to check for special incoming values that mean resetting

    Example:
        Not resettable::

            parser.add_argument(choices=('1', '2', '3', '4'), default=['1', '2'],
                                typeaction=ListOfChoices)

    """

    def __init__(self, *args, **kwds):
        # initialize list of arguments
        self.result = []
        # initialize superclass
        super().__init__(*args, **kwds)

    def _means_resetting(self, value):
        """
        Override this method if you want special values to mean resetting
        """
        return False

    def __call__(self, parser, namespace, value, option_string=None):
        # check if this means resetting
        if self._means_resetting(value):
            self.result = []
        else:
            self.result.append(value)
        # in any case
        setattr(namespace, self.dest, self.result)


class ListOfChoicesNullReset(ListOfChoices):

    """
    Example:
       Resettable with ``-p 0``::

           parser.add_argument(choices=(1, 2, 3, 0), type=int,
                               default=[1],
                               typeaction=ListOfChoicesNullReset)

    **Note** make sure to mention ``0`` in the `choices`.
    """

    def _means_resetting(self, value):
        return value <= 0
