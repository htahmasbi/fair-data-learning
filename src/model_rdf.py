"""Model provenance as RDF triples (Stage 5: semantic MLOps).

MLflow, params.yaml and metrics.json answer questions like "which data
produced this model?" only for humans who read the files. Asserting the
same facts as triples makes them machine-queryable *together with* the
data they refer to:

    model   prov:wasGeneratedBy   run .
    run     mls:hasInput          dataset .      <- data lineage
    run     mls:hasOutput         evaluation .   <- measured performance
    run     mls:hasInput          setting .      <- hyperparameters as data
    model   prov:wasAttributedTo  orcid:...      <- accountability (FAIR F3)

Vocabularies are reused, never reinvented:
  - PROV-O (http://www.w3.org/ns/prov#)  - W3C provenance: who/when/what-from
  - ML-Schema (http://www.w3.org/ns/mls#) - W3C community ML: runs/evaluations

Run:
    python src/model_rdf.py
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import sklearn
import yaml
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Make `from src import ...` work when run as `python src/model_rdf.py`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_params
from src.vocab import (
    ALGORITHMS,
    DATASETS,
    HYPERPARAMETERS,
    IMPLEMENTATIONS,
    MEASURES,
    MLS,
    MODELS,
    MP_OXIDES_DATASET_ID,
    OWL,
    PROV,
    RUNS,
    SDO,
    TASKS,
    XSD,
)

METRICS_PATH = PROJECT_ROOT / "metrics.json"
CITATION_PATH = PROJECT_ROOT / "CITATION.cff"
MODEL_PATH = PROJECT_ROOT / "models" / "model.pkl"

# Estimator classes used by src/train.py. Tests assert this mapping matches
# train.MODEL_REGISTRY so the two modules cannot silently drift apart.
ESTIMATOR_CLASS = {
    "Ridge": "sklearn.linear_model.Ridge",
    "RandomForest": "sklearn.ensemble.RandomForestRegressor",
    "GradientBoost": "sklearn.ensemble.HistGradientBoostingRegressor",
}

MEASURE_LABELS = {
    "cv_r2_mean": "Cross-validated R2",
    "cv_r2_std": "Cross-validated R2 (standard deviation)",
    "cv_mae": "Cross-validated mean absolute error",
    "cv_rmse": "Cross-validated root mean squared error",
}


def file_md5(path: Path, chunk_size: int = 1 << 20) -> str:
    """Content hash of an artifact - the artifact's identity in the graph."""
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()


