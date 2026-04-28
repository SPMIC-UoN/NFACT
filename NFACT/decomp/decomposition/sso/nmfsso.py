from NFACT.decomp.decomposition.sso.sso_functions import (
    compute_similairty_matrix,
    sim2dis,
    clustering_components,
    idx2centrotype,
    projection,
    cluster_scores,
    cumulative_variance,
    save_individual_components,
    save_initialisation,
)
from NFACT.decomp.decomposition.sso.sso_plotting import (
    plot_matrix,
    plot_cluster_stats,
    NMFgraph,
)
from NFACT.base.utils import nprint, colours
from NFACT.base.matrix_handling import thresholding
from NFACT.decomp.decomposition.nmf_runs import which_nmf
import numpy as np
from multiprocessing import shared_memory
from joblib import Parallel, delayed
import os
import pandas as pd
import warnings

warnings.filterwarnings("ignore")


class NMFsso:
    """
    NMFsso class. Creates can run with and
    without parallelization. This is based on
    ICAsso but paired down to suit NFACT

    Usage
    -----
    est = NMFsso(
        fdt_mat=fdt_mat,
        num_int=15,
        nmf_params=nmf_params,
        n_jobs=5
    )

    components = est.run()

    """

    def __init__(
        self,
        fdt_mat: np.ndarray,
        num_int: int,
        nmf_params: dict,
        n_jobs: int,
        gpu: bool = False,
    ) -> None:
        self.num_int = num_int
        self.nmf_params = nmf_params.copy()
        self.n_jobs = 1 if gpu else n_jobs
        self.fdt_mat = fdt_mat
        self.nmf_params["init"] = "random"
        self.col = colours()
        self.nmf_decomp = which_nmf(gpu)
        self.threshold = 3

    def _results(self) -> dict:
        """
        Method to return dict to
        store results

        Parameters
        -----------
        None

        Returns
        -------
        dict: dictionary object
            dict of grey, white lists
        """
        return {"grey": [], "white": []}

    def _run_single_shared(
        self, shm_name: str, shape: tuple, dtype: np.dtype, nmf_params: dict
    ) -> dict:
        """
        Method to run NMF via for a shared object.

        Parameters
        ----------
        shape: tuple
            shape of what fdt matrix should be
        dtype: np.dtype
            fdt mat datatype
        nmf_params: dict
            parmeters for nmf

        Returns
        -------
        tuple: tuple object
            tuple of dictionary
            objects grey and white
        """
        shm = shared_memory.SharedMemory(name=shm_name)
        fdt_mat = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
        nmf_params["random_state"] = None
        nmf_state = self.nmf_decomp(nmf_params, fdt_mat)
        shm.close()
        nmf_state["white_components"] = thresholding(
            nmf_state["white_components"], self.threshold
        )
        return nmf_state["grey_components"], nmf_state["white_components"]

    def _parallel_run(self) -> dict:
        """
        Method entry point for parallel run

        Parameters
        ----------
        None

        Returns
        -------
        dict: dictionary object
            dict of grey and white
            matter output from sso
        """
        self.shared_shape = self.fdt_mat.shape
        self.shared_dtype = self.fdt_mat.dtype
        self.shm = shared_memory.SharedMemory(create=True, size=self.fdt_mat.nbytes)
        np.ndarray(self.shared_shape, dtype=self.shared_dtype, buffer=self.shm.buf)[
            :
        ] = self.fdt_mat
        self.shm_name = self.shm.name
        os.environ["OMP_NUM_THREADS"] = "1"
        os.environ["MKL_NUM_THREADS"] = "1"
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["NUMEXPR_NUM_THREADS"] = "1"

        if self.n_jobs > self.num_int:
            self.n_jobs = self.num_int

        print(f"{self.col['light_pink']}")
        results = Parallel(n_jobs=self.n_jobs, verbose=10)(
            delayed(self._run_single_shared)(
                self.shm_name,
                self.shared_shape,
                self.shared_dtype,
                self.nmf_params,
            )
            for _ in range(self.num_int)
        )
        print(f"{self.col['reset']}\n")
        # Collect results
        nmf_sso_results = self._results()
        for grey, white in results:
            nmf_sso_results["grey"].append(grey)
            nmf_sso_results["white"].append(white)

        # Clean up shared memory
        self.shm.close()
        self.shm.unlink()

        return nmf_sso_results

    def _single_run(self) -> dict:
        """
        Single run NMF-sso method

        Parameters
        ----------
        None

        Returns
        -------
        nmf_sso_results: dict
            dict of grey and white matter_components
        """
        import sys
        import io
        import contextlib

        # ANSI: move cursor up 2 lines then erase from there to end of screen
        _UP2_CLEAR = "\033[2A\033[J"

        nmf_sso_results = self._results()
        for iterat in range(self.num_int):
            # --- Capture stdout so internal "Using: ..." prints don't scroll ---
            _buf = io.StringIO()
            with contextlib.redirect_stdout(_buf):
                self.nmf_params["random_state"] = None
                nmf_state = self.nmf_decomp(self.nmf_params, self.fdt_mat)

            _using_line = next(
                (line for line in _buf.getvalue().splitlines() if "Using:" in line),
                f"{self.col['pink']}Using:{self.col['reset']} unknown",
            )

            if iterat > 0:
                sys.stdout.write(_UP2_CLEAR)

            sys.stdout.write(
                f"{self.col['pink']}Run: {self.col['reset']}{iterat + 1}/{self.num_int}\n"
                f"{_using_line}\n"
            )
            sys.stdout.flush()

            nmf_sso_results["grey"].append(nmf_state["grey_components"])
            nmf_state["white_components"] = thresholding(
                nmf_state["white_components"].astype(np.float32), self.threshold
            )
            nmf_sso_results["white"].append(nmf_state["white_components"])

        return nmf_sso_results

    def run(self) -> dict:
        """
        Run method for NMF sso. Will run either parallel
        or single run depending on number of jobs given

        Parameters
        -----------
        None

        Returns
        -------
        nmf_sso_results: dict
            dict of grey and white matter_components
        """
        nprint(f"{self.col['pink']}NMF iterations: {self.col['reset']}{self.num_int}")
        if self.n_jobs > 1:
            nmf_sso_results = self._parallel_run()
        else:
            nmf_sso_results = self._single_run()
        return nmf_sso_results


