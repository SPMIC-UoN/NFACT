import argparse
from pathlib import Path
import re
import pytest
from NFACT.base.base_args import (
    algo_arg,
    base_arguments,
    cluster_args,
    nfact_decomp_folder,
    parallel_args,
    seed_roi_args,
    set_up_args,
)
from NFACT.base.config import (
    convert_str_to_bool,
    get_nfact_arguments,
    process_dictionary_arguments,
)
from NFACT.base.filesystem import (
    delete_folder,
    get_current_date,
    load_json,
    make_directory,
    read_file_to_list,
    write_to_file,
)
from NFACT.base.setup import (
    check_algo,
    check_arguments,
    check_fsl_is_installed,
    check_nfact_decomp_directory,
    check_rois,
    check_seeds_surfaces,
    check_subject_exist,
    creat_subfolder_setup,
    does_list_of_subjects_exist,
    get_paths,
    get_subjects,
    previous_matrix,
    process_dim,
    process_input_imgs,
    return_list_of_subjects_from_file,
    which_folders_dont_exist,
)
from NFACT.base.utils import colours


def test_make_and_delete_directory(tmp_path: Path) -> None:
    """
    Function to test make_directory and delete_folder functions.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    target_directory = tmp_path / "sample_folder"
    make_directory(str(target_directory))
    assert target_directory.exists()

    nested_file = target_directory / "dummy.txt"
    nested_file.write_text("dummy content")

    make_directory(str(target_directory), overwrite=True)
    assert target_directory.exists()
    assert not nested_file.exists()

    delete_folder(str(target_directory))
    assert not target_directory.exists()

    make_directory(str(target_directory), ignore_errors=True)
    assert target_directory.exists()


def test_write_and_read_file_to_list(tmp_path: Path) -> None:
    """
    Function to test write_to_file and read_file_to_list.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    sample_lines = ["subject_01\n", "subject_02\n", "subject_03\n"]
    success_status = write_to_file(
        str(tmp_path), "subjects.txt", sample_lines, text_is_list=True
    )
    assert success_status

    read_lines = read_file_to_list(str(tmp_path / "subjects.txt"))
    assert read_lines == ["subject_01", "subject_02", "subject_03"]

    write_single_status = write_to_file(
        str(tmp_path), "single.txt", "single line", text_is_list=False
    )
    assert write_single_status
    assert (tmp_path / "single.txt").read_text() == "single line"

    invalid_status = write_to_file(
        "/invalid/directory/path/never/exists", "fail.txt", "content"
    )
    assert not invalid_status


def test_load_json_valid_and_invalid(tmp_path: Path) -> None:
    """
    Function to test load_json with valid and invalid files.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    json_path = tmp_path / "config.json"
    json_path.write_text('{"algo": "NMF", "dim": 50}')

    loaded_dictionary = load_json(str(json_path))
    assert loaded_dictionary["algo"] == "NMF"
    assert loaded_dictionary["dim"] == 50

    bad_json_path = tmp_path / "bad.json"
    bad_json_path.write_text("{broken json")
    with pytest.raises(SystemExit) as exit_info:
        load_json(str(bad_json_path))
    assert exit_info.value.code == 1


def test_get_current_date() -> None:
    """
    Function to test get_current_date format matching.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    date_string = get_current_date()
    assert re.match(r"^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}$", date_string)


def test_convert_str_to_bool_and_process_dictionary() -> None:
    """
    Function to test convert_str_to_bool and process_dictionary_arguments.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert convert_str_to_bool("true") is True
    assert convert_str_to_bool("True") is True
    assert convert_str_to_bool("false") is False
    assert convert_str_to_bool("False") is False
    assert convert_str_to_bool("other_string") == "other_string"
    assert convert_str_to_bool(123) == 123

    nested_dict = {
        "flag_true": "True",
        "flag_false": "False",
        "nested": {"inner_bool": "true", "number": 10},
    }
    processed = process_dictionary_arguments(nested_dict)
    assert processed["flag_true"] is True
    assert processed["flag_false"] is False
    assert processed["nested"]["inner_bool"] is True
    assert processed["nested"]["number"] == 10


def test_get_nfact_arguments() -> None:
    """
    Function to test get_nfact_arguments extracts arguments for all modules.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    nfact_args_dict = get_nfact_arguments()
    expected_modules = ["cluster", "nfact_pp", "nfact_decomp", "nfact_dr", "nfact_qc"]
    for module_name in expected_modules:
        assert module_name in nfact_args_dict
        assert isinstance(nfact_args_dict[module_name], dict)


