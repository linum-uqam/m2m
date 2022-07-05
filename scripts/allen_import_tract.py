#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Download all streamlines for each Allen mouse brain
    connectivity atlas experiments and combine into a single tractogram

    Note: The output tract will be aligned on the allen ras template.\n
          Please use allen_tract_transform.py to align your tractogram on your
          reference before using it in other scripts.

    Using a csv file from : https://connectivity.brain-map.org/

    >>> allen_import_tract --csv_ids path/to/ids.csv path/to/output.trk

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
sys.path.append(".")

from allen2tract.streamlines import AllenStreamLines

from allen2tract.control import (add_cache_arg, add_output_dir_arg,
                                 add_overwrite_arg,
                                 check_file_exists)

from allen2tract.util import get_mcc

EPILOG = """
Author : Mahdi
"""


def _build_arg_parser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                epilog=EPILOG, description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--ids_csv', help='Path to a csv file containing ids')
    g.add_argument('--ids', type=int, nargs='+',help='List of experiment ids.')
    p.add_argument('out_tract', help='Path to output tractogram (trk)')
    add_output_dir_arg(p)
    add_overwrite_arg(p)
    add_cache_arg(p)
    return p


def main():
    # Building argparser
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Configuring output directory
    args.dir = Path(args.dir)
    args.dir.mkdir(exist_ok=True, parents=True)

    # Configuring cache dir
    cache_dir = Path().home() / "allen2tract/data"

    # Verifying output file
    check_file_exists(parser, args, args.out_tract)
    if args.ids:
        in_ids = args.ids
    if args.ids_csv:
        in_ids = pd.read_csv(args.ids_csv).id.tolist()

    # Getting allen experiments
    allen_experiments = get_mcc(args)[0]

    # Verifying experiment id
    ids = allen_experiments.id
    for id in in_ids:
        if id not in ids:
            parser.error("Experiment {} doesn't exist.\n"
                         "Please check: https://connectivity.brain-map.org/"
                         "".format(id))

    # Initializing and downloading the streamlines
    s = AllenStreamLines(cache_dir / "cache_streamlines")
    s.download(in_ids)

    # Save the streamlines as a .trk file
    s.download_tract(args.out_tract)


if __name__ == "__main__":
    main()
