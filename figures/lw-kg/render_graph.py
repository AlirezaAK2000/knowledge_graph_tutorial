"""Render presentation subgraphs directly from the LW-KG Turtle catalog."""

import argparse
import json
from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as CurvePath
from rdflib import Graph, Namespace, RDF, RDFS

AIR = Namespace("http://example.org/airend#")
OUT = Path(__file__).resolve().parent
DEFAULT_SOURCE = Path.home() / "projects/LW-KG/src/manufacturing_rca/data/knowledge_graph.ttl"
C = {
    "text": "#17283F", "muted": "#526176", "blue": "#2263BB", "blue_fill": "#ECF3FF",
    "purple": "#7041B5", "purple_fill": "#F3EDFB", "amber": "#AC5708", "amber_fill": "#FFF3E0",
    "teal": "#087A70", "teal_fill": "#EAF7F4", "white": "#FFFFFF",
}
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "savefig.facecolor": "white"})


def text(ax, x, y, value, size=18, color="text", ha="left", weight="normal", **kwargs):
    return ax.text(x, y, value, fontsize=size, color=C[color], ha=ha,
                   va="center", weight=weight, zorder=5, **kwargs)


def canvas(title, subtitle, number):
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set(xlim=(0, 16), ylim=(0, 9))
    ax.set_axis_off()
    text(ax, .75, 8.65, "LW-KG  /  MANUFACTURING ROOT-CAUSE ANALYSIS", 14, "muted", weight="bold")
    text(ax, 15.25, 8.65, number, 14, "muted", ha="right")
    text(ax, .75, 8.03, title, 34, weight="bold")
    text(ax, .75, 7.42, subtitle, 17, "muted")
    return fig, ax


def local(node):
    return str(node).removeprefix(str(AIR))


def label(graph, node):
    value = graph.value(node, RDFS.label) or graph.value(node, AIR.paramName)
    return str(value) if value is not None else local(node)


def node(ax, graph, resource, x, y, width, height, color, wrap=26, size=20, foot=None):
    ax.add_patch(FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height,
        boxstyle="round,pad=0,rounding_size=0.16", facecolor=C[f"{color}_fill"],
        edgecolor=C[color], linewidth=1.5, zorder=3,
    ))
    kind = local(graph.value(resource, RDF.type))
    kind = "FAILURE MODE" if kind == "FailureMode" else kind.upper()
    name = label(graph, resource)
    if kind == "PARAMETER":
        name = name.replace("_", " ")
    text(ax, x, y + height / 2 - .28, kind, 14, color, ha="center", weight="bold")
    text(ax, x, y - .08 if foot is None else y + .03, fill(name.strip(), wrap),
         size, ha="center", weight="bold", linespacing=1.2)
    if foot:
        text(ax, x, y - height / 2 + .27, foot, 17, color, ha="center", weight="bold")


def arrow(ax, start, end, color, controls=None):
    path = CurvePath([start, *controls, end],
                     [CurvePath.MOVETO, CurvePath.CURVE4, CurvePath.CURVE4, CurvePath.CURVE4]) if controls else None
    ax.add_patch(FancyArrowPatch(
        posA=None if path else start, posB=None if path else end, path=path,
        arrowstyle="-|>", mutation_scale=23, linewidth=2.6, color=C[color],
        shrinkA=0, shrinkB=0, zorder=2,
    ))


def legend(ax, x, y, value, color):
    arrow(ax, (x, y), (x + .56, y), color)
    text(ax, x + .72, y, value, 16, "muted")


def edge_label(ax, x, y, value, color):
    text(ax, x, y, value, 16, color, ha="center",
         bbox={"facecolor": "white", "edgecolor": "none", "pad": 4})


def verify_edge(graph, triples, subject, predicate, obj):
    assert (subject, predicate, obj) in graph, (subject, predicate, obj)
    triples.append({
        "subject": local(subject), "predicate": local(predicate), "object": local(obj),
        "subject_label": label(graph, subject), "object_label": label(graph, obj),
    })


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=240)
    fig.savefig(OUT / f"{name}.svg")
    plt.close(fig)
    print(f"Created {name}.png (3840 × 2160) and {name}.svg")


