"""
Unit tests for NFACT decomposition, SSO clustering, setup, and pipeline pipes.
"""

import json
from pathlib import Path
import matplotlib
import numpy as np
import pytest
from NFACT.decomp.decomposition.sso.nmfsso import (
    NMFsso,
    nmf_cluster_stats_csv,
)
from NFACT.decomp.decomposition.sso.sso_functions import (
    CCA,
    calculate_cluster_stats,
    calculate_elbow,
    centrotype,
    check_clustering,
    cluster_scores,
    cluster_valid,
    clustering_components,
    clustering_linkage,
    compute_cluster_score,
    compute_similairty_matrix,
    create_stats_dict,
    cumulative_variance,
    dendogram_cut,
    idx2centrotype,
    load_initialisation,
    projection,
    rownorm,
    save_initialisation,
    sim2dis,
)
from NFACT.decomp.decomposition.sso.sso_plotting import (
    NMFgraph,
    plot_cluster_stats,
    plot_matrix,
)
from NFACT.decomp.pipes.image_handling import (
    save_components_to_disk,
)
from NFACT.decomp.setup.arg_check import (
    check_pca,
    process_components,
    process_wta_zhr,
)
from NFACT.decomp.setup.configure_setup import (
    check_config_file,
    load_config_file,
)
from NFACT.decomp.setup.file_setup import (
    create_folder_set_up,
    get_group_average_files,
)

matplotlib.use("Agg")


def test_rownorm_sim_and_dis() -> None:
    """
    Function to test rownorm, similarity matrix calculation, and sim2dis conversion.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    matrix_with_zeros = np.array([[3.0, 4.0], [0.0, 0.0], [1.0, 1.0]], dtype=np.float32)
    normalized_matrix = rownorm(matrix_with_zeros)
    assert np.allclose(np.linalg.norm(normalized_matrix[0]), 1.0)
    assert np.allclose(normalized_matrix[1], [0.0, 0.0])
    assert not np.isnan(normalized_matrix).any()

    components = np.array(
        [[1.0, 2.0, 3.0], [1.0, 2.1, 3.0], [10.0, 0.1, 0.2]], dtype=np.float32
    )
    similarity_matrix = compute_similairty_matrix(components)
    assert similarity_matrix.shape == (3, 3)
    assert np.all(similarity_matrix >= 0.0)
    assert np.all(similarity_matrix <= 1.0)
    assert np.allclose(np.diag(similarity_matrix), 1.0)

    dissimilarity_matrix = sim2dis(similarity_matrix)
    assert np.allclose(dissimilarity_matrix, 1.0 - similarity_matrix)
    assert np.allclose(np.diag(dissimilarity_matrix), 0.0)


def test_clustering_linkage_elbow_and_dendogram_cut() -> None:
    """
    Function to test linkage, elbow detection, and dendrogram clustering cut.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    similarity_block = np.zeros((9, 9), dtype=np.float32)
    similarity_block[0:3, 0:3] = 0.95
    similarity_block[3:6, 3:6] = 0.95
    similarity_block[6:9, 6:9] = 0.95
    np.fill_diagonal(similarity_block, 1.0)
    dissimilarity_block = sim2dis(similarity_block)

    link_matrix = clustering_linkage(dissimilarity_block)
    assert link_matrix.shape[0] == 8

    elbow_point = calculate_elbow(link_matrix[:, 2])
    assert elbow_point >= 0.0

    valid_partition = np.array([1, 1, 1, 2, 2, 2, 3, 3, 3])
    assert cluster_valid(valid_partition, dim=3) is True

    singleton_partition = np.array([1, 1, 1, 2, 3, 4, 5, 6, 7])
    assert cluster_valid(singleton_partition, dim=3) is False

    single_cluster_partition = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert cluster_valid(single_cluster_partition, dim=3) is False

    clusters_found = dendogram_cut(link_matrix, elbow_point, dim=3)
    assert clusters_found is not None
    assert len(np.unique(clusters_found)) == 3

    direct_clusters = clustering_components(dissimilarity_block, dim=3)
    assert direct_clusters is not None


