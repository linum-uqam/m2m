import gdown
import os
import requests
import shutil
from pathlib import Path

from m2m.control import get_cached_dir

GDRIVE_BASE_URL = "https://drive.google.com/uc?id={}"

data_ids = {
    "allen_tractogram_wildtype_50um.trk": "17WP0F1POmxWToKLV0Dl9aD5MsMMyQYlt",
    "allen_template_ras_50um.nii.gz": "1hX_oW8TLH6aPMvdk7-fuikeuJhKIASa2",
}

def download_to_cache(data_id: str, force_download: bool=False, dry_run=False) -> str:
    """ Download the Allen Mouse Brain Tractogram

    Returns
    -------
    Filename

    """
    assert data_id in data_ids.keys(), f"Available data: {data_ids.keys()}"
    url = GDRIVE_BASE_URL.format(data_ids[data_id])
    local_filename = Path(get_cached_dir("data")) / data_id

    if dry_run:
        return str(local_filename)

    if not local_filename.is_file() or force_download:
        local_filename.parent.mkdir(exist_ok=True, parents=True)
        gdown.download(url, str(local_filename))
    else:
        print("Already in cache")

    return str(local_filename)