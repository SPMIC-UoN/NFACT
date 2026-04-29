from NFACT.decomp.decomposition.matrix_handling import avg_fdt
from NFACT.decomp.decomposition.matrix_decomposition import (
    melodic_incremental_group_pca,
    ica_decomp,
    get_parameters,
    sign_flip,
)
from NFACT.decomp.decomposition.nmf_runs import nmf_decomp
from NFACT.decomp.pipes.image_handling import create_wta_map
from NFACT.base.matrix_handling import normalise_components, load_fdt_matrix
from NFACT.dual_reg.dual_regression.dual_regression_methods import (
    nmf_dual_regression,
    ica_dual_regression,
)
import pytest
import os
from pathlib import Path
import numpy as np


@pytest.fixture
def list_of_mat_files():
    current_working_dir = Path(__file__).parent
    return [
        f"{current_working_dir}/test_data/sub-1",
        f"{current_working_dir}/test_data/sub-2",
        f"{current_working_dir}/test_data/sub-3",
    ]


@pytest.fixture
def fdt_files(list_of_mat_files):
    return [os.path.join(sub, "fdt_matrix2.dot") for sub in list_of_mat_files]


@pytest.fixture
def individual_matrix(fdt_files):
    return load_fdt_matrix(fdt_files[0])


def test_loading_works(individual_matrix):
    assert isinstance(individual_matrix, np.ndarray)


@pytest.fixture
def test_matrix(fdt_files):
    return avg_fdt(fdt_files)


def test_load_worked(test_matrix):
    assert isinstance(test_matrix, np.ndarray)


@pytest.fixture
def test_pca(test_matrix):
    return melodic_incremental_group_pca(test_matrix, 10, 10)


def test_pca_worked(test_pca):
    assert isinstance(test_pca, np.ndarray)
    assert test_pca.shape[1] == 10


@pytest.fixture
def test_ICA_hyperparameters():
    return get_parameters(None, "ica", 10)


@pytest.fixture
def test_NMF_hyperparameters():
    return get_parameters(None, "nmf", 10)


def test_hyperparameters_ICA_worked(test_ICA_hyperparameters):
    assert isinstance(test_ICA_hyperparameters, dict)


def test_hyperparameters_NMF_worked(test_NMF_hyperparameters):
    assert isinstance(test_NMF_hyperparameters, dict)


@pytest.fixture
def test_ica(test_pca, test_ICA_hyperparameters, test_matrix):
    return ica_decomp(test_ICA_hyperparameters, test_pca, test_matrix)


def test_ica_worked(test_ica):
    assert isinstance(test_ica, dict)
    assert isinstance(test_ica["white_components"], np.ndarray)


@pytest.fixture
def test_nmf(test_NMF_hyperparameters, test_matrix):
    return nmf_decomp(test_NMF_hyperparameters, test_matrix)


def test_nmf_worked(test_nmf):
    assert isinstance(test_nmf, dict)
    assert isinstance(test_nmf["white_components"], np.ndarray)


def test_normalise_comp(test_ica):
    norm_comp = normalise_components(
        test_ica["grey_components"], test_ica["white_components"]
    )
    assert isinstance(norm_comp, dict)
    assert isinstance(norm_comp["white_matter"], np.ndarray)


def test_signflip(test_ica):
    assert isinstance(sign_flip(test_ica["white_components"]), np.ndarray)


def test_wta(test_ica):
    assert isinstance(create_wta_map(test_ica["white_components"], 0, 0.0), np.ndarray)


def test_nnls_non_parrallel(test_nmf, individual_matrix):
    sub_specific = nmf_dual_regression(test_nmf, individual_matrix, n_jobs=1)
    assert isinstance(sub_specific["white_components"], np.ndarray)


def test_nnls_parrallel(test_nmf, individual_matrix):
    sub_specific = nmf_dual_regression(test_nmf, individual_matrix, n_jobs=4)
    assert isinstance(sub_specific["white_components"], np.ndarray)


def test_ica_dr(test_ica, individual_matrix):
    sub_specific = ica_dual_regression(test_ica, individual_matrix)
    assert isinstance(sub_specific["white_components"], np.ndarray)
