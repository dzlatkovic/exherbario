from app.chemistry.services.pca_analysis import calculate_pca



def test_compositional_pca_reports_excluded_features():
    profiles = [
        {"a": ("A", 10.0), "b": ("B", 20.0), "c": ("C", 0.0), "d": ("D", None)},
        {"a": ("A", 20.0), "b": ("B", 15.0), "c": ("C", 10.0)},
        {"a": ("A", 25.0), "b": ("B", 5.0), "c": ("C", 5.0)},
    ]
    result = calculate_pca(profiles, basis="peak_area_percent", scale=True)
    assert result["features"] == ["A", "B"]
    assert result["excluded"] == {"zeros": ["C"], "missing": ["D"], "constant": []}
    assert result["configuration"]["scale"] is False