def test_subject_list_existence_and_parsing(tmp_path: Path) -> None:
    """
    Function to test subject list validation and reading functions.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    missing_file = tmp_path / "missing.txt"
    assert not does_list_of_subjects_exist(str(missing_file))
    assert not does_list_of_subjects_exist(str(tmp_path))

    valid_file = tmp_path / "subjects.sublist"
    valid_file.write_text("sub-1\n\nsub-2\n")
    assert does_list_of_subjects_exist(str(valid_file))

    parsed_subjects = return_list_of_subjects_from_file(str(valid_file))
    assert parsed_subjects == ["sub-1", "sub-2"]

    no_extension_file = tmp_path / "subject_file"
    no_extension_file.write_text("sub-A\nsub-B\n")
    parsed_no_ext = return_list_of_subjects_from_file(str(no_extension_file))
    assert parsed_no_ext == ["sub-A", "sub-B"]

    invalid_ext_file = tmp_path / "subjects.csv"
    invalid_ext_file.write_text("sub-1\n")
    with pytest.raises(SystemExit) as exit_info:
        return_list_of_subjects_from_file(str(invalid_ext_file))
    assert exit_info.value.code == 1


def test_check_subject_exist(tmp_path: Path) -> None:
    """
    Function to test check_subject_exist validates path existence.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    subject_directory = tmp_path / "sub_01"
    subject_directory.mkdir()
    check_subject_exist([str(subject_directory)])

    with pytest.raises(SystemExit) as exit_info:
        check_subject_exist([str(tmp_path / "sub_missing")])
    assert exit_info.value.code == 1


@pytest.mark.parametrize(
    "algo_input, expected_algo",
    [("NMF", "nmf"), ("nmf", "nmf"), ("ICA", "ica"), ("ica", "ica")],
)
def test_check_algo_valid(algo_input: str, expected_algo: str) -> None:
    """
    Function to test check_algo returns lowercase for valid algorithms.

    Parameters
    ----------
    algo_input: str
        Input algorithm string.
    expected_algo: str
        Expected lowercase algorithm string.

    Returns
    -------
    None
    """
    assert check_algo(algo_input) == expected_algo


def test_check_algo_invalid() -> None:
    """
    Function to test check_algo exits on unknown algorithms.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    with pytest.raises(SystemExit) as exit_info:
        check_algo("PCA")
    assert exit_info.value.code == 1


def test_previous_matrix(tmp_path: Path) -> None:
    """
    Function to test previous_matrix returns expected 5-path list.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    matrix_paths = previous_matrix(str(tmp_path))
    assert len(matrix_paths) == 5
    assert matrix_paths[0] == str(tmp_path)
    assert any("average_matrix2.npy" in path_item for path_item in matrix_paths)


def test_get_subjects(tmp_path: Path) -> None:
    """
    Function to test get_subjects populates subject list in arguments dictionary.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    subject_file = tmp_path / "subjects.txt"
    subject_file.write_text("sub-01\nsub-02\n")
    arguments_dict = {"list_of_subjects": str(subject_file)}
    updated_dict = get_subjects(arguments_dict)
    assert updated_dict["ptxdir"] == ["sub-01", "sub-02"]


def test_subfolder_creation_helpers(tmp_path: Path) -> None:
    """
    Function to test which_folders_dont_exist and creat_subfolder_setup.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    subfolder_list = ["logs", "components", "group_averages"]
    missing_list = which_folders_dont_exist(str(tmp_path), subfolder_list)
    assert missing_list == subfolder_list

    creat_subfolder_setup(str(tmp_path), subfolder_list)
    assert (tmp_path / "logs").exists()
    assert (tmp_path / "components").exists()
    assert (tmp_path / "group_averages").exists()

    creat_subfolder_setup(str(tmp_path), subfolder_list)


def test_check_arguments_validation() -> None:
    """
    Function to test check_arguments exits on missing compulsory keys.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    sample_arguments = {"outdir": "/tmp/out", "dim": False}
    with pytest.raises(SystemExit) as exit_info:
        check_arguments(sample_arguments, ["outdir", "dim"])
    assert exit_info.value.code == 1


def test_process_dim() -> None:
    """
    Function to test process_dim parses integer and float dimensions.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert process_dim("50") == 50
    assert process_dim("75.0") == 75
    assert process_dim(25) == 25
    with pytest.raises(SystemExit) as exit_info:
        process_dim("not_a_number")
    assert exit_info.value.code == 1


