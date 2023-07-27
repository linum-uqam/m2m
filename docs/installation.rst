Installation
============

In a Python virtual environment (or on your machine), run the following commands

.. code-block:: bash

    git clone https://github.com/linum-uqam/m2m.git
    cd m2m
    pip install -e .

Notes
=====

Python version
~~~~~~~~~~~~~~
The toolkit support Python >= 3.7. 
However, if you encouter any issue with the installation, prefer using 3.7.

Windows
~~~~~~~
The toolkit does not support Windows native installation
due to some dependencies. However, it is possibile to use it in a WSL.

To download WSL, open a command prompt (or Windows PowerShell) as an administrator and run

.. code-block:: bash

    wsl --install

Then follow the instructions. 

For more details, check the `official documentation <https://learn.microsoft.com/en-us/windows/wsl/install/>`_

Also, it can be convient to use `Windows Terminal <https://www.microsoft.com/store/productId/9N0DX20HK701/>`_

Additional dependencies
~~~~~~~~~~~~~~~~~~~~~~~

You will probably need to install these additional dependencies before installing the package

* MacOS

.. code-block:: bash

    brew install libpng openblas lapack gfortran

* Linux (or WSL)

.. code-block:: bash

    sudo apt-get install libpng-dev libblas-dev liblapack-dev

* Conda

.. code-block:: bash

    conda install libpng libblas liblapack