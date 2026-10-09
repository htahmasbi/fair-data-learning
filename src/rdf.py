"""Knowledge graph builder: CSV dataset -> RDF triples (Turtle).

Each material row becomes a node typed as mat:Material with:
  - composition & structural properties (typed literals)
  - links to standardized crystal-system / space-group nodes
  - element participation (linked to Wikidata chemical-element entities)
  - provenance: every material wasDerivedFrom a Materials Project URL

The dataset itself is a prov:Collection whose members are the materials,
and main() also merges the model-provenance graph (src/model_rdf.py) so
one SPARQL query can traverse materials -> dataset -> model -> metrics.

Output: data/processed/knowledge_graph.ttl (interoperable standard format).
"""

import sys
from pathlib import Path

import pandas as pd
from rdflib import Graph, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS

# Make `from src import ...` work when run as `python src/rdf.py`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_params
from src.vocab import (
    ALGORITHMS,
    CRYSTAL_SYSTEMS,
    DATASETS,
    HYPERPARAMETERS,
    IMPLEMENTATIONS,
    MATERIALS,
    MAT,
    MEASURES,
    MLS,
    MODELS,
    MP_OXIDES_DATASET_ID,
    PROV,
    RDFS,
    RUNS,
    SDO,
    SPACE_GROUPS,
    TASKS,
    WIKIDATA,
    XSD,
)

# Wikidata chemical element URIs (subset used by the dataset; extendable).
ELEMENT_URIS = {
    "O": WIKIDATA["Q629"],
    "N": WIKIDATA["Q627"],
    "Cl": WIKIDATA["Q688"],
    "V": WIKIDATA["Q1054"],
    "F": WIKIDATA["Q650"],
    "Mg": WIKIDATA["Q660"],
    "Si": WIKIDATA["Q670"],
    "Ti": WIKIDATA["Q716"],
    "Fe": WIKIDATA["Q677"],
    "Ca": WIKIDATA["Q706"],
    "Al": WIKIDATA["Q665"],
    "Na": WIKIDATA["Q658"],
    "Li": WIKIDATA["Q568"],
    "K": WIKIDATA["Q703"],
    "Sr": WIKIDATA["Q938"],
    "Ba": WIKIDATA["Q645"],
    "Cu": WIKIDATA["Q753"],
    "Zn": WIKIDATA["Q758"],
    "Zr": WIKIDATA["Q1038"],
    "Nb": WIKIDATA["Q1046"],
    "Mo": WIKIDATA["Q1053"],
    "W": WIKIDATA["Q743"],
    "S": WIKIDATA["Q682"],
    "P": WIKIDATA["Q674"],
    "B": WIKIDATA["Q618"],
}


def material_uri(material_id: str) -> URIRef:
    return MATERIALS[material_id]


def build_graph(df: pd.DataFrame) -> Graph:
    g = Graph()
    g.bind("mat", MAT)
    g.bind("matl", MATERIALS)  # handy short prefix for material entities
    g.bind("sdo", SDO)
    g.bind("prov", PROV)
    g.bind("mls", MLS)
    g.bind("rdfs", RDFS)
    g.bind("wd", WIKIDATA)

    dataset_uri = DATASETS[MP_OXIDES_DATASET_ID]

    for _, row in df.iterrows():
        m = material_uri(row["material_id"])
        g.add((m, RDF.type, MAT.Material))
        # Membership makes the dataset <-> materials link queryable, so
        # SPARQL can count materials *and* follow provenance to the model.
        g.add((dataset_uri, PROV.hadMember, m))
        g.add((m, RDFS.label, Literal(row["formula"])))
        g.add((m, MAT.hasFormula, Literal(row["formula"])))
        g.add((m, MAT.hasBandGap, Literal(float(row["band_gap"]), datatype=XSD.double)))
        g.add(
            (
                m,
                MAT.hasFormationEnergyPerAtom,
                Literal(float(row["formation_energy_per_atom"]), datatype=XSD.double),
            )
        )
        g.add((m, MAT.hasDensity, Literal(float(row["density"]), datatype=XSD.double)))
        g.add((m, MAT.isStable, Literal(bool(row["is_stable"]), datatype=XSD.boolean)))

        # Crystal system + space group as typed nodes
        cs_uri = CRYSTAL_SYSTEMS[row["crystal_system"]]
        g.add((cs_uri, RDF.type, MAT.CrystalSystem))
        g.add((m, MAT.hasCrystalSystem, cs_uri))

        sg_uri = SPACE_GROUPS[row["space_group"].replace(" ", "_")]
        g.add((sg_uri, RDF.type, MAT.SpaceGroup))
        g.add((m, MAT.hasSpaceGroup, sg_uri))

        # Element participation via Wikidata URIs
        for symbol in _elements_of_formula(row["formula"]):
            if symbol in ELEMENT_URIS:
                g.add((m, MAT.containsElement, ELEMENT_URIS[symbol]))

        # Provenance: derived from Materials Project record
        g.add((m, PROV.wasDerivedFrom, URIRef(f"https://materialsproject.org/materials/{row['material_id']}")))

    # Dataset-level provenance
    g.add((dataset_uri, RDF.type, PROV.Entity))
    g.add((dataset_uri, RDF.type, PROV.Collection))
    g.add((dataset_uri, RDF.type, MLS.Dataset))  # ML-Schema type for MLS:Run inputs
    g.add((dataset_uri, SDO.name, Literal("Materials Project Oxides dataset (1000 subset)")))
    query_bnode = BNode()
    g.add((dataset_uri, PROV.wasGeneratedBy, query_bnode))
    g.add((query_bnode, PROV.used, URIRef("https://materialsproject.org/api")))
    g.add((query_bnode, PROV.wasAttributedTo, URIRef("https://github.com/htahmasbi")))

    return g


def _elements_of_formula(formula: str):
    """Crude element extraction for simple oxide formulas (e.g. 'Fe2O3' -> ['Fe','O'])."""
    import re

    return re.findall(r"[A-Z][a-z]?", formula)


def main() -> None:
    params = load_params()
    out_dir = Path(params["data"]["output_dir"])
    df = pd.read_csv(Path(params["data"]["input"]))
    g = build_graph(df)

    # Stage 5: merge model provenance into the same graph, so a single
    # SPARQL query can walk materials -> dataset -> training run -> model.
    from src.model_rdf import build_model_graph, read_metrics

    model_graph = build_model_graph(metrics=read_metrics(), params=params)
    for triple in model_graph:
        g.add(triple)
    for prefix, ns in {
        "model": MODELS,
        "run": RUNS,
        "meas": MEASURES,
        "task": TASKS,
        "hparam": HYPERPARAMETERS,
        "algo": ALGORITHMS,
        "impl": IMPLEMENTATIONS,
    }.items():
        g.bind(prefix, ns)
    print(f"Merged {len(model_graph)} model-provenance triples")

    out_path = out_dir / "knowledge_graph.ttl"
    g.serialize(destination=out_path, format="turtle")
    print(f"Built graph with {len(g)} triples from {len(df)} materials")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()