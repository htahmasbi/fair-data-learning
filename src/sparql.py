"""Example SPARQL queries against the materials knowledge graph.

Run:  python src/sparql.py
"""

import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace

PROV = Namespace("https://www.w3.org/ns/prov#")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MAT = Namespace("https://fair-data-learning.example.org/ontology/materials#")

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
}


def load_graph() -> Graph:
    g = Graph()
    g.parse(PROJECT_ROOT / "data" / "processed" / "knowledge_graph.ttl", format="turtle")
    return g


def main() -> None:
    g = load_graph()
    print(f"Loaded graph: {len(g)} triples\n")
    for name, query in QUERIES.items():
        print(f"{'=' * 60}\n{name} — SPARQL\n{'=' * 60}")
        results = g.query(query, initNs={"mat": MAT, "wd": Namespace("http://www.wikidata.org/entity/"), "prov": PROV})
        for row in results:
            print("  " + " | ".join(str(v) for v in row))
        print()


if __name__ == "__main__":
    main()