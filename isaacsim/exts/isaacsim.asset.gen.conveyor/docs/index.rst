..
    This file was auto-generated by the 'repo_extension_docs' tool.
    Run 'repo extension_docs --help' for more details.

..
    [begin reference autogenerated]

.. _ext_isaacsim_asset_gen_conveyor:

..
    [end reference autogenerated]

..
    [begin title autogenerated]

[isaacsim.asset.gen.conveyor] Isaac Sim Conveyor belt utility
#############################################################

..
    [end title autogenerated]

..
    [begin deprecation autogenerated]
..
    [end deprecation autogenerated]

..
    [begin version autogenerated]

**Version**: :guilabel:`1.0.4`

..
    [end version autogenerated]

..
    [begin description autogenerated]

The Conveyor Belt Utility Extension provides an utility to turn Rigid bodies into conveyors in Omniverse Isaac Sim. It provides an Omnigraph Node that support configuring a mesh asset into a conveyor belt Rigid Body in simulation, and commands to create the conveyor belt Omnigraph programatically.

..
    [end description autogenerated]

..
    [begin preview autogenerated]
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

            APP_SCRIPT.(sh|bat) --enable isaacsim.asset.gen.conveyor

    .. tab-item:: Experience/extension configuration
        :sync: tab_toml

        Define the next entry under ``[dependencies]`` in an experience (``.kit``) file or an extension configuration (``extension.toml``) file.

        .. code-block:: ini

            [dependencies]
            "isaacsim.asset.gen.conveyor" = {}

    .. tab-item:: Extension Manager UI
        :sync: tab_gui

        Open the *Window > Extensions* menu in a running application instance and search for ``isaacsim.asset.gen.conveyor``.
        Then, toggle the enable control button if it is not already active.


..
    [end enable-extension autogenerated]

..
    [begin usage autogenerated]
..
    [end usage autogenerated]

..
    [begin api autogenerated]
..
    [end api autogenerated]

..
    [begin ogn autogenerated]

Omnigraph Nodes
===============

The extension exposes the following Omnigraph nodes:

.. toctree::
    :glob:
    :maxdepth: 1

    ogn/*

..
    [end ogn autogenerated]

..
    [begin settings autogenerated]
..
    [end settings autogenerated]
