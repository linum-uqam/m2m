from calendar import c
import numpy as np
import gzip
import json
import requests
import nibabel as nib
from pathlib import Path
from allen2tract.tract import save_tract


class AllenStreamLines(object):
    """
    Class to work with the Allen Mouse Brain Connectivity Streamlines
    Adapted from : https://github.com/BrancoLab/BrainRender
    """
    def __init__(self, directory="./streamlines", cache=True):
        """
        Downloads and save Allen Mouse brain streamlines as .trk files

        Parameters
        ----------
        directory : str, Path()
            Directory used to cache the streamline files.
        cache : boolean
            Keep the raw streamline json files into cache.
        """
        # We are using the streamlines cache from neuroinformatics.nl
        self.template_streamline_json_url = "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_{:d}.json.gz"
        self.data = []
        self.files = []
        self.cache = cache
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.reference = "data/allen/allen_template_50_ras.nii.gz"

    def download(self, experiment_ids, force=False):
        """
        Downloads the streamline files for a list of experiment IDs.

        Parameters
        ----------
        experiment_ids: list of integers
            Allen experiment IDs.
        force: bool
            Force download, otherwise we will check the cache first.
        """

        if not isinstance(experiment_ids, (list, np.ndarray, tuple)):
            experiment_ids = [experiment_ids]

        for eid in experiment_ids:
            url = self.make_streamline_request_url(eid)
            jsonpath = self.directory / f"{eid}.json"
            self.files.append(jsonpath)
            if not jsonpath.is_file() or force:
                response = requests.get(url)

                # Write the response content as a temporary compressed file
                temp_path = self.directory / "tmp.gz"
                with open(temp_path, "wb") as temp:
                    temp.write(response.content)

                # Open in pandas and delete temp
                with gzip.open(temp_path, "rb") as f:
                    url_data = json.loads(f.read().decode('utf-8'))
                # Remove this file
                temp_path.unlink()

                # Save json
                json_object = json.dumps(url_data, indent=4)
                with open(jsonpath, "w") as outfile:
                    outfile.write(json_object)

                # Append to lists and return
                self.data.append(url_data)

                # Remove the json file if cache=False
                if not self.cache:
                    jsonpath.unlink()
            else:
                with open(jsonpath, 'r') as f:
                    self.data.append(json.load(f))

        # Updating the streamlines information
        self.n_experiments = len(self.data)
        self.n_streamlines_per_experiments = []
        for iExp in range(self.n_experiments):
            self.n_streamlines_per_experiments.append(
                len(self.data[iExp]['lines']))

        # Convert the streamlines to a list of ndarrays
        # 1st dim is the number of points, 2nd dim is the xyz position
        s = []
        for iExp in range(self.n_experiments):
            for iStream in range(self.n_streamlines_per_experiments[iExp]):
                streamline = self.data[iExp]['lines'][iStream]

                n_positions = len(streamline)
                this_streamline = np.zeros((n_positions, 3), dtype=np.float32)

                for j in range(n_positions):
                    this_streamline[j, 0] = streamline[j]['x']
                    this_streamline[j, 1] = streamline[j]['y']
                    this_streamline[j, 2] = streamline[j]['z']

                s.append(this_streamline)

        self.streamlines_list = s

    def print_info(self):
        """
        Print some informations about the downloaded streamlines
        """
        print("Number of experiments:", self.n_experiments)
        print("Number of streamlines per experiments")
        for i, n_streamlines in enumerate(self.n_streamlines_per_experiments):
            print(f"  Experiment {i} has {n_streamlines} streamlines")

    def make_streamline_request_url(self, experiment_id):
        """
        Get url of JSON file for an experiment

        Parameters
        ----------
        experiment_id: int
            Allen experiment ID number.

        Return
        ------
        str: url_request
        """
        return self.template_streamline_json_url.format(experiment_id)

    def download_tract(self, filename):
        """
        Save the streamlines as a .trk file

        Parameters
        ----------
        filename: str
            Full path to the output trk.
        """
        # Define the reference
        reference = self.reference

        # Prepare the output file
        filename = Path(filename)
        assert filename.suffix == ".trk", "The filename must end with .trk"
        filename.parent.mkdir(parents=True, exist_ok=True)

        # Load the reference and extract the pixel dimensions
        # Assuming that pixdim is in mm
        pixdim = nib.load(reference).header["pixdim"]
        rx = pixdim[1] * 1e3  # X resolution in micron
        ry = pixdim[2] * 1e3  # Y resolution in micron
        rz = pixdim[3] * 1e3  # Z resolution in micron

        # Convert the streamline positions to the right resolution
        sl = []
        for i in range(len(self.streamlines_list)):
            this_s = self.streamlines_list[i].copy()
            # PIR to RAS
            this_s[:, 1] = self.streamlines_list[i][:, 0] / rx
            this_s[:, 2] = self.streamlines_list[i][:, 1] / -ry
            this_s[:, 0] = self.streamlines_list[i][:, 2] / -rz
            # this_s[:, 0] = self.streamlines_list[i][:, 0] / rx
            # this_s[:, 1] = self.streamlines_list[i][:, 1] / ry
            # this_s[:, 2] = self.streamlines_list[i][:, 2] / rz
            sl.append(this_s)

        # Save the tractogram
        save_tract(
            fname=str(filename),
            streamlines=sl,
            reference=reference,
            check_bbox=False,
            )

    def remove_cache(self):
        """
        Remove the streamlines cache
        """
        for f in self.files:
            f.unlink()
