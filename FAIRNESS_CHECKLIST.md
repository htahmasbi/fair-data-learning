# FAIR Data Self-Assessment

How this repository meets the 15 FAIR sub-principles (Wilkinson et al., 2016),
with concrete evidence files for each.

Legend: ✅ implemented locally · 🟡 partially / requires external service · ❌ not yet

---

## F — Findable

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| F1 | (meta)data have a globally unique and persistent identifier | 🟡 | Identifiers assigned (`schema:identifier`, material URIs); needs a DOI/PID via Zenodo release for permanence |
| F2 | data are described with rich metadata | ✅ | `metadata/dataset_metadata.jsonld` (title, terms, units, keywords, variables) |
| F3 | metadata clearly include the identifier of the data | ✅ | `@id: https://example.org/datasets/mp-oxides-v1` + `dcterms:identifier` |
| F4 | (meta)data are registered or indexed in a searchable resource | 🟡 | Repo + JSON-LD public on GitHub; Zenodo registration pending |

## A — Accessible

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| A1 | (meta)data retrievable by their identifier via a standard protocol | ✅ | Public HTTP(S) URLs on GitHub/raw; `dcat:Distribution.accessURL` |
| A1.1 | protocol is open, free, and universally implementable | ✅ | HTTP(S), CSV + Turtle + JSON-LD formats (no proprietary formats) |
| A1.2 | protocol supports authentication/authorization (if needed) | ✅ | Data is open (no auth); API key access documented for re-fetching |
| A2 | metadata remain available even if the data no longer is | 🟡 | Metadata committed in git (survives); requires long-lived PID (Zenodo) |

## I — Interoperable

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I1 | use a formal, accessible, shared, broadly applicable language | ✅ | RDF/Turtle (`knowledge_graph.ttl`), JSON-LD; CSV is a W3C REC format |
| I2 | use FAIR vocabularies | ✅ | Schema.org, DCAT, Dublin Core (dcterms), W3C PROV-O, Wikidata entities |
| I3 | (meta)data include qualified references to other (meta)data | ✅ | `prov:wasDerivedFrom` → Materials Project records; `mat:containsElement wd:Q677` |

## R — Reusable

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| R1 | (meta)data are richly described with a plurality of accurate attributes | ✅ | JSON-LD: variables, units, query used, generator, spatial/temporal scope |
| R1.1 | data are released with a clear and accessible data usage license | ✅ | `CC-BY-4.0` in JSON-LD + `CITATION.cff` + `.zenodo.json` |
| R1.2 | (meta)data are associated with detailed provenance | ✅ | W3C PROV-O chain data → API query → Materials Project (`src/rdf.py`) |
| R1.3 | (meta)data meet domain-relevant community standards | 🟡 | Matches MP/pymatgen conventions; mapping to a full materials ontology (e.g. EMMO) is future work |

## Summary

**Fully met (✅): 9 · Partially met (🟡): 4 · Not met (❌): 0**

Remaining actions to reach 100%:
1. **Publish a GitHub Release** → auto-archives to Zenodo (via `.zenodo.json`) → will yield a persistent **DOI** (F1, A2, F4)
2. Replace the placeholder ORCID in `CITATION.cff` / `.zenodo.json`
3. (Optional) map properties to a community ontology like EMMO (R1.3)