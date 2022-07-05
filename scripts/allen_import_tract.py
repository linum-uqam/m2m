#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Download all streamlines for each Allen mouse brain
    connectivity atlas experiments and combine into a single tractogram

    Note: The output tract will be aligned on the allen ras template.\n
          Please use allen_tract_transform.py to align your tractogram on your
          reference before using it in other scripts.

    >>> allen_import_tract path/to/ids.csv path/to/output.trk
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
    p.add_argument('in_ids', help='Path to a csv file containing ids')
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
    in_ids = pd.read_csv(args.in_ids).id.tolist()

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