def candidate_causes(graph):
    fig, ax = canvas(
        "From a QC symptom to candidate causes",
        "Low QC efficiency points to three possible failure modes and their recorded causes.", "01",
    )
    triples = []
    symptom = AIR.Symptom_QC_Eff_Low
    node(ax, graph, symptom, 2.65, 4.1, 3.8, 2.35, "blue", wrap=18, size=25)
    modes = [AIR.FM_TestSetupError, AIR.FM_InsufficientHardening, AIR.FM_RotorGeometryDeviation]
    rows = [6.05, 4.1, 2.15]
    for index, (mode, y) in enumerate(zip(modes, rows)):
        cause = next(graph.objects(mode, AIR.hasCause))
        verify_edge(graph, triples, symptom, AIR.suggestsFailureMode, mode)
        verify_edge(graph, triples, mode, AIR.hasCause, cause)
        node(ax, graph, mode, 7.75, y, 3.45, 1.7, "purple", wrap=19, size=20)
        node(ax, graph, cause, 12.95, y, 4.35, 1.7, "amber", wrap=23, size=20)
        start_y = 4.1 + (.52 if index == 0 else -.52 if index == 2 else 0)
        start, end = (4.55, start_y), (6.025, y)
        arrow(ax, start, end, "blue", controls=[(5.23, start_y), (5.30, y)])
        arrow(ax, (9.475, y), (10.775, y), "purple")
    legend(ax, .75, .96, "suggestsFailureMode · recorded", "blue")
    legend(ax, 8.3, .96, "hasCause · recorded", "purple")
    text(ax, .75, .37, "Graph-linked candidates, not confirmed diagnoses. Other symptoms, parameters, checks and SOP links omitted.", 14, "muted")
    save(fig, "01-qc-candidate-causes")
    return triples


def pressure_evidence(graph):
    fig, ax = canvas(
        "Ground the investigation in checks and rules",
        "QC pressure branch · the shared parameter connects a cause, check, action, and A12 limit.", "02",
    )
    triples = []
    cause = AIR.Cause_WrongQCPressure
    parameter = AIR.qc_ingoing_pressure
    action = AIR.Action_Adjust_QC_Pressure_Retest
    check = AIR.Check_Verify_QC_Pressure
    rule = AIR.Rule_QC_Pressure_A12
    minimum = str(graph.value(rule, AIR.minValue))
    maximum = str(graph.value(rule, AIR.maxValue))
    unit = str(graph.value(rule, AIR.ruleUnit))

    node(ax, graph, cause, 5.4, 6.0, 4.0, 1.95, "amber", wrap=22, size=22)
    node(ax, graph, parameter, 11.8, 6.0, 4.0, 1.95, "blue", wrap=17, size=24,
         foot=f"unit: {graph.value(parameter, AIR.paramUnit)}")
    node(ax, graph, action, 2.75, 2.75, 4.0, 2.15, "teal", wrap=23, size=20)
    node(ax, graph, check, 8.0, 2.75, 4.0, 2.15, "purple", wrap=22, size=20)
    node(ax, graph, rule, 13.25, 2.75, 4.0, 2.15, "amber", wrap=22, size=20,
         foot=f"{minimum}–{maximum} {unit}")

    verify_edge(graph, triples, cause, AIR.affectsParameter, parameter)
    arrow(ax, (7.4, 6.0), (9.8, 6.0), "amber")
    edge_label(ax, 8.6, 6.43, "affectsParameter", "amber")
    verify_edge(graph, triples, action, AIR.mitigatesCause, cause)
    arrow(ax, (2.75, 3.825), (4.95, 5.025), "teal")
    edge_label(ax, 3.0, 4.57, "mitigatesCause", "teal")
    verify_edge(graph, triples, check, AIR.measuresParameter, parameter)
    arrow(ax, (8.0, 3.825), (11.15, 5.025), "purple")
    edge_label(ax, 9.05, 4.37, "measuresParameter", "purple")
    verify_edge(graph, triples, rule, AIR.ruleAboutParameter, parameter)
    arrow(ax, (13.25, 3.825), (12.5, 5.025), "amber")
    edge_label(ax, 13.77, 4.53, "ruleAboutParameter", "amber")

    text(ax, 8.0, .96, "Trace the recommendation through explicit, inspectable relationships.",
         21, ha="center", weight="bold")
    text(ax, .75, .37, "All arrows are recorded RDF triples. The pressure range is an example rule stored in the project's Turtle file.", 14, "muted")
    save(fig, "02-qc-pressure-evidence")
    return {
        "edges": triples,
        "rule": {"id": local(rule), "minimum": minimum, "maximum": maximum, "unit": unit},
        "parameter": {"id": local(parameter), "unit": str(graph.value(parameter, AIR.paramUnit))},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    graph = Graph().parse(args.source, format="turtle")
    evidence = {
        "source": str(args.source.resolve()), "namespace": str(AIR),
        "interpretation": "Selected asserted subgraphs; graph traversal, no inferred diagnosis.",
        "candidate_causes": candidate_causes(graph), "pressure_evidence": pressure_evidence(graph),
    }
    (OUT / "graph-excerpt.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("All 10 displayed relationship triples verified against the Turtle source.")


if __name__ == "__main__":
    main()