def test_centrotype_and_idx2centrotype() -> None:
    """
    Function to test centrotype and cluster centroid index extraction.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    similarity_subset = np.array(
        [[1.0, 0.8, 0.4], [0.8, 1.0, 0.7], [0.4, 0.7, 1.0]], dtype=np.float32
    )
    centroid_index = centrotype(similarity_subset)
    assert centroid_index == 1

    two_cluster_sim = np.zeros((6, 6), dtype=np.float32)
    two_cluster_sim[0:3, 0:3] = similarity_subset
    two_cluster_sim[3:6, 3:6] = similarity_subset
    partitions = np.array([1, 1, 1, 2, 2, 2])

    centroids = idx2centrotype(two_cluster_sim, partitions)
    assert len(centroids) == 2
    assert centroids[0] == 1
    assert centroids[1] == 4


def test_cluster_stats_and_scores() -> None:
    """
    Function to test cluster score ranking and stats dictionaries.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    empty_stats_dict = create_stats_dict(2)
    assert "internal" in empty_stats_dict
    assert "external" in empty_stats_dict

    similarity_matrix = np.array(
        [
            [1.0, 0.9, 0.1, 0.1],
            [0.9, 1.0, 0.1, 0.1],
            [0.1, 0.1, 1.0, 0.95],
            [0.1, 0.1, 0.95, 1.0],
        ],
        dtype=np.float32,
    )
    partitions = np.array([1, 1, 2, 2])
    cluster_stats = calculate_cluster_stats(similarity_matrix, partitions)
    assert cluster_stats["N"][0] == 2
    assert cluster_stats["N"][1] == 2

    computed_scores = compute_cluster_score(cluster_stats)
    assert "mean_score" in computed_scores
    assert "minmax_score" in computed_scores

    ranked_scores = cluster_scores(similarity_matrix, partitions)
    assert "clusternumber" in ranked_scores
    assert "internal_score" in ranked_scores
    assert len(ranked_scores["clusternumber"]) == 2

    assert check_clustering(2, partitions, similarity_matrix) is None
    with pytest.raises(SystemExit) as exit_error_empty:
        check_clustering(0, np.array([]), np.empty((0, 0), dtype=np.float32))
    assert exit_error_empty.value.code == 1


def test_cumulative_variance_algebraic_identity() -> None:
    """
    Function to test fast BLAS cumulative variance against naive Frobenius norm.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    np.random.seed(42)
    number_voxels_seed = 30
    number_voxels_tract = 40
    number_components = 4

    grey_components = np.random.uniform(
        0.1, 1.0, size=(number_voxels_seed, number_components)
    ).astype(np.float32)
    white_components = np.random.uniform(
        0.1, 1.0, size=(number_components, number_voxels_tract)
    ).astype(np.float32)
    synthetic_fdt = grey_components @ white_components + np.random.normal(
        0, 0.05, size=(number_voxels_seed, number_voxels_tract)
    ).astype(np.float32)

    variance_result = cumulative_variance(
        synthetic_fdt, grey_components, white_components
    )
    blas_cumulative = variance_result["cumulative_r2"]
    per_comp = variance_result["per_comp"]

    total_ss = float(np.sum((synthetic_fdt - synthetic_fdt.mean()) ** 2))
    expected_cumulative = np.zeros(number_components)
    for comp_index in range(number_components):
        reconstructed = (
            grey_components[:, : comp_index + 1] @ white_components[: comp_index + 1, :]
        )
        residual_ss = float(np.sum((synthetic_fdt - reconstructed) ** 2))
        expected_cumulative[comp_index] = 1.0 - residual_ss / total_ss

    assert np.allclose(blas_cumulative, expected_cumulative, atol=1e-4)
    assert np.allclose(per_comp[0], blas_cumulative[0], atol=1e-4)
    assert np.allclose(per_comp[1], blas_cumulative[1] - blas_cumulative[0], atol=1e-4)


def test_cca_projection_and_projection_wrapper() -> None:
    """
    Function to test Curvilinear Component Analysis 2D projection.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    dissimilarity_sample = np.random.uniform(0.1, 0.9, size=(10, 10))
    np.fill_diagonal(dissimilarity_sample, 0.0)
    dissimilarity_sample = (dissimilarity_sample + dissimilarity_sample.T) / 2.0

    cca_instance = CCA(dissimilarity_sample, epochs=5)
    embedded_points = cca_instance.run()
    assert embedded_points.shape == (10, 2)
    assert not np.isnan(embedded_points).any()

    wrapped_projection = projection(dissimilarity_sample)
    assert wrapped_projection.shape == (10, 2)


