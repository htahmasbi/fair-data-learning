"""Tests for FAIR packaging artifacts (CITATION.cff, OWL, RO-Crate, Zenodo)."""

import json
from pathlib import Path

import pytest
import yaml

from rdflib import Graph
from rdflib.namespace import OWL, RDF, RDFS

from src.ontology import build_ontology
from src.ro_crate import build_ro_crate
from src.vocab import MAT


def test_ontology_declares_classes_and_properties():
    g = build_ontology()
    assert (MAT.Material, RDF.type, OWL.Class) in g
    assert (MAT.CrystalSystem, RDF.type, OWL.Class) in g
    assert (MAT.SpaceGroup, RDF.type, OWL.Class) in g
    # Datatype property for band gap
    assert (MAT.hasBandGap, RDF.type, OWL.DatatypeProperty) in g
    # Object property linking material -> crystal system
    assert (MAT.hasCrystalSystem, RDF.type, OWL.ObjectProperty) in g
    # Subclass relationship
    assert (MAT.StableMaterial, RDFS.subClassOf, MAT.Material) in g


def test_ontology_file_serializes_and_reloads():
    from src.ontology import build_ontology
    import tempfile

    g = build_ontology()
    with tempfile.NamedTemporaryFile(suffix=".owl") as tmp:
        g.serialize(destination=tmp.name, format="xml")
        reloaded = Graph()
        reloaded.parse(tmp.name, format="xml")
    assert len(reloaded) == len(g)


def test_ro_crate_is_well_formed():
    crate = build_ro_crate()
    assert "ro/crate/1.1" in crate["@context"]
    graph = crate["@graph"]
    ids = [node["@id"] for node in graph]
    # A root dataset + a metadata descriptor must exist
    assert "./" in ids
    assert "ro-crate-metadata.json" in ids
    # Data entities referenced as files
    files = [n for n in graph if n["@type"] == "File"]
    assert any("mp_oxides_clean.csv" in f["@id"] for f in files)
    assert any("knowledge_graph.ttl" in f["@id"] for f in files)


def test_citation_cff_is_valid_yaml():
    p = Path("CITATION.cff")
    assert p.exists()
    data = yaml.safe_load(p.read_text())
    assert data["cff-version"].startswith("1.")
    assert data["title"]
    assert data["authors"]


def test_zenodo_json_is_valid():
    p = Path(".zenodo.json")
    assert p.exists()
    data = json.loads(p.read_text())
    assert data["upload_type"] == "software"
    assert data["license"] == "apache-2.0"
    assert data["creators"]