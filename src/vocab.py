"""Namespace and vocabulary definitions for the materials knowledge graph.

RDF works because every term has a URI, so two people can never
disagree on the *meaning* of a term: it points to a shared definition.
"""

from rdflib import Namespace

# Our own (ad-hoc) materials ontology - the URI base is made up here,
# but the point is: it is *stable, dereferenceable, and documented*.
MAT = Namespace("https://fair-data-learning.example.org/ontology/materials#")

# Instances/entities in our graph
MATERIALS = Namespace("https://fair-data-learning.example.org/entity/material/")
CRYSTAL_SYSTEMS = Namespace("https://fair-data-learning.example.org/entity/crystal_system/")
SPACE_GROUPS = Namespace("https://fair-data-learning.example.org/entity/space_group/")
DATASETS = Namespace("https://fair-data-learning.example.org/entity/dataset/")

# Single source of truth for the dataset entity URI, shared by the material
# graph (src/rdf.py) and the model-provenance graph (src/model_rdf.py).
MP_OXIDES_DATASET_ID = "mp-oxides-v1"

# Model-provenance entities (Stage 5: semantic MLOps)
MODELS = Namespace("https://fair-data-learning.example.org/entity/model/")
RUNS = Namespace("https://fair-data-learning.example.org/entity/run/")
MEASURES = Namespace("https://fair-data-learning.example.org/entity/measure/")
TASKS = Namespace("https://fair-data-learning.example.org/entity/task/")
HYPERPARAMETERS = Namespace("https://fair-data-learning.example.org/entity/hyperparameter/")
ALGORITHMS = Namespace("https://fair-data-learning.example.org/entity/algorithm/")
IMPLEMENTATIONS = Namespace("https://fair-data-learning.example.org/entity/implementation/")

# Standard namespaces
SDO = Namespace("https://schema.org/")
# PROV-O's canonical namespace is http:// (not https://) - using the wrong
# scheme silently produces a *different* term and breaks joins with any
# other tool's provenance data.
PROV = Namespace("http://www.w3.org/ns/prov#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
WIKIDATA = Namespace("http://www.wikidata.org/entity/")
OWL = Namespace("http://www.w3.org/2002/07/owl#")

# W3C community vocabulary for machine learning (experiments, runs, evaluations).
# We *use* it rather than inventing our own model vocabulary.
MLS = Namespace("http://www.w3.org/ns/mls#")