def test_save_and_load_initialisation(tmp_path: Path) -> None:
    """
    Function to test save_initialisation and load_initialisation round-trip.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    grey_matrix = np.ones((10, 3), dtype=np.float32)
    white_matrix = np.ones((3, 20), dtype=np.float32)

    sso_output_dir = tmp_path / "nfact_decomp" / "sso_output"
    sso_output_dir.mkdir(parents=True)

    save_initialisation(grey_matrix, white_matrix, str(tmp_path))

    saved_gm = sso_output_dir / "gm_mat.npy"
    saved_wm = sso_output_dir / "wm_mat.npy"
    assert saved_gm.exists()
    assert saved_wm.exists()

    loaded_initialization = load_initialisation(str(saved_gm), str(saved_wm))
    assert loaded_initialization is not None
    assert np.array_equal(loaded_initialization["gm_mat"], grey_matrix)
    assert np.array_equal(loaded_initialization["wm_mat"], white_matrix)

    missing_initialization = load_initialisation("/invalid/gm.npy", "/invalid/wm.npy")
    assert missing_initialization is None


def test_nmfsso_single_and_parallel() -> None:
    """
    Function to test NMFsso execution in both single-core and parallel modes.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    np.random.seed(123)
    fdt_toy_matrix = np.random.uniform(0.1, 1.0, size=(15, 20)).astype(np.float32)
    nmf_parameters = {
        "n_components": 2,
        "max_iter": 20,
        "init": "random",
        "random_state": 42,
    }

    sso_single = NMFsso(
        fdt_mat=fdt_toy_matrix,
        num_int=2,
        nmf_params=nmf_parameters,
        n_jobs=1,
        gpu=False,
    )
    results_single = sso_single.run()
    assert len(results_single["grey"]) == 2
    assert len(results_single["white"]) == 2
    assert results_single["grey"][0].shape == (15, 2)
    assert results_single["white"][0].shape == (2, 20)

    sso_parallel = NMFsso(
        fdt_mat=fdt_toy_matrix,
        num_int=2,
        nmf_params=nmf_parameters,
        n_jobs=2,
        gpu=False,
    )
    results_parallel = sso_parallel.run()
    assert len(results_parallel["grey"]) == 2
    assert len(results_parallel["white"]) == 2


def test_sso_plotting_and_cluster_stats_csv(tmp_path: Path) -> None:
    """
    Function to test plot_matrix, plot_cluster_stats, and NMFgraph rendering.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    similarity_data = np.array(
        [
            [1.0, 0.8, 0.2, 0.1],
            [0.8, 1.0, 0.1, 0.2],
            [0.2, 0.1, 1.0, 0.85],
            [0.1, 0.2, 0.85, 1.0],
        ]
    )
    dissimilarity_data = 1.0 - similarity_data
    matrix_plot_file = tmp_path / "sim_plot.tiff"
    dis_plot_file = tmp_path / "dis_plot.tiff"
    plot_matrix(str(matrix_plot_file), similarity_data, "Similarity Matrix")
    plot_matrix(str(dis_plot_file), dissimilarity_data, "Dissimilarity Matrix")
    assert matrix_plot_file.exists()
    assert dis_plot_file.exists()

    stats_dictionary = {
        "clusternumber": np.array([1, 2]),
        "number_in_cluster": np.array([2, 2]),
        "internal_score": np.array([0.7, 0.6]),
        "between_score": np.array([0.5, 0.4]),
        "cumulative_r2": np.array([0.45, 0.85]),
        "per_comp": np.array([0.45, 0.40]),
    }
    stats_csv_file = tmp_path / "cluster_stats.csv"
    nmf_cluster_stats_csv(stats_dictionary, str(tmp_path))
    assert stats_csv_file.exists()

    stats_plot_file = tmp_path / "stats_plot.tiff"
    plot_cluster_stats(stats_dictionary, str(stats_plot_file))
    assert stats_plot_file.exists()

    graph_plot_file = tmp_path / "network_plot.tiff"
    cluster_points = np.array([[0.0, 0.0], [0.1, 0.1], [5.0, 5.0], [5.1, 5.2]])
    cluster_labels = np.array([1, 1, 2, 2])
    internal_average = np.array([0.8, 0.85])
    centroid_indices = np.array([0, 2])

    graph_instance = NMFgraph(
        proj=cluster_points,
        labels=cluster_labels,
        internal_average=internal_average,
        centroid_indices=centroid_indices,
        output_dir=str(graph_plot_file),
    )
    graph_instance.plot()
    assert graph_plot_file.exists()


def test_decomp_setup_arg_check() -> None:
    """
    Function to test process_wta_zhr, process_components, and check_pca helpers.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert process_wta_zhr("2.5") == 2.5
    assert process_wta_zhr(3.0) == 3.0
    with pytest.raises(SystemExit) as exit_wta:
        process_wta_zhr("invalid_number")
    assert exit_wta.value.code == 1

    assert process_components("10.0", "ica") == 10.0
    assert process_components("10", "ica") == 10
    with pytest.raises(SystemExit) as exit_components:
        process_components("invalid", "ica")
    assert exit_components.value.code == 1

    assert check_pca("PCA") == "pca"
    assert check_pca("MIGP") == "migp"
    with pytest.raises(SystemExit) as exit_pca:
        check_pca("fast_svd")
    assert exit_pca.value.code == 1


