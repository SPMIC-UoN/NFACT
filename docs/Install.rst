Installation
============

Currently NFACT can only be installed by directly cloning the NFACT repository at https://github.com/SPMIC-UoN/NFACT directly to your local machine.

Before NFACT can be installed it needs a number of external dependencies.

External dependencies
---------------------

NFACT is written in python and works for python 3.9 - 3.11. NFACT may work for other python versions but hasn't been tested. 

To check which python version you are using::

    python3 --version

As NFACT is fully integrated into the FSL enviorment FSL is needed. To install FSL follw the install installation instructons here https://fsl.fmrib.ox.ac.uk/


Installing
------------

To install do the following steps

1. Go to https://github.com/SPMIC-UoN/NFACT
2. Click the green code button and choose how you want to download NFACT
3. Set up a python virtual enviorment (recommend)::

    python3 -m venv venv
4. Activate the virtual enviorment if using::

    source venv/bin/activate
5. Change into the NFACT folder and install::

    cd NFACT
    pip3 install . (only CPU)
    pip3 install .[gpu] (if you have an NVIDIA GPU and want to use it)
    pip3 install -e .[dev] (if you plan to work on NFACT)
6. Check NFACT is installed by running::

    nfact
7. Enjoy!
