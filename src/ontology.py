"""OWL ontology generator: defines classes/properties used by the knowledge graph.

An ontology formalizes *what terms mean* and *how they relate* (e.g. every
Material has exactly one CrystalSystem; StableMaterial is a subclass of
Material). This is the machine-readable contract that makes data
interoperable across systems.

Output: metadata/materials_ontology.owl
Edit interactively afterwards in Protégé (or any XML/RDF editor).
"""

import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vocab import MAT

XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

# Short human labels for ontology classes/properties
CLASSES = {
    "Material": "A chemical substance studied for its properties",
    "CrystalSystem": "One of the seven crystal systems (cubic, hexagonal, ...)",
    "SpaceGroup": "A crystallographic space group (230 in total)",
    "Element": "A chemical element",
}

DATATYPE_PROPS = {
    "hasFormula": "Chemical formula as a string",
    "hasBandGap": "Electronic band gap in eV",
    "hasFormationEnergyPerAtom": "Formation energy per atom in eV/atom",
    "hasDensity": "Mass density in g/cm3",
    "isStable": "Thermodynamic stability flag",
}

OBJECT_PROPS = {
    "hasCrystalSystem": "Relates a Material to its CrystalSystem",
    "hasSpaceGroup": "Relates a Material to its SpaceGroup",
    "containsElement": "Relates a Material to a chemical Element it contains",
}


def build_ontology() -> Graph:
    g = Graph()
    g.bind("owl", OWL)
    g.bind("rdfs", RDFS)
    g.bind("mat", MAT)
    g.bind("xsd", XSD)

    # Ontology header
    g.add((MAT[""], RDF.type, OWL.Ontology))
    g.add((MAT[""], RDFS.label, Literal("Fair Data Learning Materials Ontology")))

    # Classes
    class_uris = {}
    for name, comment in CLASSES.items():
        uri = MAT[name]
        class_uris[name] = uri
        g.add((uri, RDF.type, OWL.Class))
        g.add((uri, RDFS.label, Literal(name)))
        g.add((uri, RDFS.comment, Literal(comment)))

    # Subclass: stable materials are a specialisation of materials
    g.add((MAT.StableMaterial, RDF.type, OWL.Class))
    g.add((MAT.StableMaterial, RDFS.subClassOf, MAT.Material))
    g.add((MAT.StableMaterial, RDFS.label, Literal("StableMaterial")))

    # Datatype properties (value literals typed with xsd)
    for name, comment in DATATYPE_PROPS.items():
        uri = MAT[name]
        g.add((uri, RDF.type, OWL.DatatypeProperty))
        g.add((uri, RDFS.label, Literal(name)))
        g.add((uri, RDFS.comment, Literal(comment)))
        g.add((uri, RDFS.domain, MAT.Material))
        g.add((uri, RDFS.range, XSD.string if name == "hasFormula" or name == "isStable" else XSD.double))

    # Object properties (link two individuals) with domain/range constraints
    for name, comment in OBJECT_PROPS.items():
        uri = MAT[name]
        g.add((uri, RDF.type, OWL.ObjectProperty))
        g.add((uri, RDFS.label, Literal(name)))
        g.add((uri, RDFS.comment, Literal(comment)))
        g.add((uri, RDFS.domain, MAT.Material))
        range_class = {
            "hasCrystalSystem": MAT.CrystalSystem,
            "hasSpaceGroup": MAT.SpaceGroup,
            "containsElement": MAT.Element,
        }[name]
        g.add((uri, RDFS.range, range_class))

    return g


def main() -> None:
    g = build_ontology()
    out_dir = PROJECT_ROOT / "metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "materials_ontology.owl"
    g.serialize(destination=out_path, format="xml")
    print(f"Ontology written: {out_path} ({len(g)} triples)")
    print("Open it in Protégé to browse/edit: https://protege.stanford.edu")


if __name__ == "__main__":
    main()