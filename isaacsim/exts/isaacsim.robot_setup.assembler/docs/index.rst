..
    This file was auto-generated by the 'repo_extension_docs' tool.
    Run 'repo extension_docs --help' for more details.

..
    [begin reference autogenerated]

.. _ext_isaacsim_robot_setup_assembler:

..
    [end reference autogenerated]

..
    [begin title autogenerated]

[isaacsim.robot_setup.assembler] Robot Assembler
################################################

..
    [end title autogenerated]

..
    [begin deprecation autogenerated]
..
    [end deprecation autogenerated]

..
    [begin version autogenerated]

**Version**: :guilabel:`2.1.5`

..
    [end version autogenerated]

..
    [begin description autogenerated]

Alpha version of Robot Assembler Extension: Assemble multiple Articulations into a single robot

..
    [end description autogenerated]

..
    [begin preview autogenerated]


.. image:: ../data/preview.png
    :align: center
    :alt: Preview


..
    [end preview autogenerated]

..
    [begin enable-extension autogenerated]


Enable Extension
================

The extension can be enabled (if not already) in one of the following ways:

.. tab-set::
    .. tab-item:: Command-line interface
        :sync: tab_cli

        Define the next entry as an application argument from a terminal.

        .. code-block:: bash

            APP_SCRIPT.(sh|bat) --enable isaacsim.robot_setup.assembler

    .. tab-item:: Experience/extension configuration
        :sync: tab_toml

        Define the next entry under ``[dependencies]`` in an experience (``.kit``) file or an extension configuration (``extension.toml``) file.

        .. code-block:: ini

            [dependencies]
            "isaacsim.robot_setup.assembler" = {}

    .. tab-item:: Extension Manager UI
        :sync: tab_gui

        Open the *Window > Extensions* menu in a running application instance and search for ``isaacsim.robot_setup.assembler``.
        Then, toggle the enable control button if it is not already active.


..
    [end enable-extension autogenerated]

..
    [begin usage autogenerated]
..
    [end usage autogenerated]

..
    [begin api autogenerated]

.. include:: api.rst

..
    [end api autogenerated]

..
    [begin ogn autogenerated]
..
    [end ogn autogenerated]

..
    [begin settings autogenerated]
..
    [end settings autogenerated]