def test_configure_setup_config_file(tmp_path: Path) -> None:
    """
    Function to test load_config_file and check_config_file validation.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    valid_decomp_config = {
        "ica": {"max_iter": 200, "tol": 0.001},
        "nmf": {"max_iter": 300, "tol": 0.0001},
    }
    config_path = tmp_path / "decomp.config"
    config_path.write_text(json.dumps(valid_decomp_config))

    loaded_ica = load_config_file(str(config_path), "ica")
    assert loaded_ica["max_iter"] == 200

    assert check_config_file(loaded_ica, "ica") is None

    invalid_config = {"invalid_param_foo": 123}
    with pytest.raises(SystemExit) as exit_invalid_config:
        check_config_file(invalid_config, "ica")
    assert exit_invalid_config.value.code == 1


def test_decomp_file_setup_and_save_components(tmp_path: Path) -> None:
    """
    Function to test create_folder_set_up, get_group_average_files, and save_components_to_disk.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    study_directory = tmp_path / "decomp_study"
    study_directory.mkdir()
    create_folder_set_up(str(study_directory))
    assert (study_directory / "nfact_decomp" / "group_averages").exists()
    assert (study_directory / "nfact_decomp" / "sso_output").exists()
    assert (study_directory / "nfact_decomp" / "components" / "NMF" / "decomp").exists()

    with pytest.raises(SystemExit) as exit_missing_dir:
        create_folder_set_up(str(tmp_path / "non_existent_folder"))
    assert exit_missing_dir.value.code == 1

    subject_omatrix_dir = tmp_path / "sub-01_omatrix2"
    subject_omatrix_dir.mkdir()
    (subject_omatrix_dir / "lookup_tractspace_fdt_matrix2.nii.gz").write_text("lookup")
    (subject_omatrix_dir / "coords_for_fdt_matrix2").write_text("coords")
    (subject_omatrix_dir / "tract_space_coords_for_fdt_matrix2").write_text(
        "tract_coords"
    )

    group_avg_dir = study_directory / "nfact_decomp" / "group_averages"
    get_group_average_files(str(subject_omatrix_dir), str(group_avg_dir))
    assert (group_avg_dir / "lookup_tractspace_fdt_matrix2.nii.gz").exists()
    assert (group_avg_dir / "coords_for_fdt_matrix2").exists()

    component_payload = {
        "grey_components": np.ones((10, 2), dtype=np.float32),
        "white_components": np.ones((2, 20), dtype=np.float32),
    }
    decomp_base_folder = study_directory / "nfact_decomp"
    save_components_to_disk(component_payload, str(decomp_base_folder), "NMF", "2")
    saved_decomp_gm = (
        decomp_base_folder / "components" / "NMF" / "decomp" / "G_NMF_dim2.npy"
    )
    assert saved_decomp_gm.exists()