def nmf_cluster_stats_csv(cluster_stats: dict, output_dir: str) -> None:
    """
    Function to safe cluster stats into
    a csv.

    Parameters
    ----------
    cluster_stats: dict
        output of cluster_scores()
    output_dir: str
        output directory of nfact

    Returns
    -------
    None
    """

    cluster_df = pd.DataFrame(cluster_stats)
    cluster_df = cluster_df.replace(np.nan, 0)
    cluster_df = cluster_df.rename(columns={"clusternumber": "Component"})
    cluster_df.to_csv(f"{output_dir}/cluster_stats.csv", index=False)


def nmf_sso_output_wrapper(
    output_dir: str,
    sim: np.ndarray,
    dis: np.ndarray,
    partitions: np.ndarray,
    centroids: np.ndarray,
    variance: dict,
) -> None:
    """
    Function wrapper around plotting different
    measures

    Parameters
    ----------
    output_dir: str
        output directory of nfact
    sim: np.ndarray
        similairty matrix
    dis: np.ndarray
        dis-similairty matrix
    partitions: np.ndarray
        partition of cluster labels
    centroids: np.ndarray
        array of centroids

    Returns
    -------
    None
    """
    try:
        col = colours()
        plotting_output = os.path.join(output_dir, "nfact_decomp", "sso_output")
        nprint(f"{col['light_pink']}Obtaining Projections{col['reset']}\n")
        coords = projection(dis)
        clust_score = cluster_scores(sim, partitions)
        NMFgraph(
            proj=coords,
            labels=partitions,
            internal_average=clust_score["internal_avg"],
            centroid_indices=centroids,
            output_dir=os.path.join(plotting_output, "cluster_network.tiff"),
        ).plot()
        del clust_score["internal_avg"]
        clust_score["cumulative_r2"] = variance["cumulative_r2"][
            clust_score["clusternumber"] - 1
        ]
        clust_score["per_comp"] = variance["per_comp"][clust_score["clusternumber"] - 1]
        nmf_cluster_stats_csv(clust_score, plotting_output)
        plot_matrix(
            os.path.join(plotting_output, "similarity_matrix.tiff"),
            sim,
            "Similarity Matrix",
        )
        plot_matrix(
            os.path.join(plotting_output, "dissimilarity_matrix.tiff"),
            dis,
            "Dis-Similarity Matrix",
        )
        plot_cluster_stats(
            clust_score,
            os.path.join(plotting_output, "cluster_stats.tiff"),
        )

    except Exception as e:
        nprint(f"Unable to save graphs due to: {e}")


def sso_run(fdt_matrix: np.ndarray, parameters: dict, args: dict, col: dict):
    """
    Function to run nmf-sso.

    Parameters
    ----------
    fdt_matrix: np.ndarray
        fdt_matrix to decompose
    parameters: dict
        dictionary of hyperparameters
    args: dict
        dictionary of cmd arguments
    col: dict
        dictionary of colours

    Returns
    -------
    dict:
        dictionary of grey and white matter components
    """
    results_of_comp = NMFsso(
        fdt_matrix, args["iterations"], parameters, args["n_cores"], args["gpu"]
    ).run()
    w_components = np.vstack(results_of_comp["white"])
    g_components = np.hstack(results_of_comp["grey"])
    sim = compute_similairty_matrix(w_components.astype(np.float32))
    dis = sim2dis(sim)
    partitions = clustering_components(dis, args["dim"])
    if args["cluster_save"]:
        print(f"{col['light_pink']}Saving individual clusters{col['reset']}\n")
        nfact_decomp = os.path.join(args["outdir"], "nfact_decomp")
        save_individual_components(
            clusters=partitions,
            w_components=w_components,
            g_components=g_components,
            decomp_dir=os.path.join(nfact_decomp, "group_averages"),
            output_dir=os.path.join(nfact_decomp, "sso_output", "clusters"),
            seed=args["seeds"],
            roi=args["roi"],
            coord_path=os.path.join(
                nfact_decomp, "group_averages", "coords_for_fdt_matrix2"
            ),
            cifti_save=args["cifti"],
        )
    centroids = idx2centrotype(sim, partitions)
    parameters["random_state"] = None
    parameters["init"] = "custom"
    parameters["n_components"] = centroids.shape[0]
    w_mat = np.ascontiguousarray(g_components[:, centroids])
    h_mat = np.ascontiguousarray(w_components[centroids, :])
    if args["initialisation_matrices"]:
        print(f"{col['light_pink']}Saving Initialisation{col['reset']}")
        save_initialisation(w_mat, h_mat, args["outdir"])
    print(f"{col['light_pink']}Initiating final NMF{col['reset']}")
    nmf_decomp = which_nmf(args["gpu"])
    final_nmf = nmf_decomp(parameters, fdt_matrix, W_mat=w_mat, H_mat=h_mat)
    print(f"{col['light_pink']}Calculating Variance Explained{col['reset']}")
    variance = cumulative_variance(
        fdt_matrix, final_nmf["grey_components"], final_nmf["white_components"]
    )
    nmf_sso_output_wrapper(args["outdir"], sim, dis, partitions, centroids, variance)
    return final_nmf
