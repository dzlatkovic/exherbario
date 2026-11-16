"""Study-level PCA for aligned quantitative profiles."""

import numpy as np


def calculate_pca(profiles, *, basis: str, scale: bool):
    """Each profile maps a case-folded feature name to its label and value."""
    all_keys = set().union(*(profile.keys() for profile in profiles))
    complete = sorted(key for key in all_keys if all(
        key in profile and profile[key][1] is not None for profile in profiles
    ))
    labels = {
        key: next(profile[key][0] for profile in profiles if key in profile)
        for key in sorted(all_keys)
    }
    missing = [labels[key] for key in sorted(all_keys - set(complete))]
    composition = basis == "peak_area_percent"
    zeros = []
    divisor = 1.0
    if composition:
        zeros = [labels[key] for key in complete if any(profile[key][1] == 0 for profile in profiles)]
        complete = [key for key in complete if labels[key] not in zeros]
    if len(complete) < 2:
        raise ValueError("PCA needs at least two shared features with eligible values in every profile.")

    matrix = np.array([[profile[key][1] for key in complete] for profile in profiles], dtype=float)
    if composition:
        matrix = np.log(matrix)
        matrix -= matrix.mean(axis=1, keepdims=True)
        scale = False
    else:
        divisor = float(matrix.max()) or 1.0
        matrix /= divisor

    matrix -= matrix.mean(axis=0)
    deviation = matrix.std(axis=0, ddof=1)
    variable = deviation > (8 * np.finfo(float).eps if composition else 0)
    constant = [labels[key] for key, keep in zip(complete, variable) if not keep]
    matrix = matrix[:, variable]
    features = [labels[key] for key, keep in zip(complete, variable) if keep]
    if len(features) < 2:
        raise ValueError("PCA needs at least two shared features that vary across the selected profiles.")
    if scale:
        matrix /= deviation[variable]

    scores, singular, loadings = np.linalg.svd(matrix, full_matrices=False)
    anchor = np.abs(loadings[:2]).argmax(axis=1)
    signs = np.sign(loadings[np.arange(2), anchor])
    variance = singular ** 2
    return {
        "configuration": {
            "transform": "centered_log_ratio" if composition else "center",
            "measurement_basis": basis,
            "global_divisor": divisor,
            "scale": scale,
            "missing": "shared_measured_features",
            "zeros": "exclude_features_with_zeros" if composition else "retain",
            "replicates": "one_profile_per_lab_sample",
            "numpy_version": np.__version__,
        },
        "scores": (scores[:, :2] * singular[:2] * signs).tolist(),
        "loadings": (loadings[:2].T * signs).tolist(),
        "features": features,
        "explained_variance": (100 * variance / variance.sum()).tolist(),
        "excluded": {"missing": missing, "zeros": zeros, "constant": constant},
    }
