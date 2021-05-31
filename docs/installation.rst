Installation
============

Installing
----------

**Regen** currently runs on Python 3.6+, earlier versions of Python are not supported.

There are different ways to install **regen**, but the simplest and recommended way is via ``pip``:

.. code-block::

    python -m pip install regen

Also note that some operation systems will require you prefix the above command with ``sudo`` in order to install system-wide. You can append ``--user`` to install command to install at user level bias.

.. code-block::

    python -m pip install --user regen

Or you can use virtual environment to isolate the installation with your system. This way is at project/folder level, so that it wil not conflict with other Python packages' requirement. This is not covered in this document.

Dependencies
------------

When regen is installed, the following dependent Python packages should be automatically installed:

- `Jinja2 <https://pypi.org/project/Jinja2/>`_, for templating support

You does no need to take any action for those dependencies, they are just listed for reference.

Upgrading
---------

Once installed from pip, you can always upgrade to the latest stable release by adding ``--upgrade`` to pip's install command:

.. code-block::

    python -m pip install --upgrade regen