def read_metrics(path: Path = METRICS_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


def read_citation(path: Path = CITATION_PATH) -> dict:
    """Read author/publisher facts from CITATION.cff.

    Single source of truth (F1): ORCID, repository and license are asserted
    once in the citation file and reused for RDF + Zenodo metadata.
    """
    with open(path) as f:
        cff = yaml.safe_load(f)
    author = cff["authors"][0]
    orcid = str(author.get("orcid") or "")
    if orcid and not orcid.startswith("http"):
        orcid = f"https://orcid.org/{orcid}"
    return {
        "name": f'{author.get("given-names", "")} {author.get("family-names", "")}'.strip(),
        "orcid": orcid,
        "repository": cff.get("repository-code"),
        "license": cff.get("license"),
    }


def git_head_info(cwd: Path = PROJECT_ROOT) -> dict:
    """HEAD commit sha/time, used to version the model artifact.

    Returns Nones when git is unavailable (e.g. source tarball).
    """

    def _run(*args: str) -> str | None:
        try:
            proc = subprocess.run(
                ["git", *args], capture_output=True, text=True, timeout=10, cwd=cwd
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return proc.stdout.strip() if proc.returncode == 0 else None

    return {"sha": _run("rev-parse", "HEAD"), "committed_at": _run("log", "-1", "--format=%cI")}


def _digest(*parts) -> str:
    return hashlib.md5(
        json.dumps(parts, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _literal(value) -> Literal:
    if isinstance(value, bool):
        return Literal(value, datatype=XSD.boolean)
    if isinstance(value, int):
        return Literal(value, datatype=XSD.integer)
    if isinstance(value, float):
        return Literal(value, datatype=XSD.double)
    return Literal(value)


def _license_uri(license_id: str) -> Literal | URIRef:
    if "://" in license_id:
        return URIRef(license_id)
    # Map SPDX ids (e.g. "Apache-2.0") to a dereferenceable URL
    return URIRef(f"https://spdx.org/licenses/{license_id}.html")


def build_model_graph(
    metrics: dict,
    params: dict,
    model_path: Path = MODEL_PATH,
    citation: dict | None = None,
    git_info: dict | None = None,
) -> Graph:
    """Serialize the training history of model.pkl as PROV-O + ML-Schema triples."""
    citation = citation if citation is not None else read_citation()
    git_info = git_info if git_info is not None else git_head_info()
    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"{model_path} not found - train the model first (dvc repro / python src/train.py)"
        )

    g = Graph()
    for prefix, namespace in {
        "mls": MLS,
        "model": MODELS,
        "run": RUNS,
        "meas": MEASURES,
        "task": TASKS,
        "hparam": HYPERPARAMETERS,
        "algo": ALGORITHMS,
        "impl": IMPLEMENTATIONS,
        "prov": PROV,
        "sdo": SDO,
    }.items():
        g.bind(prefix, namespace)

    dataset_uri = DATASETS[MP_OXIDES_DATASET_ID]
    best_name = metrics["best_model"]
    model_uri = MODELS[f"band-gap-predictor-{file_md5(model_path)[:12]}"]

    agent_uri = URIRef(citation["orcid"]) if citation.get("orcid") else None
    if agent_uri:
        g.add((agent_uri, RDF.type, PROV.Agent))
        g.add((agent_uri, RDF.type, SDO.Person))
        g.add((agent_uri, RDFS.label, Literal(citation["name"])))
        g.add((agent_uri, SDO.identifier, Literal(citation["orcid"])))

    # Task: what every run was trying to achieve (MLS:Run realizes/achieves)
    task = TASKS["band-gap-regression"]
    g.add((task, RDF.type, MLS.Task))
    g.add((task, RDFS.label, Literal("Band gap regression for Materials Project oxides", lang="en")))
    g.add((task, MLS.definedOn, dataset_uri))

    # Implementation: the software that actually executed
    implementation = IMPLEMENTATIONS[f"scikit-learn-{sklearn.__version__}"]
    g.add((implementation, RDF.type, MLS.Implementation))
    g.add((implementation, RDFS.label, Literal(f"scikit-learn {sklearn.__version__}")))
    g.add((implementation, SDO.version, Literal(sklearn.__version__)))

    for name, cv_metrics in metrics["cv_metrics"].items():
        algorithm = ALGORITHMS[name]
        g.add((algorithm, RDF.type, MLS.Algorithm))
        g.add((algorithm, RDFS.label, Literal(name)))
        g.add((algorithm, RDFS.comment, Literal(ESTIMATOR_CLASS.get(name, name))))

        # Run identity derives from everything that defines the run, so it
        # changes exactly when hyperparameters or measured metrics change.
        hp_config = params["train"]["models"].get(name, {})
        run = RUNS[f"{name}-{_digest(name, hp_config, cv_metrics)[:10]}"]
        g.add((run, RDF.type, MLS.Run))
        g.add((run, RDF.type, PROV.Activity))
        g.add((run, SDO.name, Literal(f"{name} training run")))
        g.add((run, MLS.realizes, algorithm))
        g.add((run, MLS.executes, implementation))
        g.add((run, MLS.achieves, task))
        g.add((implementation, MLS.implements, algorithm))

        # Inputs: the dataset (shared URI with the material graph) and
        # hyperparameter settings, asserted as data rather than buried in code.
        g.add((run, MLS.hasInput, dataset_uri))
        g.add((run, PROV.used, dataset_uri))
        for hp_name, hp_value in hp_config.items():
            hp = HYPERPARAMETERS[hp_name]
            g.add((hp, RDF.type, MLS.HyperParameter))
            g.add((hp, RDFS.label, Literal(hp_name)))
            g.add((implementation, MLS.hasHyperParameter, hp))
            setting = BNode()
            g.add((setting, RDF.type, MLS.HyperParameterSetting))
            g.add((setting, MLS.specifiedBy, hp))
            g.add((setting, MLS.hasValue, _literal(hp_value)))
            g.add((run, MLS.hasInput, setting))
            g.add((run, PROV.used, setting))

        # Outputs: measurements of quality
        for metric_name, value in cv_metrics.items():
            measure = MEASURES[metric_name]
            g.add((measure, RDF.type, MLS.EvaluationMeasure))
            g.add((measure, RDFS.label, Literal(MEASURE_LABELS.get(metric_name, metric_name))))
            evaluation = BNode()
            g.add((evaluation, RDF.type, MLS.ModelEvaluation))
            g.add((evaluation, MLS.specifiedBy, measure))
            g.add((evaluation, MLS.hasValue, Literal(float(value), datatype=XSD.double)))
            g.add((run, MLS.hasOutput, evaluation))

        if name != best_name:
            continue

        # ---- assertions about the deployed artifact itself ----
        g.add((run, MLS.hasOutput, model_uri))
        g.add((model_uri, RDF.type, MLS.Model))
        g.add((model_uri, RDF.type, PROV.Entity))
        g.add((model_uri, SDO.name, Literal(f"Band gap predictor ({best_name})")))
        g.add((model_uri, SDO.description, Literal(
            f"scikit-learn {best_name} regressor predicting band gap (eV) "
            f"from composition and structure features"
        )))
        g.add((model_uri, PROV.wasGeneratedBy, run))
        # Content hash makes the URI a fingerprint of the exact artifact;
        # the git sha records which code version produced it.
        g.add((model_uri, OWL.versionInfo, Literal(git_info.get("sha") or "unknown")))

        if agent_uri:
            g.add((model_uri, PROV.wasAttributedTo, agent_uri))
            g.add((run, PROV.wasAssociatedWith, agent_uri))

        if citation.get("repository"):
            repo = citation["repository"]
            g.add((model_uri, SDO.codeRepository, URIRef(repo)))
            g.add((model_uri, SDO.citation, URIRef(f"{repo}/blob/main/CITATION.cff")))
            params_uri = URIRef(f"{repo}/blob/main/params.yaml")
            g.add((params_uri, RDF.type, PROV.Entity))
            g.add((params_uri, RDF.type, MLS.Data))
            g.add((params_uri, SDO.name, Literal("params.yaml")))
            g.add((run, PROV.used, params_uri))
            g.add((run, MLS.hasInput, params_uri))

        if citation.get("license"):
            g.add((model_uri, SDO.license, _license_uri(citation["license"])))

        committed_at = git_info.get("committed_at")
        if committed_at:
            stamp = Literal(committed_at, datatype=XSD.dateTime)
            g.add((model_uri, PROV.generatedAtTime, stamp))
            g.add((run, PROV.endedAtTime, stamp))

    return g


def main() -> None:
    metrics = read_metrics()
    graph = build_model_graph(metrics=metrics, params=load_params())
    print(f"Built model provenance graph with {len(graph)} triples")
    print(graph.serialize(format="turtle")[:2000])


if __name__ == "__main__":
    main()
