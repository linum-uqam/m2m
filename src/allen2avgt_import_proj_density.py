#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description of this script.
The description of the script should be almost at the beginning, between triple quotes.
It can be referred in the ArgumentParser constructor as __doc__.
"""

import argparse
from email.policy import default
import logging

import os
from pathlib import Path

from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
import nibabel as nib
import nrrd
import numpy as np
import ants

EPILOG = """
[1] Made by.., Subject..., Date... 
"""

def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                description=__doc__)
    p.add_argument('experiment_id',
                    help='Id of the experiment in Allen Mouse Brain Connectivity Atlas. ')
    p.add_argument('-r', '--res', type=int, default=100, choices=[25, 50, 100],
                    help='Base resolution (µm) of the projection density to download. \n'
                         'Note: The final resolution will be 70µm anyways.')
    p.add_argument('-d', '--dir', default=".",
                    help='Absolute path of the ouptut file.')
    p.add_argument('-i', '--interp', default='NN',choices=['NN, bS'],
                    help='Interpolation method. \n'
                         'NN : NearestNeighbor \n'
                         'bS : bSpline')
    p.add_argument('-f', dest='overwrite', action="store_true",
                    help='Force overwriting of the output file.')                   

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()


if __name__ == "__main__":
    main()