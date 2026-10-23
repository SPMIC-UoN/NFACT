"""
Command builder for generating NFACT CLI commands from graphical user interface state.
"""

import shlex


def format_command_string(command_arguments: list) -> str:
    """
    Format a list of command arguments into a shell-escaped command string.

    Parameters
    ----------
    command_arguments: list
        List of command arguments.

    Returns
    -------
    formatted_string: str
        Formatted, shell-escaped command string.
    """
    if not command_arguments:
        return ""
    return shlex.join([str(argument) for argument in command_arguments])


def append_cluster_options(
    command_list: list,
    state: dict,
    cluster_flag: str = "-C",
    gpu_flag: str = "-g",
) -> None:
    """
    Append standard cluster and GPU arguments to a command list.

    Parameters
    ----------
    command_list: list
        Target command list to append into.
    state: dict
        Dictionary of parameter state values.
    cluster_flag: str
        The CLI flag used to enable cluster submission (e.g. '-C' or '-Cl').
    gpu_flag: str
        The CLI flag used to enable GPU computation (e.g. '-g' or '-G').

    Returns
    -------
    None
    """
    if state.get("cluster"):
        command_list.append(cluster_flag)
    if state.get("cluster_queue"):
        command_list.extend(["-cq", str(state["cluster_queue"]).strip()])
    if state.get("cluster_ram"):
        command_list.extend(["-cr", str(state["cluster_ram"]).strip()])
    if state.get("cluster_time"):
        command_list.extend(["-ct", str(state["cluster_time"]).strip()])
    if state.get("cluster_qos"):
        command_list.extend(["-cqos", str(state["cluster_qos"]).strip()])
    if state.get("gpu"):
        command_list.append(gpu_flag)


def build_pipeline_command(state: dict) -> list:
    """
    Construct the CLI command list for the main nfact pipeline.

    Parameters
    ----------
    state: dict
        Dictionary of state values from the pipeline tab.

    Returns
    -------
    command_list: list
        Complete list of command arguments.
    """
    command_list = ["nfact"]

    if state.get("config"):
        command_list.extend(["-c", str(state["config"]).strip()])
        return command_list

    if state.get("list_of_subjects"):
        command_list.extend(["-l", str(state["list_of_subjects"]).strip()])
    if state.get("outdir"):
        command_list.extend(["-o", str(state["outdir"]).strip()])
    if state.get("folder_name") and state["folder_name"] != "nfact":
        command_list.extend(["-n", str(state["folder_name"]).strip()])

    if state.get("pp_skip"):
        command_list.append("-P")
    if state.get("qc_skip"):
        command_list.append("-Q")
    if state.get("dr_skip"):
        command_list.append("-D")
    if state.get("overwrite"):
        command_list.append("-O")

    # Cluster options
    append_cluster_options(command_list, state, cluster_flag="-C", gpu_flag="-g")

    # Decomp parameters
    if state.get("dim"):
        command_list.extend(["-d", str(state["dim"]).strip()])
    if state.get("algo"):
        command_list.extend(["-a", str(state["algo"]).strip()])

    # Pre-processing parameters (relevant when pp is not skipped)
    if not state.get("pp_skip"):
        if state.get("file_tree"):
            command_list.extend(["-f", str(state["file_tree"]).strip()])
        if state.get("seed"):
            seeds_list = (
                state["seed"]
                if isinstance(state["seed"], list)
                else str(state["seed"]).split()
            )
            if seeds_list:
                command_list.append("-s")
                command_list.extend([str(seed_item) for seed_item in seeds_list])
        if state.get("warps"):
            warps_list = (
                state["warps"]
                if isinstance(state["warps"], list)
                else str(state["warps"]).split()
            )
            if warps_list:
                command_list.append("-w")
                command_list.extend([str(warp_item) for warp_item in warps_list])
        if state.get("bpx_path"):
            command_list.extend(["-b", str(state["bpx_path"]).strip()])
        if state.get("roi"):
            rois_list = (
                state["roi"]
                if isinstance(state["roi"], list)
                else str(state["roi"]).split()
            )
            if rois_list:
                command_list.append("-r")
                command_list.extend([str(roi_item) for roi_item in rois_list])
        if state.get("seedref"):
            command_list.extend(["-sr", str(state["seedref"]).strip()])
        if state.get("target2"):
            command_list.extend(["-t", str(state["target2"]).strip()])
    else:
        if state.get("rf_decomp"):
            command_list.extend(["-rf", str(state["rf_decomp"]).strip()])

    # QC threshold
    if not state.get("qc_skip") and state.get("threshold"):
        command_list.extend(["--threshold", str(state["threshold"]).strip()])

    return command_list


