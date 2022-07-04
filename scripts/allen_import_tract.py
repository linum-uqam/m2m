#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Download all streamlines for each Allen mouse brain
    connectivity atlas experiments and combine into a single tractogram

    >>> allen_import_tract id1 id2 id3 id4 ... --dir dir
   """

import argparse
import numpy as np
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
    p.add_argument('ids', type=int, nargs='+',
                   help='Experiment ids in the Allen Mouse Brain '
                        'Connectivity Atlas dataset.')
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

    # Getting allen experiments
    allen_experiments = get_mcc(args)[0]

    # Verifying experiment id
    ids = allen_experiments.id
    for id in args.ids:
        if id not in ids:
            parser.error("Experiment {} doesn't exist.\n"
                         "Please check: https://connectivity.brain-map.org/"
                         "".format(id))

    # Preparing filename
    str_ids = str(args.ids[0])
    if len(args.ids) > 1:
        for i in range(1, len(args.ids)):
            str_ids += "-{}".format(args.ids[i])
    trk_ = "{}.trk".format(str_ids)
    trk_file = os.path.join(args.dir, trk_)
    check_file_exists(parser, args, trk_file)

    # Initializing and downloading the streamlines
    s = AllenStreamLines(cache_dir / "cache_streamlines")
    s.download(args.ids)

    # Save the streamlines as a .trk file
    s.download_tract(trk_file)


if __name__ == "__main__":
    main()
