"""Tests for the FAIR/semantic layer (metadata, RDF builder)."""

import json

import pandas as pd
import pytest
from rdflib import Graph, Namespace
from rdflib.namespace import RDF

from src.rdf import build_graph
from src.vocab import MAT

METADATA_PATH = "metadata/dataset_metadata.jsonld"


def test_metadata_is_valid_json_ld():
    with open(METADATA_PATH) as f:
        doc = json.load(f)
    assert "@context" in doc
    assert "@type" in doc
    # FAIR: must be describable via a standard vocabulary
    assert any("Dataset" in t for t in doc["@type"])
    # Reusable: license must be declared
    assert "schema:license" in doc or "license" in doc


def _sample_df():
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


def test_graph_has_material_entities():
    g = build_graph(_sample_df())
    materials = list(g.subjects(RDF.type, MAT.Material))
    assert len(materials) == 2


def test_graph_has_properties_and_provenance():
    g = build_graph(_sample_df())
    n_band_gap = len(list(g.subject_objects(MAT.hasBandGap)))
    assert n_band_gap == 2
    # Provenance: every material links to a Materials Project URL
    from src.vocab import PROV

    n_derived = len(list(g.triples((None, PROV.wasDerivedFrom, None))))
    assert n_derived == 2


def test_graph_serializes_to_turtle():
    g = build_graph(_sample_df())
    ttl = g.serialize(format="turtle")
    assert "@prefix" in ttl
    assert "mat:" in ttl


def test_dataset_collection_has_material_members():
    """Stage 5: materials must be reachable from the dataset node, otherwise
    SPARQL cannot join 'this dataset' to 'these materials'."""
    from src.vocab import DATASETS, MP_OXIDES_DATASET_ID, PROV

    g = build_graph(_sample_df())
    dataset = DATASETS[MP_OXIDES_DATASET_ID]
    members = list(g.objects(dataset, PROV.hadMember))
    assert len(members) == 2
    assert (dataset, RDF.type, PROV.Collection) in g


def test_prov_namespace_is_canonical():
    """PROV-O's canonical namespace is http:// - the https:// variant is a
    *different* URI and would be aliased as prov1:, silently breaking any
    query written against the standard prefix."""
    from src.vocab import PROV

    assert str(PROV) == "http://www.w3.org/ns/prov#"
    ttl = build_graph(_sample_df()).serialize(format="turtle")
    assert "prov1:" not in ttl