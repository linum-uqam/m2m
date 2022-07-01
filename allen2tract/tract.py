import numpy as np
from dipy.io.streamline import load_tractogram, save_tractogram
from dipy.tracking.utils import near_roi

from allen2tract.util import load_avgt


def get_avgt_wildtype():
    """
    Load avgt_wildtype_clean.trk
    """
    fname = "./data/avgt/avgt_wildtype_clean.trk"
    return load_tractogram(fname)


def get_tract(fname):
    return load_tractogram(fname)


def get_streamlines(tract):
    """
    Get streamlines datas of the tractogram
    """
    return tract[0]


def get_header(tract):
    """
    Get metadatas of the tractogram
    """
    return tract[1]


def save_tract(fname, streamlines,
               affine, header):
    save_tractogram(
        fname=fname,
        streamlines=streamlines,
        affine=affine,
        header=header
    )


def filter_tract_near_roi(mask, fname):
    """
    Save a bundle of streamlines passing
    through the binary mask

    Parameters
    ----------
    mask: ndarray
        Binary mask.
    fname: string
        Path to the output file
    """
    # Getting avgt wildtype tractogram
    avgt_wildtype = get_avgt_wildtype()

    # Filtering streamlines
    # Keeping only the ones that pass through the roi
    through_roi = near_roi(
        streamlines=get_streamlines(avgt_wildtype),
        affine=load_avgt().affine,
        region_of_interest=mask
    )

    # Writting streamlines array sequence
    streamlines_through_roi = []
    for i in range(len(get_streamlines(avgt_wildtype))):
        if through_roi[i]:
            streamlines_through_roi.append(
                get_streamlines(avgt_wildtype)[i])

    # Saving the tractogram
    save_tract(
        fname=fname,
        streamlines=streamlines_through_roi,
        affine=np.eye(4),
        header=get_header(avgt_wildtype)
    )



