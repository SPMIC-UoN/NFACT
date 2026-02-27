from NFACT.base.imagehandling import imaging_type, get_cifti_data
from NFACT.base.utils import nprint, colours, error_and_exit
from NFACT.base.matrix_handling import thresholding
import numpy as np
import nibabel as nb
import os
import glob
from tqdm import tqdm
import pandas as pd


class Component_loading:
    """
    Class to calculate component loadings
    between group and subjects components

    Usage
    -----
    loadings = Component_loading(group_white, group_grey, dim)
    component_loadings = loadings.run(subjects_output)
    """

    def __init__(
        self,
        white_group_component_path: str,
        grey_group_component_path: list,
        dim: str,
        threshold: int,
    ) -> None:
        """
        Calculate component loadings
         between group and subjects components

        Parameters
        ---------
        white_group_component_path: str
            path to wm group component
        grey_group_component_path: list
            list of path(s) to gm group
            components
        dim: str
            number of components
        threshold: int
            threshold value
        """
        self.white_group_component_path = white_group_component_path
        self.grey_group_component_path = grey_group_component_path
        self.dim = dim
        self.threshold = threshold

    def run(self, subject_paths: list) -> dict[np.ndarray]:
        """
        Run method of component loadings

        Parameters
        -----------
        subject_paths: list
            list of subject paths

        Returns
        -------
        dict: dictionary object
           dict of np.arrays of
           white and grey component
           loadings
        """
        self.__load_group_components()
        self.group_white_mean = self.group_white.mean(axis=0)
        self.group_white_std = self.group_white.std(axis=0)
        self.group_grey_mean = self.group_grey.mean(axis=0)
        self.group_grey_std = self.group_grey.std(axis=0)
        w_corr = []
        g_corr = []
        for subject in tqdm(
            subject_paths, desc="Component Loadings", colour="magenta", unit=" Subject"
        ):
            component_loadings = self._subject_correlations(subject)
            w_corr.append(component_loadings["w"])
            g_corr.append(component_loadings["g"])

        return {
            "white_correlations": np.vstack(w_corr),
            "grey_correlations": np.vstack(g_corr),
        }

    def __load_group_components(self):
        """
        Method to Load group components
        """
        group_white = self.__volume(self.white_group_component_path)
        group_grey = self.__process_grey(self.grey_group_component_path)
        self.group_white = self.__threshold_values(group_white)
        self.group_grey = self.__threshold_values(group_grey)

    def __threshold_values(self, array: np.ndarray):
        if self.threshold > 0:
            return thresholding(array, self.threshold)
        return array

    def __process_grey(self, grey_paths: list) -> np.ndarray:
        """
        Method to process gm files according
        to imaging type

        Parameters
        ----------
        grey_paths: list
            list of grey matter
            files

        Returns
        -------
        np.ndarry: array
            Array of grey matter components
            n by component number
        """
        if imaging_type(grey_paths[0]) == "cifti":
            return self.__cifti(grey_paths[0])
        loaders = {"nifti": self.__volume, "gifti": self.__gifti}
        grey_component = []
        for grey_img in grey_paths:
            grey_comp = loaders[imaging_type(grey_img)](grey_img)
            grey_component.append(grey_comp)
        return np.vstack(grey_component)

    def __volume(self, vol_path: str):
        """
        Method to load volume data

        Parameters
        ----------
        vol_path: str
            path to volume file

        Returns
        -------
        np.ndarry: array
            Array of volume data
            n by component number
        """
        vol_data = nb.load(vol_path).get_fdata()
        return vol_data.reshape(-1, vol_data.shape[-1])

    def __gifti(self, gifti_path: str) -> np.ndarray:
        """
        Method to load gifti data

        Parameters
        ----------
        gifti_path: str
            path to gifti file

        Returns
        -------
        np.ndarry: array
            Array of surface data
            n by component number
        """
        gifti_img = nb.load(gifti_path)
        return np.column_stack([darray.data for darray in gifti_img.darrays])

    def __cifti(self, cifti_path: str) -> np.ndarray:
        """
        Method to load cifti data

        Parameters
        ----------
        cifti_path: str
            path to cifti file

        Returns
        -------
        np.ndarry: array
            Array of cifti data
            n by component number
        """
        gm_dat = get_cifti_data(cifti_path)
        component_data = np.concatenate([gm_dat["L_surf"], gm_dat["R_surf"]], axis=0)
        if "vol" in gm_dat.keys():
            vol_flat = gm_dat["vol"].get_fdata().reshape(-1, gm_dat["vol"].shape[-1])
            component_data = np.concatenate([component_data, vol_flat], axis=0)
        return component_data

    def __get_subject_img(self, subject_path: str) -> dict[str]:
        """
        Method to get a subjects files
        by type

        Parameters
        ----------
        subject_path: str
            subject path

        Returns
        -------
        dict: dictionary
            dict of file paths
            by component type
        """
        basename = os.path.basename(subject_path)
        return {
            "grey_components": glob.glob(
                os.path.join(
                    os.path.dirname(subject_path), f"G_{basename}_dim{self.dim}*"
                )
            ),
            "white_component": glob.glob(
                os.path.join(
                    os.path.dirname(subject_path), f"W_{basename}_dim{self.dim}*"
                )
            ),
        }

    def __correlating(
        self,
        subject_data: np.ndarray,
        group_data: np.ndarray,
        group_mean: np.ndarray,
        group_std: np.ndarray,
    ) -> np.ndarray:
        """
        Method to run correaltion between group and subject
        by components

        Parameters
        ----------
        subject_data: np.ndarray
            subject data
        group_data: np.ndarray
            group data
        group_mean: np.ndarray
            group mean
        group_std: np.ndarray
            group std

        Returns
        -------
        np.ndarray: np.ndarray
            array of component loadings
        """

        subj_mean = subject_data.mean(axis=0)
        subj_std = subject_data.std(axis=0)
        cov = ((subject_data - subj_mean) * (group_data - group_mean)).sum(axis=0) / (
            subject_data.shape[0] - 1
        )
        return cov / (subj_std * group_std)

    def _subject_correlations(self, subject_path: str) -> dict[np.ndarray]:
        """
        Method to get the correlation values for
        each subject.

        Parameters
        ----------
        subject_path: str
            path to subject data

        Returns
        -------
        dict: dictionary[np.ndarray]
            dictionary of a subjects
            component loadings by type
        """
        subject_images = self.__get_subject_img(subject_path)
        w_subject = self.__volume(subject_images["white_component"][0])
        if self.threshold > 0:
            w_subject = self.__threshold_values(w_subject)
        w_subject_correlations = self.__correlating(
            w_subject, self.group_white, self.group_white_mean, self.group_white_std
        )
        del w_subject
        g_subject = self.__process_grey(subject_images["grey_components"])
        if self.threshold > 0:
            g_subject = self.__threshold_values(g_subject)
        g_subject_correlations = self.__correlating(
            g_subject, self.group_grey, self.group_grey_mean, self.group_grey_std
        )
        del g_subject
        return {"w": w_subject_correlations, "g": g_subject_correlations}


