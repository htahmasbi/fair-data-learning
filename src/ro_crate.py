"""RO-Crate generator: bundles dataset + metadata + provenance as a research object.

RO-Crate (https://www.researchobject.org/ro-crate/) is the EU/community standard
for *packaging* digital research outputs so they can be archived, cited, and
reused as a unit. Its central file is `ro-crate-metadata.json` (JSON-LD).

Output: metadata/ro-crate-metadata.json
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def build_ro_crate() -> dict:
    return {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "Fair Data Learning - Materials Project Oxides",
                "description": (
                    "Reproducible ML (band-gap prediction) + FAIR semantic layer "
                    "for 1000 oxide materials from the Materials Project."
                ),
                "datePublished": "2026-09-14",
                "license": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
                "creator": {"@id": "#htahmasbi"},
                "hasPart": [
                    {"@id": "./data/processed/mp_oxides_clean.csv"},
                    {"@id": "./data/processed/knowledge_graph.ttl"},
                    {"@id": "./metadata/dataset_metadata.jsonld"},
                ],
            },
            {
                "@id": "#htahmasbi",
                "@type": "Person",
                "name": "Hossein Tahmasbi",
                "url": "https://github.com/htahmasbi",
            },
            {
                "@id": "./data/processed/mp_oxides_clean.csv",
                "@type": "File",
                "name": "mp_oxides_clean.csv",
                "encodingFormat": "text/csv",
                "contentSize": 52071,
                "description": "1000 oxide materials from Materials Project (band gap, formation energy, crystal structure, density).",
                "isBasedOn": {"@id": "https://materialsproject.org/api"},
            },
            {
                "@id": "./data/processed/knowledge_graph.ttl",
                "@type": "File",
                "name": "knowledge_graph.ttl",
                "encodingFormat": "text/turtle",
                "description": "RDF knowledge graph: materials -> structures -> properties -> provenance (12,196 triples).",
            },
            {
                "@id": "./metadata/dataset_metadata.jsonld",
                "@type": "File",
                "name": "dataset_metadata.jsonld",
                "encodingFormat": "application/ld+json",
                "description": "Machine-readable dataset metadata using Schema.org + DCAT + PROV-O.",
            },
        ],
    }


def main() -> None:
    crate = build_ro_crate()
    out_dir = PROJECT_ROOT / "metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ro-crate-metadata.json"
    out_path.write_text(json.dumps(crate, indent=2))
    print(f"RO-Crate metadata written: {out_path}")
    print("Validate online with the RO-Crate validator: https://www.researchobject.org/ro-crate/validator/")


if __name__ == "__main__":
    main()