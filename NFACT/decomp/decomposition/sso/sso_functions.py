import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from NFACT.base.utils import error_and_exit
from NFACT.base.imagehandling import save_white_matter, save_grey_matter_components
from NFACT.base.filesystem import make_directory
import warnings


# Functions to silence Tensorflow
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["XLA_FLAGS"] = "--xla_gpu_cuda_data_dir="

try:
    import tensorflow as tf

    # Force CPU-only execution
    tf.get_logger().setLevel("ERROR")
    tf.config.set_visible_devices([], "GPU")
except Exception:
    pass
from umap.parametric_umap import ParametricUMAP

warnings.simplefilter("ignore", UserWarning)


def projection(dis) -> np.ndarray:
    """
    Function to project disimilairty
    matrix to 2d projects for plotting

    Parameters
    ----------
    dis: np.ndarray
        disimilairty matrix

    Returns
    -------
    np.ndarray: array
        array of projections
    """
    embedder = ParametricUMAP(metric="precomputed")
    return embedder.fit(dis, precomputed_distances=dis).embedding_


def rownorm(nmf_mat: np.ndarray):
    """
    Normalise rows for clustering

    Parameters
    ----------
    nmf_mat: np.ndarray
        nmf matrix to normalise
        on

    Returns
    -------
    nmf_mat: np.ndarray
        nmf matrix normalised
    """
    norms = np.linalg.norm(nmf_mat, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return nmf_mat / norms


def compute_similairty_matrix(components: np.ndarray) -> np.ndarray:
    """
    Function to compute similarity across NMF components
    from multiple runs.

    Parameters
    ----------
    components: np.ndarray
        out from NMF sso

    Returns
    -------
    sim: np.ndarray
        similarity matrix
    """

    normalised_mat = rownorm(components)
    sim = np.corrcoef(normalised_mat)
    np.clip(sim, 0, 1, out=sim)
    return sim


def sim2dis(sim: np.ndarray) -> np.ndarray:
    """
    Function to calculate the dissimlairty matrix

    Parameters
    ----------
    sim: np.ndarray
        similarity matrix

    Returns
    -------
    np.ndarry: array
        disimilarity matrix
    """
    return 1 - sim


def create_stats_dict(n_clusters: int) -> dict:
    """
    Function to create stats dictionary

    Parameters
    ----------
    n_clusters: int
        number of clusters

    Returns
    --------
    dict: dictionary object
        dictionary of cluster stats
        array
    """
    return {
        "N": np.zeros(n_clusters, dtype=int),
        "internal": {
            "sum": np.full(n_clusters, np.nan),
            "min": np.full(n_clusters, np.nan),
            "avg": np.full(n_clusters, np.nan),
            "max": np.full(n_clusters, np.nan),
        },
        "external": {
            "sum": np.full(n_clusters, np.nan),
            "min": np.full(n_clusters, np.nan),
            "avg": np.full(n_clusters, np.nan),
            "max": np.full(n_clusters, np.nan),
        },
    }


def calculate_internal_stats(
    sim_internal: np.ndarray, cluster: int, stat: dict
) -> dict:
    """
    Function to calculate the internal statistics
    of a given cluster

    Parameters
    ----------
    sim_internal: np.ndarray
        array of similarity measures within
        a cluster
    cluster: int
        cluster working on
    stat: dict
        stats dictionary

    Returns
    -------
    stats: dictionary
        stats dictionary
        with sum, min, max & avg
        within cluster stats
    """
    sim_off_diag = np.copy(sim_internal)
    np.fill_diagonal(sim_off_diag, np.nan)
    sim_values = sim_off_diag.flatten()
    sim_values_clean = sim_values[~np.isnan(sim_values)]

    # Calculate and store internal statistics
    if sim_values_clean.size > 0:
        stat["internal"]["sum"][cluster] = np.sum(sim_values_clean)
        stat["internal"]["min"][cluster] = np.min(sim_values_clean)
        stat["internal"]["avg"][cluster] = np.mean(sim_values_clean)
        stat["internal"]["max"][cluster] = np.max(sim_values_clean)
    return stat


def calculate_external_cluster_stats(
    stat: dict, cluster: int, sim_external: np.ndarray
) -> dict:
    """
    Function to calculate external cluster
    stats

    Parameters
    ----------
    stat: dict
        dictionary to store stats in
    cluster: int
        cluster number
    sim_external: np.ndarray
        external similairty matrix

    Returns
    -------
    stats: dictionary
        stats dictionary
        with sum, min, max & avg
        external cluster stats
    """
    stat["external"]["sum"][cluster] = np.sum(sim_external)
    stat["external"]["min"][cluster] = np.min(sim_external)
    stat["external"]["avg"][cluster] = np.mean(sim_external)
    stat["external"]["max"][cluster] = np.max(sim_external)
    return stat


def calculate_cluster_stats(sim: np.ndarray, partition: np.ndarray) -> dict:
    """
    Function to calculate cluster stats:

    Internal (stats on all unique pairs of distinct
              nodes in a cluster)
        - sum: sum of the total edge weight in cluster
        - min: minimium edge weight
        - avg: avergae edge weight
        - max: maximum edge weight
    External (current cluster nodes and all nodes in all other clusters
              combined)
        - sum: total edge weight of cluster to rest of graph
        - min: min edge weight of cluster to rest of graph
        - avg: avg edge weight of cluster to rest of graph
        - max: max edge weight of cluster to rest of graph


    Parameters
    ----------
    sim: np.ndarray
        similairty matrix
    partition: np.ndarray
        array of cluster labels for all partitions


    Returns
    -------
        A dictionary containing the calculated statistics. NumPy arrays are used for
        all internal data structures.
    """
    n_clusters = int(np.max(partition))
    check_clustering(n_clusters, partition, sim)
    stat = create_stats_dict(n_clusters)

    # Iterate over clusters (using 1-based indexing for matching the partition labels)
    for cluster in range(1, n_clusters + 1):
        working_cluster = cluster - 1

        # Boolean mask for current cluster members: (partition == cluster)
        this_partition_mask = partition == cluster

        # Internal Statistics (S(thisPartition,thisPartition)) ---
        sim_internal = sim[this_partition_mask][:, this_partition_mask]
        stat["N"][working_cluster] = sim_internal.shape[0]

        # Only calculate internal stats if cluster size is > 1 (required for off-diagonal values)
        if stat["N"][working_cluster] > 1:
            stat = calculate_internal_stats(sim_internal, working_cluster, stat)

        # External Statistics (S(thisPartition, ~thisPartition)) ---
        not_this_partition_mask = ~this_partition_mask
        sim_external = sim[this_partition_mask][:, not_this_partition_mask].flatten()

        # Calculate and store external statistics only if the resulting array is not empty
        if sim_external.size > 0:
            stat = calculate_external_cluster_stats(stat, working_cluster, sim_external)

    return stat


def clustering_linkage(dis: np.ndarray) -> np.ndarray:
    """
    Function to cluster linkage

    Parameters
    ----------
    dis: np.ndarray
       dis-similairty matrix

    Returns
    --------
    np.ndarray: array
       a merge distance array
       from clustering
    """
    dis_flatened = squareform(dis, checks=False)
    return linkage(dis_flatened, method="average")


def calculate_elbow(merge_dist: np.ndarray) -> float:
    """
    Function to get point

    Parameters
    ----------
    merge_dist: np.ndarray
        merging distance array
        for clusters

    Returns
    --------
    float: float value
        elbow point
    """
    x_coords = merge_dist
    y_coords = np.arange(merge_dist.shape[0])

    # Convert to 3D (z=0)
    start_point = np.array([x_coords[0], y_coords[0], 0.0])
    end_point = np.array([x_coords[-1], y_coords[-1], 0.0])

    distances = []
    for x_coords_point, y_coords_point in zip(x_coords, y_coords):
        moving_point = np.array([x_coords_point, y_coords_point, 0.0])

        # Distance to the line in 3D; z components are all zero
        dist = np.linalg.norm(
            np.cross(end_point - start_point, moving_point - start_point)
        ) / np.linalg.norm(end_point - start_point)
        distances.append(dist)

    distances = np.array(distances)
    knee_index = np.argmax(distances)
    return x_coords[knee_index]


def cluster_valid(cluster_partition: np.ndarray, dim: int) -> bool:
    """
    Function to ascertain if a cluster
    partition is all a single cluster
    or has any singletons

    Parameters
    ----------
    cluster_partition: np.ndarray
        clustuster partition

    Returns
    -------
    bool: boolean
        bool of True no singletons
        or False if it is
    """
    clusters, counts = np.unique(cluster_partition, return_counts=True)
    if np.any(counts == 1) or len(clusters) == 1:
        return False
    if clusters.max() > dim:
        return False
    return True


def dendogram_cut(link_mat: np.ndarray, elbow_height: float, dim: int) -> np.ndarray:
    """
    Function to cut the dendogram at set point.

    Parameters
    ----------
    link_mat: np.ndarray
        linkage matrix
    elbow_height: float
        elbow point to use
        as starting point

    Returns
    -------
    np.ndarray: array
        array of labels
    """
    intial_run = fcluster(link_mat, t=elbow_height, criterion="distance")
    if cluster_valid(intial_run, dim):
        return intial_run

    merge_heights = np.sort(np.unique(link_mat))
    start_idx = np.searchsorted(merge_heights, elbow_height)

    for height in merge_heights[start_idx:]:
        part = fcluster(link_mat, t=height, criterion="distance")

        if cluster_valid(part, dim):
            return part


def clustering_components(dis: np.ndarray, dim: int) -> np.ndarray:
    """
    Function to cluster components

    Parameters
    ----------
    dis: np.ndarray
       dis-similairty matrix

    Returns
    --------
    np.ndarray: array
       a partition array
    """
    zlink = clustering_linkage(dis)
    merge_distance = zlink[:, 2]
    elbow = calculate_elbow(merge_distance)

    return dendogram_cut(zlink, elbow, dim)


def check_clustering(n_clusters: int, partition: np.ndarray, sim: np.ndarray) -> None:
    """
    Function wrapper to check that clustering
    and similairty calculations worked

    Parameters
    -----------
    n_clusters: int
        how many clusters
    partition: np.ndarray
        paritition array
    sim: np.ndarray
        similairty matrix

    Returns
    -------
    None
    """
    error_and_exit(partition.size != 0, "Clustering Failed. Please check Num of dims")
    error_and_exit(
        sim.size != 0, "Failed to Calculate similairty matrix. Please check Num of dims"
    )
    error_and_exit(n_clusters > 0, "Clustering Failed. Please check Num of dims")


def centrotype(sim: np.ndarray) -> np.ndarray:
    """
    Find the centrotype (most central element)
    of a similarity matrix.

    Parameters
    ----------
    sim : ndarray
        Similarity matrix.

    Returns
    -------
    idx : int
        Index of the centrotype within
        similairty matrix
    """
    col_sums = np.sum(sim, axis=0)
    idx = np.argmax(col_sums)
    return idx


def idx2centrotype(sim: np.ndarray, partition: np.ndarray) -> np.ndarray:
    """
    Function to compute centrotype(s)
    given a similarity matrix and partitions.

    Parameters
    ----------
    sim : ndarray
        Similarity matrix.
    partition : ndarray
        partition array

    Returns
    -------
    index2centrotype : ndarray
        Index/indices of the centriods of the cluster
    """

    n_cluster = partition.max()
    index2centrotype = np.zeros(n_cluster, dtype=int)

    for cluster in range(1, n_cluster + 1):
        indices = np.where(partition == cluster)[0]
        sim_cluster_sub = sim[np.ix_(indices, indices)]
        centroid_idx = centrotype(sim_cluster_sub)
        index2centrotype[cluster - 1] = indices[centroid_idx]

    return index2centrotype


def compute_cluster_score(stat: dict) -> dict:
    """
    Compute cluster quality score for a partition.

    Parameters
    ----------
    stat: dict
        stat dictionary

    Returns
    -------
    dict: dictionary object
        dictonary of cluster scores
    """

    mean_in_score = stat["internal"]["avg"]
    mean_out_score = stat["external"]["avg"]
    minmax_in_score = stat["internal"]["min"]
    minmax_out_score = stat["external"]["max"]

    return {
        "mean_score": mean_in_score - mean_out_score,
        "mean_in_score": mean_in_score,
        "mean_out_score": mean_out_score,
        "minmax_score": minmax_in_score - minmax_out_score,
        "minmax_in_score": minmax_in_score,
        "minmax_out_score": minmax_out_score,
    }


def cluster_scores(sim: np.ndarray, partitions: np.ndarray) -> dict:
    """
    Function to calculate cluster scores and order
    clusters by stability

    Parameters
    ----------
    sim: np.ndarray
        similairty matrix
    partitions: np.ndarray
        array of cluster labels

    Returns
    -------
    dict: dictionary object
        dict of cluster statistics
    """
    cluster_stat = calculate_cluster_stats(sim, partitions)
    cluster_scores = compute_cluster_score(cluster_stat)
    clusternumber = np.arange(1, len(cluster_scores["mean_score"]) + 1)
    order = np.argsort(-cluster_scores["mean_score"])

    return {
        "clusternumber": clusternumber[order],
        "number_in_cluster": cluster_stat["N"][order],
        "internal_score": cluster_scores["mean_score"][order],
        "between_score": cluster_scores["minmax_score"][order],
        "internal_avg": cluster_scores["mean_in_score"],
    }


def cumulative_variance(
    fdt_mat: np.ndarray, grey: np.ndarray, white: np.ndarray
) -> dict:
    """
    Function to calculate total variance
    explained by adding on additional component
    and

    Parameters
    ------------
    fdt_mat: np.ndarray
        orginal fdt matrix
    grey: np.ndarray
        grey matter NMF
    white: np.ndarray
        White matter NMF

    Returns
    -------
    dict: dictionary object
        dict of cummilative_r2 and
        per_comp (how much extra variation
        is explained by adding that component)
    """
    n_components = white.shape[0]
    ss_total = np.sum((fdt_mat - fdt_mat.mean()) ** 2)
    X_recon_cum = np.zeros_like(fdt_mat)
    r2_cumulative = []

    for comp in range(n_components):
        X_recon_cum += np.outer(grey[:, comp], white[comp, :])
        ss_resid = np.sum((fdt_mat - X_recon_cum) ** 2)
        r2_cumulative.append(1 - ss_resid / ss_total)

    return {
        "cumulative_r2": np.array(r2_cumulative),
        "per_comp": np.diff(np.concatenate([[0], np.array(r2_cumulative)])),
    }


def save_individual_components(
    clusters: np.ndarray,
    w_components: np.ndarray,
    g_components: np.ndarray,
    decomp_dir: str,
    output_dir: str,
    seed: list,
    roi: list,
    coord_path: str,
    cifti_save: bool,
) -> None:
    """
    Function to save individual clusters as
    volumes.

    Parameters
    ----------
    clusters: np.ndarray
        list of cluster numbers
    w_components: np.ndarray
        array of white matter components
    g_components: np.ndarray
        array of grey matter components
    decomp_dir: str
        decomposition directory
    output_dir: str
        output directory
    seed: list
        list of seeds
    roi: list
        list of region of interest
    coord_path: str
        coords_for_fdt_matrix2 file
    cifti_save: bool
        should the grey matter seeds be
        saved as ciftis
    """
    make_directory(output_dir, ignore_errors=True)
    labels = np.unique(clusters)
    for label in labels:
        idx = np.where(clusters == label)[0]
        w_cluster = w_components[idx, :]
        g_cluster = g_components[idx, :]
        save_white_matter(
            w_cluster,
            f"{decomp_dir}/lookup_tractspace_fdt_matrix2.nii.gz",
            f"{decomp_dir}/tract_space_coords_for_fdt_matrix2",
            f"{output_dir}/clusters/cluster_{label}_sso",
        )
        save_grey_matter_components(
            grey_matter_components=g_cluster,
            nfact_path="/",
            directory=output_dir,
            dim="sso",
            cifti_save=cifti_save,
            coord_path=coord_path,
            roi=roi,
            seeds=seed,
        )
