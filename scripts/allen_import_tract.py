#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Download all streamlines for each Allen mouse brain
    connectivity atlas experiments and combine into a single tractogram

    Note: The output tract will be aligned on the allen ras template.\n
          Please use allen_tract_transform.py to align your tractogram on your
          reference before using it in other scripts.

    Using a csv file from : https://connectivity.brain-map.org/

    >>> allen_import_tract --ids_csv path/to/ids.csv path/to/output.trk

    Setting ids manually:

    >>> allen_import_tract path/to/output.trk --ids id1 id2 id3 . . .
    Important: the script should be called in this specific order
   """

import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import os
import sys
from allen2tract.streamlines import AllenStreamLines
from allen2tract.control import (add_cache_arg,
                                 add_overwrite_arg,
                                 add_resolution_arg,
                                 add_reference_arg,
                                 add_matrix_arg,
                                 check_file_exists,
                                 check_input_file,
                                 get_cache_dir)
from allen2tract.allensdk_utils import (download_template_vol,
                                        get_mcc_exps)
from allen2tract.util import load_user_template

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    add_matrix_arg(p)
    add_reference_arg(p)
    g.add_argument('--ids_csv', help='Path to a csv file containing ids')
    g.add_argument('--ids', type=int, nargs='+', help='List of experiment ids.')
    p.add_argument('out_tract', help='Path to output tractogram (trk)')
    add_overwrite_arg(p)
    add_resolution_arg(p)
    add_cache_arg(p)
    return p


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Configuring cache dir
    cache_dir = get_cache_dir()

    # Loading reference
    check_input_file(parser, args.reference)
    user_vol = load_user_template(args.reference)

    # Checking file mat
    check_input_file(parser, args.file_mat)

    # Verifying output file
    check_file_exists(parser, args, args.out_tract)
    if args.ids:
        in_ids = args.ids
    if args.ids_csv:
        in_ids = pd.read_csv(args.ids_csv).id.tolist()

    # Getting allen experiments
    allen_experiments = get_mcc_exps(args.nocache)

    # Verifying experiment id
    ids = allen_experiments.id
    if any(x not in ids for x in in_ids):
        parser.error("Experiment {} doesn't exist.\n"
                     "Please check: https://connectivity.brain-map.org/"
                     "".format(id))

    # Initializing and downloading the streamlines
    s = AllenStreamLines(args.res, os.path.join(cache_dir, "cache_streamlines"))
    s.download(in_ids)

    # Downloading Allen PIR refrence template
    nrrd_file = "allen_template_{}.nrrd".format(args.res)
    allen_vol = download_template_vol(nrrd_file, args.res,
                                      args.nocache)

    # Saving the streamlines as a .trk file
    s.download_tract(args.out_tract, args.file_mat, args.reference,
                     user_vol, allen_vol, args.res)


if __name__ == "__main__":
    main()
