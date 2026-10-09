"""Stage 5: model provenance as RDF (PROV-O + ML-Schema).

These tests verify the *links* - model -> run -> dataset -> metrics - because
provenance is only useful if it joins.
"""

from pathlib import Path

import pandas as pd
import pytest
from rdflib import URIRef
from rdflib.namespace import RDF

from src.config import load_params
from src.model_rdf import (
    ESTIMATOR_CLASS,
    build_model_graph,
    file_md5,
    read_citation,
    read_metrics,
)
from src.rdf import build_graph
from src.sparql import run_query
from src.vocab import DATASETS, MEASURES, MLS, PROV, SDO, OWL

ORCID = "https://orcid.org/0000-0002-3072-8217"
DATASET_URI = DATASETS["mp-oxides-v1"]

# Deterministic metadata for tests (real CITATION.cff / git are integration-tested)
FAKE_CITATION = {
    "name": "Hossein Tahmasbi",
    "orcid": ORCID,
    "repository": "https://github.com/htahmasbi/fair-data-learning",
    "license": "Apache-2.0",
}
FAKE_GIT = {"sha": "abc123def456", "committed_at": "2026-10-08T12:00:00+00:00"}


def _make_model_file(tmp_path: Path, content: bytes = b"model-bytes-v1") -> Path:
    path = tmp_path / "model.pkl"
    path.write_bytes(content)
    return path


def _build(tmp_path: Path, content: bytes = b"model-bytes-v1"):
    return build_model_graph(
        metrics=read_metrics(),
        params=load_params(),
        model_path=_make_model_file(tmp_path, content),
        citation=FAKE_CITATION,
        git_info=FAKE_GIT,
    )


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "material_id": ["mp-1", "mp-2"],
            "formula": ["Fe2O3", "MgO"],
            "space_group": ["R-3c", "Fm-3m"],
            "crystal_system": ["Trigonal", "Cubic"],
            "band_gap": [2.1, 7.8],
            "formation_energy_per_atom": [-3.0, -5.0],
            "density": [5.2, 3.6],
            "is_stable": [True, True],
        }
    )


def _combined_graph(tmp_path: Path):
    """Material graph + model graph, as serialized by the semantic stage."""
    g = build_graph(_sample_df())
    for triple in _build(tmp_path):
        g.add(triple)
    return g


def test_citation_file_is_source_of_truth_for_orcid():
    assert read_citation()["orcid"] == ORCID


def test_missing_model_raises_actionable_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="dvc repro"):
        build_model_graph(
            metrics=read_metrics(),
            params={"train": {"models": {}}},
            model_path=tmp_path / "missing.pkl",
            citation=FAKE_CITATION,
            git_info=FAKE_GIT,
        )


def test_model_uri_is_content_addressed(tmp_path):
    """Same bytes -> same identity; different bytes -> different identity."""
    g1 = _build(tmp_path, b"weights-a")
    g2 = _build(tmp_path, b"weights-a")
    g3 = _build(tmp_path, b"weights-b")
    assert set(g1.subjects(RDF.type, MLS.Model)) == set(g2.subjects(RDF.type, MLS.Model))
    assert set(g1.subjects(RDF.type, MLS.Model)) != set(g3.subjects(RDF.type, MLS.Model))
    # The URI really is the md5 of the file
    model_uri = next(g1.subjects(RDF.type, MLS.Model))
    assert file_md5(_make_model_file(tmp_path, b"weights-a"))[:12] in str(model_uri)


def test_model_run_links_dataset_and_measurements(tmp_path):
    g = _build(tmp_path)
    expected_r2 = read_metrics()["cv_metrics"]["GradientBoost"]["cv_r2_mean"]

    model_uri = next(g.subjects(RDF.type, MLS.Model))
    run = next(g.objects(model_uri, PROV.wasGeneratedBy))
    # Data lineage: run consumed the *same* dataset URI the material graph uses
    assert DATASET_URI in list(g.objects(run, MLS.hasInput))
    # Performance lineage: run emitted an evaluation of CV R2 with the real value
    r2_values = [
        float(v)
        for ev in g.objects(run, MLS.hasOutput)
        for v in g.objects(ev, MLS.hasValue)
        if list(g.objects(ev, MLS.specifiedBy)) == [MEASURES["cv_r2_mean"]]
    ]
    assert expected_r2 in r2_values


def test_model_is_attributed_to_author_orcid(tmp_path):
    g = _build(tmp_path)
    model_uri = next(g.subjects(RDF.type, MLS.Model))
    assert list(g.objects(model_uri, PROV.wasAttributedTo)) == [URIRef(ORCID)]
    assert (URIRef(ORCID), RDF.type, PROV.Agent) in g
    assert (URIRef(ORCID), RDF.type, SDO.Person) in g


def test_hyperparameters_are_queryable_data(tmp_path):
    g = _build(tmp_path)
    settings = [
        (list(g.objects(s, MLS.specifiedBy)), list(g.objects(s, MLS.hasValue)))
        for s in g.subjects(RDF.type, MLS.HyperParameterSetting)
    ]
    learning_rate = [v for hp, v in settings if str(hp[0]).endswith("learning_rate")]
    assert learning_rate, "expected a learning_rate hyperparameter setting"
    assert float(learning_rate[0][0]) == pytest.approx(0.1)


def test_version_and_license_asserted(tmp_path):
    g = _build(tmp_path)
    model_uri = next(g.subjects(RDF.type, MLS.Model))
    assert str(next(g.objects(model_uri, OWL.versionInfo))) == "abc123def456"
    assert any("Apache-2.0" in str(v) for v in g.objects(model_uri, SDO.license))


def test_estimator_mapping_matches_training_module():
    """Guards against drift between model_rdf.py and train.py."""
    from src.train import MODEL_REGISTRY

    assert set(ESTIMATOR_CLASS) == set(MODEL_REGISTRY)


def test_lineage_sparql_query_joins_model_to_dataset(tmp_path):
    g = _combined_graph(tmp_path)
    rows = list(run_query(g, "model_lineage"))
    assert len(rows) == 1
    model, algorithm, dataset, cv_r2, author = rows[0]
    assert str(dataset) == str(DATASET_URI)
    assert str(author) == ORCID
    assert float(cv_r2) == pytest.approx(
        read_metrics()["cv_metrics"]["GradientBoost"]["cv_r2_mean"]
    )
    assert str(algorithm).endswith("GradientBoost")


def test_materials_query_counts_members_behind_model(tmp_path):
    """Cross-domain query: materials graph x model provenance graph."""
    g = _combined_graph(tmp_path)
    rows = list(run_query(g, "materials_behind_the_model"))
    assert len(rows) == 1
    assert int(rows[0][2]) == 2  # the two sample materials


def test_all_models_query_compares_candidates(tmp_path):
    g = _combined_graph(tmp_path)
    rows = list(run_query(g, "all_models_quality"))
    assert len(rows) == 3
    scores = [float(r[2]) for r in rows]
    assert scores == sorted(scores, reverse=True)