def test_check_seeds_surfaces_and_check_rois(tmp_path: Path) -> None:
    """
    Function to test check_seeds_surfaces and check_rois.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    assert check_seeds_surfaces(["/path/L.surf.gii", "/path/R.surf.gii"])
    assert not check_seeds_surfaces(["/path/L.white.nii.gz"])

    roi_file = tmp_path / "roi.txt"
    roi_file.write_text("/path/medial_wall.shape.gii\n")

    arguments_surface = {
        "surface": True,
        "roi": str(roi_file),
    }
    processed_rois = check_rois(arguments_surface)
    assert processed_rois["roi"] == ["/path/medial_wall.shape.gii"]

    arguments_no_roi = {"surface": True, "roi": False}
    with pytest.raises(SystemExit) as exit_info:
        check_rois(arguments_no_roi)
    assert exit_info.value.code == 1


def test_process_input_imgs(tmp_path: Path) -> None:
    """
    Function to test process_input_imgs reads paths and checks extensions.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    seeds_file = tmp_path / "seeds.txt"
    seeds_file.write_text("/study/seed1.nii.gz\n/study/seed2.gii\n")
    processed_list = process_input_imgs(str(seeds_file))
    assert processed_list == ["/study/seed1.nii.gz", "/study/seed2.gii"]


def test_check_fsl_is_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Function to test check_fsl_is_installed validates FSLDIR in environment.

    Parameters
    ----------
    monkeypatch: pytest.MonkeyPatch
        Pytest monkeypatch fixture.

    Returns
    -------
    None
    """
    monkeypatch.setenv("FSLDIR", "/usr/local/fsl")
    check_fsl_is_installed()

    monkeypatch.delenv("FSLDIR", raising=False)
    with pytest.raises(SystemExit) as exit_info:
        check_fsl_is_installed()
    assert exit_info.value.code == 1


def test_get_paths_and_check_decomp_directory(tmp_path: Path) -> None:
    """
    Function to test get_paths and check_nfact_decomp_directory.

    Parameters
    ----------
    tmp_path: Path
        Pytest temporary directory path.

    Returns
    -------
    None
    """
    decomp_directory = tmp_path / "nfact_decomp"
    components_directory = decomp_directory / "components" / "NMF" / "decomp"
    group_avg_directory = decomp_directory / "group_averages"

    components_directory.mkdir(parents=True)
    group_avg_directory.mkdir(parents=True)

    dummy_component = components_directory / "W_NMF_dim50.nii.gz"
    dummy_component.write_text("dummy")
    dummy_avg = group_avg_directory / "coords_for_fdt_matrix2"
    dummy_avg.write_text("dummy")

    arguments_decomp = {
        "nfact_decomp_dir": str(decomp_directory),
        "decomp_dir": None,
        "algo": "nmf",
    }
    extracted_paths = get_paths(arguments_decomp)
    assert extracted_paths["component_path"] == str(components_directory)
    assert extracted_paths["group_average_path"] == str(group_avg_directory)

    check_nfact_decomp_directory(
        extracted_paths["component_path"], extracted_paths["group_average_path"]
    )

    empty_directory = tmp_path / "empty_dir"
    empty_directory.mkdir()
    with pytest.raises(SystemExit) as exit_info:
        check_nfact_decomp_directory(str(empty_directory), str(group_avg_directory))
    assert exit_info.value.code == 1


def test_base_args_builders() -> None:
    """
    Function to test base_args configuration builders.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    colour_dict = colours()
    parser_instance = argparse.ArgumentParser()
    cluster_args(parser_instance, colour_dict)
    parallel_args(parser_instance, colour_dict, "Parallel cores help")
    set_up_args(parser_instance, colour_dict)
    base_arguments(parser_instance)
    seed_roi_args(parser_instance)
    algo_arg(parser_instance)

    parsed_namespace = parser_instance.parse_args(
        ["--cluster", "--n_cores", "4", "--algo", "ICA"]
    )
    assert parsed_namespace.cluster is True
    assert parsed_namespace.n_cores == "4"
    assert parsed_namespace.algo == "ICA"

    decomp_parser = argparse.ArgumentParser()
    nfact_decomp_folder(decomp_parser)
    decomp_namespace = decomp_parser.parse_args(
        ["--dim", "50", "--nfact_folder", "/path/to/folder"]
    )
    assert decomp_namespace.dim == "50"
    assert decomp_namespace.nfact_folder == "/path/to/folder"
