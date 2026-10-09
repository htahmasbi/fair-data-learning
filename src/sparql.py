"""Example SPARQL queries against the materials + model-provenance graph.

Run:  python src/sparql.py
"""

import sys
from pathlib import Path

from rdflib import Graph, Namespace

# Make `from src import ...` work when run as `python src/sparql.py`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vocab import DATASETS, MAT, MEASURES, MLS, MODELS, PROV, RDFS, WIKIDATA

# Prefix bindings for every query (avoids hardcoding URIs in query strings;
# note PROV uses https while ML-Schema uses http - a classic pitfall).
INIT_NS = {
    "mat": MAT,
    "mls": MLS,
    "prov": PROV,
    "rdfs": RDFS,
    "sdo": Namespace("https://schema.org/"),
    "wd": WIKIDATA,
    "meas": MEASURES,
    "model": MODELS,
    "ds": DATASETS,
}

QUERIES = {
    "top_band_gap": """# Top 5 semiconductors by band gap
SELECT ?material ?formula ?gap
WHERE {
  ?material a mat:Material ;
            mat:hasFormula ?formula ;
            mat:hasBandGap ?gap .
  FILTER(?gap > 0)
}
ORDER BY DESC(?gap)
LIMIT 5""",
    "contains_iron": """# Materials containing iron (linked via Wikidata URI)
SELECT ?material ?formula
WHERE {
  ?material a mat:Material ;
            mat:hasFormula ?formula ;
            mat:containsElement wd:Q677 .   # Q677 = Iron on Wikidata
}
LIMIT 10""",
    "stable_by_crystal_system": """# Count of stable materials per crystal system
SELECT ?system (COUNT(?material) AS ?n)
WHERE {
  ?material a mat:Material ;
            mat:hasCrystalSystem ?system ;
            mat:isStable true .
}
GROUP BY ?system
ORDER BY DESC(?n)""",
    "avg_gap_by_class": """# Average band gap grouped by crystal system
SELECT ?system (AVG(?gap) AS ?avg_gap) (COUNT(?material) AS ?n)
WHERE {
  ?material a mat:Material ;
            mat:hasCrystalSystem ?system ;
            mat:hasBandGap ?gap .
}
GROUP BY ?system
ORDER BY DESC(?avg_gap)""",
    "provenance": """# Everything's provenance: material -> source record
SELECT ?material ?source
WHERE {
  ?material a mat:Material ;
            prov:wasDerivedFrom ?source .
}
LIMIT 5""",
    "model_lineage": """# Which dataset produced the deployed model, how good is it,
# and who is accountable for it (FAIR F3)?
SELECT ?model ?algorithm ?dataset ?cvR2 ?author
WHERE {
  ?model a mls:Model ;
         prov:wasGeneratedBy ?run ;
         prov:wasAttributedTo ?author .
  ?run   mls:realizes ?algorithm ;
         mls:hasInput ?dataset ;
         mls:hasOutput ?evaluation .
  ?dataset a mls:Dataset .   # exclude hyperparameter settings / params.yaml inputs
  ?evaluation mls:specifiedBy meas:cv_r2_mean ;
              mls:hasValue ?cvR2 .
}""",
    "materials_behind_the_model": """# The money shot: how many materials are behind the deployed model?
# Joins the material graph with the model-provenance graph in one query.
SELECT ?model ?dataset (COUNT(?material) AS ?nMaterials) ?cvR2
WHERE {
  ?dataset prov:hadMember ?material .
  ?model  a mls:Model ; prov:wasGeneratedBy ?run .
  ?run    mls:hasInput ?dataset ; mls:hasOutput ?evaluation .
  ?evaluation mls:specifiedBy meas:cv_r2_mean ;
              mls:hasValue ?cvR2 .
}
GROUP BY ?model ?dataset ?cvR2""",
    "model_hyperparameters": """# Hyperparameters as queryable data (not buried in a script)
SELECT ?model ?hyperparameter ?value
WHERE {
  ?model a mls:Model ; prov:wasGeneratedBy ?run .
  ?run  mls:hasInput ?setting .
  ?setting a mls:HyperParameterSetting ;
           mls:specifiedBy ?hyperparameter ;
           mls:hasValue ?value .
}""",
    "all_models_quality": """# Compare every trained candidate by cross-validated R2
SELECT ?runName ?algorithm ?cvR2
WHERE {
  ?run a mls:Run ; sdo:name ?runName ;
       mls:realizes ?algorithm ;
       mls:hasOutput ?evaluation .
  ?evaluation mls:specifiedBy meas:cv_r2_mean ;
              mls:hasValue ?cvR2 .
}
ORDER BY DESC(?cvR2)""",
}


def load_graph() -> Graph:
    g = Graph()
    g.parse(PROJECT_ROOT / "data" / "processed" / "knowledge_graph.ttl", format="turtle")
    return g


def run_query(g: Graph, name: str):
    """Execute a named query with the shared prefix bindings (used by tests too)."""
    return g.query(QUERIES[name], initNs=INIT_NS)


def main() -> None:
    g = load_graph()
    print(f"Loaded graph: {len(g)} triples\n")
    for name, query in QUERIES.items():
        print(f"{'=' * 60}\n{name} — SPARQL\n{'=' * 60}")
        for row in run_query(g, name):
            print("  " + " | ".join(str(v) for v in row))
        print()


if __name__ == "__main__":
    main()