def build_pp_command(state: dict) -> list:
    """
    Construct the CLI command list for nfact_pp.

    Parameters
    ----------
    state: dict
        Dictionary of state values from the pre-process tab.

    Returns
    -------
    command_list: list
        Complete list of command arguments.
    """
    command_list = ["nfact_pp"]

    if state.get("list_of_subjects"):
        command_list.extend(["-l", str(state["list_of_subjects"]).strip()])
    if state.get("outdir"):
        command_list.extend(["-o", str(state["outdir"]).strip()])
    if state.get("overwrite"):
        command_list.append("-O")

    if state.get("file_tree"):
        command_list.extend(["-f", str(state["file_tree"]).strip()])
    if state.get("seed"):
        seeds_list = (
            state["seed"]
            if isinstance(state["seed"], list)
            else str(state["seed"]).split()
        )
        if seeds_list:
            command_list.append("-s")
            command_list.extend([str(seed_item) for seed_item in seeds_list])
    if state.get("warps"):
        warps_list = (
            state["warps"]
            if isinstance(state["warps"], list)
            else str(state["warps"]).split()
        )
        if warps_list:
            command_list.append("-w")
            command_list.extend([str(warp_item) for warp_item in warps_list])
    if state.get("bpx_path"):
        command_list.extend(["-b", str(state["bpx_path"]).strip()])
    if state.get("roi"):
        rois_list = (
            state["roi"]
            if isinstance(state["roi"], list)
            else str(state["roi"]).split()
        )
        if rois_list:
            command_list.append("-r")
            command_list.extend([str(roi_item) for roi_item in rois_list])
    if state.get("seedref"):
        command_list.extend(["-sr", str(state["seedref"]).strip()])
    if state.get("target2"):
        command_list.extend(["-t", str(state["target2"]).strip()])
    if state.get("nsamples") and str(state["nsamples"]) != "5000":
        command_list.extend(["-ns", str(state["nsamples"]).strip()])
    if state.get("min_mask"):
        command_list.append("-mm")
    if state.get("ptx_options"):
        command_list.extend(["-p", str(state["ptx_options"]).strip()])
    if state.get("exclusion"):
        command_list.extend(["-e", str(state["exclusion"]).strip()])
    if state.get("stop"):
        command_list.extend(["-S", str(state["stop"]).strip()])
    if state.get("add_seeds"):
        command_list.extend(["-A", str(state["add_seeds"]).strip()])
    if state.get("first_ref"):
        command_list.extend(["-F", str(state["first_ref"]).strip()])

    if state.get("downsample"):
        command_list.append("-D")
    if state.get("voxel_size"):
        command_list.extend(["-vx", str(state["voxel_size"]).strip()])
    if state.get("vol_ref"):
        command_list.extend(["-vl", str(state["vol_ref"]).strip()])

    if state.get("n_cores"):
        command_list.extend(["-n", str(state["n_cores"]).strip()])

    append_cluster_options(command_list, state, cluster_flag="-C", gpu_flag="-G")

    return command_list


