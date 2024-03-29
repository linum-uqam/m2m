import os


def add_overwrite_arg(parser):
    parser.add_argument(
        '-f', dest='overwrite', action='store_true',
        help='Force overwriting of the output files.')


def add_resolution_arg(parser):
    parser.add_argument('res', type=int,
                        choices=[10, 25, 50, 100],
                        help='Resolution (in micron) of the Allen files \n'
                             'Please use the same resolution as '
                             'the transformation matrix.')


def add_output_dir_arg(parser):
    parser.add_argument('-d', '--dir', default=".",
                        help='Path of the ouptut file directory is . '
                             'by default.\n'
                             'Using --dir <dir> will change '
                             'the output file\'s '
                             'directory or create a new one '
                             'if does not exits.')


def add_cache_arg(parser):
    parser.add_argument('-c', '--nocache', action="store_true",
                        help='Update the Allen Mouse Brain Connectivity Cache')


def add_reference_arg(parser):
    parser.add_argument('reference',
                        help='Path to reference volume (.nii.gz)')


def add_matrix_arg(parser):
    parser.add_argument('file_mat',
                        help='Path to transform matrix (.mat)')


def check_file_exists(parser, args, path):
    """
    Verify that output does not exist or that if it exists, -f should be used.
    If not used, print parser's usage and exit.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
        Parser.
    args: argparse namespace
        Argument list.
    path: string or path to file
        Required path to be checked.
    """
    if os.path.isfile(path) and not args.overwrite:
        parser.error('Output file {} exists. Use -f to force '
                     'overwriting'.format(path))

    path_dir = os.path.dirname(path)
    if path_dir and not os.path.isdir(path_dir):
        parser.error('Directory {}/ \n for a given output file '
                     'does not exists.'.format(path_dir))


def check_input_file(parser, path):
    """
    Assert that all inputs exist. If not, print parser's usage and exit.

    Parameters
    ----------
    parser: argparse.ArgumentParser object
        Parser.
    path: string or path to file
        Required path to be checked.
    """
    if not os.path.isfile(path):
        parser.error('Input file {} does not exist'.format(path))


def get_cache_dir():
    return os.path.join(os.path.expanduser('~'), '.m2m')


def get_cached_dir(dir):
    return os.path.join(get_cache_dir(), dir)
