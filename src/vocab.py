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

# Standard namespaces
SDO = Namespace("https://schema.org/")
PROV = Namespace("https://www.w3.org/ns/prov#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
WIKIDATA = Namespace("http://www.wikidata.org/entity/")