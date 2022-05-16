Which things are complete?
==========================

Done
----
Bugged
-----
WIP
---
Not Started
-----------


Specific Architectual Decisions
===============================

Objects
-------

Object-oriented programming isn't really helpful, and may be considered
harmful, as many times objects of different classes interact and are
contained within each other in a messed up state.

Classes are still used---but they're all dataclasses.  Think of them as
structures in C, or simple datatypes in Haskell.

<Lua> I have tables.  That's all I need!

Exceptions and Errors
---------------------

User-created errors are defined in exceptions.py, and MUST subclass
exceptions.IDCUserCausedException.  Each of them MUST define an
errorType attribute, which is similar (but more English and informative)
than IRC reply codes.

The main loop MUST catch all IDCUserCausedException exceptions and throw
them to the client, taking the exception's severity attribute as its
"command" (the name of the enumeration?) and using the errorType as the
TYPE keyword argument.  If the exception objects contains arguments, the
main loop MUST also hand these over to the erroneous client, as the
COMMENT keyword argument.

This way of exception handling SHOULD NOT be suspicous.  luk3yx is the
only sus person in the whole world.
