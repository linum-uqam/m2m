Installation
============

We recommend using Anaconda and to install m2m in a separate environment. Execute the following command.

.. code-block:: bash

    git clone https://github.com/linum-uqam/m2m.git
    cd m2m
    conda env create -f environment.yml
    conda activate m2m
    pip install -e .

Update
======

To update the toolkit, execute the following command.

.. code-block:: bash

    conda activate m2m
    git pull
    pip install -e .  # This command is necessary only if the requirements have changed

Notes
=====

Python version
~~~~~~~~~~~~~~
The toolkit support Python >= 3.10.

Windows
~~~~~~~
The toolkit does not support Windows native installation due to some dependencies. However, it is possible to use it in a WSL.

To download WSL, open a command prompt (or Windows PowerShell) as an administrator and run

.. code-block:: bash

    wsl --install

Then follow the instructions. 

For more details, check the `official documentation <https://learn.microsoft.com/en-us/windows/wsl/install/>`_

Also, it can be convient to use `Windows Terminal <https://www.microsoft.com/store/productId/9N0DX20HK701/>`_