Usage
=====

Web app (discovering m2m)
=========================
To get use to the m2m toolkit, you can run it on a Streamlit Web App.

To do this, there are two options

Option 1
~~~~~~~~

* Run the following command 

.. code-block:: bash

    streamlit run app/m2m_main_page.py

* Click on a link to open the Streamlit Web App locally

This option may not work on Windows, see installation page for more informations.
  
Option 2
~~~~~~~~

* Install `Docker Desktop <https://www.docker.com/get-started/>`_
* Build the Docker image

.. code-block:: bash

    docker build -t m2m/streamlit .

* Run the Docker container

.. code-block:: bash

    docker run -p 8501:8501 m2m/streamlit

* Click on a link to open the Streamlit Web App locally

Note
~~~~
Using the Steamlit Web App is not recommended if you have large images (exceeding 200 Mb)
because you may encounter some limitations. For advanced usage, we recommend working in command line.

The Web App is only usefull for beginner users in order to provide convient
interface to discover the functionalities of the toolkit.

Command line (advanced usage)
=============================
Here a example of a typical command line usage.

Step 1 - Download a user-space reference volume (choose one or both)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Download an Allen mouse brain template at 100 microns (up to 10 microns)

.. code-block:: bash

   m2m_download_template.py allen_template_100.nii.gz -r 25

* Download an Allen mouse brain annotation at 100 microns (up to 10 microns)

.. code-block:: bash

   m2m_download_annotation.py allen_annotation_100.nii.gz labels.txt -r 25

Step 2 - Compute a transform matrix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Compute the transform matrix ``transform_50.mat`` at 50 microns, 
  given a user-space reference volume ``reference.nii.gz`` at 100 microns

.. code-block:: bash

    m2m_compute_transform_matrix.py reference.nii.gz transform_50.mat 50

Note that a transformation matrix for a specific resolution is valid only for this specific resolution.
If you want to import data (Step 3) with another resolution, you have to compute another matrix.

Step 3 - Examples of uses cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
With your reference image (e.g. ``reference.nii.gz``) and 
your resolution-specific transformation matrix (e.g. ``transform_50.mat``) , you can

* Import the projection density from the experiment id ``100140756``.

.. code-block:: bash

    m2m_import_proj_density.py --id 100140756  reference.nii.gz transform_50.mat 50

* Find crossings ROIs based on two injection positions, ``(132,133,69)`` for the first injection position 
  and ``(143,94,69)`` for the second injection position. The injection positions are given in voxel in the user space. 
  For this example, a threshold of 0.07 is used to generate the crossings mask.

.. code-block:: bash

    m2m_crossing_finder.py transform_50.mat reference.nii.gz 50 --red 132 133 69 --green 143 94 69 --injection --threshold 0.07


* Find 5 experiments ids in the Allen Mouse Brain Connectivity Atlas dataset
  given an injetion position ``(132,133,69)``. The injection position is given in voxel in the user space.
  The ids are downloaded in a csv file and can be used in ``m2m_import_proj_density.py``.

.. code-block:: bash

    m2m_experiments_finder.py 50 transform_50.mat reference.nii.gz experiments_ids.csv 132 133 69 --injection --nb_of_exps 5

Note
~~~~
The following example are shown using basic arguments. 
Consult the help of a script for more details about the other options available.

* Display the help for a script

.. code-block:: bash

    m2m_compute_transform_matrix.py --help

Alternatively, you can consult the scripts page.