def build_decomp_command(state: dict) -> list:
    """
    Construct the CLI command list for nfact_decomp.

    Parameters
    ----------
    state: dict
        Dictionary of state values from the decomposition tab.

    Returns
    -------
    command_list: list
        Complete list of command arguments.
    """
    command_list = ["nfact_decomp"]

    if state.get("list_of_subjects"):
        command_list.extend(["-l", str(state["list_of_subjects"]).strip()])
    if state.get("outdir"):
        command_list.extend(["-o", str(state["outdir"]).strip()])
    if state.get("seeds"):
        seeds_list = (
            state["seeds"]
            if isinstance(state["seeds"], list)
            else str(state["seeds"]).split()
        )
        if seeds_list:
            command_list.append("-s")
            command_list.extend([str(seed_item) for seed_item in seeds_list])
    if state.get("roi"):
        rois_list = (
            state["roi"]
            if isinstance(state["roi"], list)
            else str(state["roi"]).split()
        )
        if rois_list:
            command_list.append("-r")
            command_list.extend([str(roi_item) for roi_item in rois_list])
    if state.get("matrix"):
        command_list.extend(["-m", str(state["matrix"]).strip()])
    if state.get("config_file"):
        command_list.extend(["-f", str(state["config_file"]).strip()])
    if state.get("overwrite"):
        command_list.append("-O")

    if state.get("algo"):
        command_list.extend(["-a", str(state["algo"]).strip()])
    if state.get("dim"):
        command_list.extend(["-d", str(state["dim"]).strip()])
    if state.get("iterations") and str(state["iterations"]) != "20":
        command_list.extend(["-i", str(state["iterations"]).strip()])
    if state.get("n_cores"):
        command_list.extend(["-n", str(state["n_cores"]).strip()])

    if state.get("wta"):
        command_list.append("-w")
    if state.get("wta_zhr"):
        command_list.extend(["-g", str(state["wta_zhr"]).strip()])
    if state.get("no_decomp"):
        command_list.append("-X")

    # ICA-specific options
    if str(state.get("algo", "")).lower() == "ica":
        if state.get("pca_comp"):
            command_list.extend(["-c", str(state["pca_comp"]).strip()])
        if state.get("pca_type"):
            command_list.extend(["-p", str(state["pca_type"]).strip()])
        if state.get("spatial_sign_flip"):
            command_list.append("-S")

    # Outputs
    if state.get("cifti"):
        command_list.append("-C")
    if state.get("disk_save"):
        command_list.append("-D")
    if state.get("wta_save"):
        command_list.append("-W")
    if state.get("wta_thr"):
        command_list.extend(["-z", str(state["wta_thr"]).strip()])
    if state.get("normalise"):
        command_list.append("-N")
    if state.get("threshold"):
        command_list.extend(["-t", str(state["threshold"]).strip()])
    if state.get("cluster_save"):
        command_list.append("-CS")
    if state.get("initialisation_matrices"):
        command_list.append("-I")

    append_cluster_options(command_list, state, cluster_flag="-Cl", gpu_flag="-G")

    return command_list


def build_qc_command(state: dict) -> list:
    """
    Construct the CLI command list for nfact_Qc.

    Parameters
    ----------
    state: dict
        Dictionary of state values from the quality control tab.

    Returns
    -------
    command_list: list
        Complete list of command arguments.
    """
    command_list = ["nfact_Qc"]

    if state.get("nfact_folder"):
        command_list.extend(["-n", str(state["nfact_folder"]).strip()])
    if state.get("dim"):
        command_list.extend(["-d", str(state["dim"]).strip()])
    if state.get("algo"):
        command_list.extend(["-a", str(state["algo"]).strip()])
    if state.get("threshold") and str(state["threshold"]) != "2":
        command_list.extend(["-t", str(state["threshold"]).strip()])
    if state.get("overwrite"):
        command_list.append("-O")

    return command_list


