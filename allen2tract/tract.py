import numpy as np
from dipy.io.streamline import load_tractogram, save_tractogram
from dipy.tracking.utils import near_roi

from allen2tract.util import load_avgt


def get_allen_tract():
    """
    Load avgt_wildtype_tractogram.trk
    """
    fname = "./data/avgt/avgt_wildtype_tractogram.trk"
    return load_tractogram(fname)


def get_streamlines():
    """
    Get streamlines datas of the tractogram
    """
    return get_allen_tract()[0]


def get_header():
    """
    Get metadatas of the tractogram
    """
    return get_allen_tract()[1]


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
    # Getting streamlines of the avgt allen tractogram
    streamlines = get_streamlines()

    # Filtering streamlines
    # Keeping only the ones that pass through the roi
    through_roi = near_roi(
        streamlines=streamlines,
        affine=load_avgt().affine,
        region_of_interest=mask
    )

    # Writting streamlines array sequence
    streamlines_through_roi = []
    for i in range(len(streamlines)):
        if through_roi[i]:
            streamlines_through_roi.append(streamlines[i])

    # Saving the tractogram
    save_tractogram(
        fname=fname,
        streamlines=streamlines_through_roi,
        affine=np.eye(4),
        header=get_header()
    )