def save_components(
    matrix: np.ndarray,
    filename: str,
    file_path: str,
    subjects: list,
    no_csv: bool = False,
) -> None:
    """
    Function to save component values

    Parameters
    ----------
    matrix: np.ndarray
        matrix of comp loadings
        to save
    filename: str
        name of file to save
    file_path: str
        where to save the file
    subjects: list
        list of subjects (really needed
        for csv not for np array)
    no_csv: bool
       save component loadings as np array
       rather than csv

    Returns
    -------
    None
    """
    save_path = os.path.join(file_path, filename)
    if no_csv:
        np.save(f"{save_path}.npy", matrix)
        return None
    subject_ids = [os.path.basename(sub) for sub in subjects]
    df = pd.DataFrame(matrix, columns=[f"comp_{idx}" for idx in range(matrix.shape[1])])
    df.insert(0, "subject", subject_ids)
    df.to_csv(f"{save_path}.csv", index=False)


def component_loadings_main(args: dict) -> None:
    """
    Main component loading function

    Parameters
    ----------
    args: dict
        dictionary of command line
    stats dir: str
        path to stats directory

    Returns
    -------
    None

    """
    col = colours()
    nprint(f"\n{col['pink']}Running:{col['reset']} Component loadings")
    nprint("-" * 100)

    try:
        loadings = Component_loading(
            args["group_white"], args["group_grey"], args["dim"], args["threshold"]
        )
        component_loadings = loadings.run(args["dr_output"])
    except Exception as e:
        error_and_exit(False, f"Unable to calculate component loadings due to {e}")

    nprint(f"\n{col['pink']}Saving:{col['reset']} Component loadings")
    nprint("-" * 100)

    try:
        save_components(
            component_loadings["white_correlations"],
            "W_component_loadings",
            args["stats_dir"],
            args["dr_output"],
            args["no_csv"],
        )
        save_components(
            component_loadings["grey_correlations"],
            "G_component_loadings",
            args["stats_dir"],
            args["dr_output"],
            args["no_csv"],
        )
    except Exception as e:
        error_and_exit(False, f"Unable to Save component loadings due to {e}")