def build_dr_command(state: dict) -> list:
    """
    Construct the CLI command list for nfact_dr.

    Parameters
    ----------
    state: dict
        Dictionary of state values from the dual regression tab.

    Returns
    -------
    command_list: list
        Complete list of command arguments.
    """
    command_list = ["nfact_dr"]

    if state.get("list_of_subjects"):
        command_list.extend(["-l", str(state["list_of_subjects"]).strip()])
    if state.get("outdir"):
        command_list.extend(["-o", str(state["outdir"]).strip()])
    if state.get("overwrite"):
        command_list.append("-O")

    if state.get("algo"):
        command_list.extend(["-a", str(state["algo"]).strip()])
    if state.get("seeds"):
        seeds_list = (
            state["seeds"]
            if isinstance(state["seeds"], list)
            else str(state["seeds"]).split()
        )
        if seeds_list:
            command_list.append("-s")
            command_list.extend([str(seed_item) for seed_item in seeds_list])
    if state.get("roi"):
        rois_list = (
            state["roi"]
            if isinstance(state["roi"], list)
            else str(state["roi"]).split()
        )
        if rois_list:
            command_list.append("-r")
            command_list.extend([str(roi_item) for roi_item in rois_list])

    if state.get("nfact_decomp_dir"):
        command_list.extend(["-d", str(state["nfact_decomp_dir"]).strip()])
    if state.get("decomp_dir"):
        command_list.extend(["-dd", str(state["decomp_dir"]).strip()])

    if state.get("normalise"):
        command_list.append("-N")
    if state.get("dscalar"):
        command_list.append("-D")
    if state.get("threshold") and str(state["threshold"]) != "0":
        command_list.extend(["-t", str(state["threshold"]).strip()])
    if state.get("n_cores"):
        command_list.extend(["-n", str(state["n_cores"]).strip()])

    append_cluster_options(command_list, state, cluster_flag="-C", gpu_flag="-G")

    return command_list


def build_stats_command(state: dict) -> list:
    """
    Construct the CLI command list for nfact_stats.

    Parameters
    ----------
    state: dict
        Dictionary of state values from the statistics tab.

    Returns
    -------
    command_list: list
        Complete list of command arguments.
    """
    command_list = ["nfact_stats"]
    subcommand = state.get("subcommand", "loadings")
    command_list.append(subcommand)

    if state.get("list_of_subjects"):
        command_list.extend(["-l", str(state["list_of_subjects"]).strip()])
    if state.get("outdir"):
        command_list.extend(["-o", str(state["outdir"]).strip()])
    if state.get("nfact_folder"):
        command_list.extend(["-n", str(state["nfact_folder"]).strip()])
    if state.get("algo"):
        command_list.extend(["-a", str(state["algo"]).strip()])
    if state.get("dim"):
        command_list.extend(["-d", str(state["dim"]).strip()])
    if state.get("overwrite"):
        command_list.append("-O")

    if subcommand == "loadings":
        if state.get("threshold"):
            command_list.extend(["-t", str(state["threshold"]).strip()])
        if state.get("no_csv"):
            command_list.append("-C")
    elif subcommand == "statsmap":
        if state.get("components"):
            comps = (
                state["components"]
                if isinstance(state["components"], list)
                else str(state["components"]).split()
            )
            if comps:
                command_list.append("-c")
                command_list.extend([str(comp_item) for comp_item in comps])
        if state.get("map_name"):
            command_list.extend(["-m", str(state["map_name"]).strip()])
        if state.get("threshold"):
            command_list.extend(["-t", str(state["threshold"]).strip()])
        if state.get("group_only"):
            command_list.append("-G")
        if state.get("skip"):
            command_list.append("-S")

    return command_list


def build_config_command(state: dict) -> list:
    """
    Construct the CLI command list for nfact_config.

    Parameters
    ----------
    state: dict
        Dictionary of state values from the config tab.

    Returns
    -------
    command_list: list
        Complete list of command arguments.
    """
    command_list = ["nfact_config"]

    action = state.get("action", "pipeline")
    if action == "pipeline":
        command_list.append("-C")
    elif action == "decomp":
        command_list.append("-D")
    elif action == "subject_list" and state.get("subject_dir"):
        command_list.extend(["-s", str(state["subject_dir"]).strip()])
    elif action == "zip" and state.get("zip_dir"):
        command_list.extend(["-z", str(state["zip_dir"]).strip()])

    if state.get("output_dir"):
        command_list.extend(["-o", str(state["output_dir"]).strip()])
    if state.get("file_name"):
        command_list.extend(["-f", str(state["file_name"]).strip()])

    return command_list
