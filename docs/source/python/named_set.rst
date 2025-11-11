NamedSet
========

Utility for simplifying access to a dict where the key is a property of
the value.  e.g.

.. code-block:: python3

   obj = ValuedClass("name", "value")

   d: dict[str, ValuedClass] = {}
   d[obj.name] = obj
   # becomes
   ns: NamedSet[ValuedClass] = NamedSet()
   ns.add(obj)

.. module:: riscv_formal.named_set

.. autoclass:: NamedSet
   :show-inheritance:
   :members:

.. autoclass:: NamedClass

.. autoclass:: NC


Exceptions
----------

.. autoclass:: KeyMismatchError
   :show-inheritance:

.. autoclass:: KeyExistsError
   :show-inheritance:
