nfact_gui
=========

**nfact_gui** is the native Graphical User Interface (GUI) for the NFACT suite. Built purely with standard library ``tkinter``, it provides an intuitive, professional scientific workspace adhering to the signature NFACT visual style.

Launching the GUI
-----------------

The GUI can be launched directly from the terminal:

.. code-block:: bash

   nfact_gui

CLI Options
-----------

.. list-table::
   :widths: 25 20 55
   :header-rows: 1

   * - Argument
     - Type
     - Description
   * - ``--theme {dark, light}``
     - String
     - Initial theme (default: ``dark``).
   * - ``-c``, ``--config``
     - File path
     - Pre-populate the GUI with an initial pipeline configuration file.
   * - ``-w``, ``--workdir``
     - Directory path
     - Set the initial working directory for file and folder pickers.
   * - ``-hh``, ``--verbose_help``
     - Flag
     - Display extended usage help and ASCII splash screen in the terminal.

Key Capabilities
----------------

1. **Dark & Light Mode**: Seamless runtime switching between a deep obsidian dark theme and a soft lavender-white light theme using NFACT's authentic color palette (Deep Pink, Amethyst, Plum, Lavender).
2. **Whole Pipeline or Standalone Execution**:
   - **Full Pipeline (``nfact``)**: Interactive 4-stage flow bar allowing users to run the end-to-end pipeline or toggle individual stages on/off (e.g., skip pre-processing with ``--pp_skip``, skip QC with ``--qc_skip``, or skip dual regression with ``--dr_skip``).
   - **Dedicated Module Tabs**: Dedicated parameter workspaces for ``nfact_pp``, ``nfact_decomp``, ``nfact_Qc``, ``nfact_dr``, ``nfact_stats``, and ``nfact_config``.
3. **Live Command Preview & Copy**: Real-time display of the exact CLI command constructed by widget inputs, with one-click copying to clipboard for cluster submission scripts.
4. **Interactive Runlog Console**:
   - **Live Runlog**: Streams subprocess stdout/stderr with full ANSI terminal color rendering (including ASCII splashes) and carriage return (``\\r``) progress bar support.
   - **Command History**: Timestamped table tracking all executed commands, working directories, durations, and exit statuses.
   - **Saved Log Inspector**: Browse and inspect historical ``.log`` files generated in ``<outdir>/nfact/logs/``.
5. **Interactive JSON Config Editor**: Built-in editor to inspect, validate, format, and save ``.config`` JSON files directly inside the GUI.
