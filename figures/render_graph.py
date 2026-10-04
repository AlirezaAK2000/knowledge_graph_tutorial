"""Export three 16:9 catalog diagrams. Requires matplotlib and project dependencies."""

from pathlib import Path
import sys
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as CurvePath

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kg import EX, asserted_graph, course_brief, course_categories, prerequisite_facts, recorded_terms
from rdflib import RDF, RDFS

OUT = Path(__file__).resolve().parent
COLORS = {
    "text": "#17283F", "muted": "#526176", "blue": "#2263BB",
    "blue_fill": "#ECF3FF", "amber": "#AC5708", "amber_fill": "#FFF3E0",
    "purple": "#7041B5", "purple_fill": "#F3EDFB", "teal": "#087A70",
    "border": "#C9D7E8", "white": "#FFFFFF",
}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "svg.fonttype": "none",
    "savefig.facecolor": "white", "axes.unicode_minus": False,
})


def canvas(title, subtitle, number):
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set(xlim=(0, 16), ylim=(0, 9))
    ax.set_axis_off()
    text(ax, .75, 8.65, "CEDAR UNIVERSITY  /  KNOWLEDGE GRAPH", 14, COLORS["muted"], weight="bold")
    text(ax, 15.25, 8.65, number, 14, COLORS["muted"], ha="right")
    text(ax, .75, 8.03, title, 34, weight="bold")
    text(ax, .75, 7.42, subtitle, 17, COLORS["muted"])
    return fig, ax


def text(ax, x, y, value, size=18, color=None, ha="left", weight="normal", **kwargs):
    return ax.text(x, y, value, fontsize=size, color=color or COLORS["text"],
                   ha=ha, va="center", weight=weight, zorder=5, **kwargs)


def box(ax, x, y, fill_color, border_color):
    ax.add_patch(FancyBboxPatch(
        (x - 1.45, y - 1.05), 2.9, 2.1,
        boxstyle="round,pad=0,rounding_size=0.16",
        facecolor=fill_color, edgecolor=border_color, linewidth=1.5, zorder=3,
    ))


def course_node(ax, course_id, x, y, indirect=False):
    course = EX[course_id]
    facts = course_brief(course)
    color = COLORS["amber"] if indirect else COLORS["blue"]
    background = COLORS["amber_fill"] if indirect else COLORS["blue_fill"]
    box(ax, x, y, background, color)
    text(ax, x, y + .64, facts["id"], 25, color, ha="center", weight="bold")
    text(ax, x, y + .04, fill(facts["name"], 20), 18, ha="center", linespacing=1.2)
    credits = int(asserted_graph.value(course, EX.credits))
    terms = ", ".join(recorded_terms(course)) or "term unknown"
    text(ax, x, y - .76, f"{credits} credits · {terms}", 15, COLORS["muted"], ha="center")


def class_node(ax, category, x, y):
    box(ax, x, y, COLORS["purple_fill"], COLORS["purple"])
    text(ax, x, y + .66, "CLASS", 14, COLORS["purple"], ha="center", weight="bold")
    name = str(asserted_graph.value(category, RDFS.label))
    text(ax, x, y + .06, fill(name, 14), 23, ha="center", weight="bold", linespacing=1.2)
    key = str(category).removeprefix(str(EX))
    text(ax, x, y - .76, key, 14, COLORS["muted"], ha="center")


def arrow(ax, start, end, color, dashed=False, controls=None):
    path = None
    if controls:
        path = CurvePath([start, *controls, end],
                         [CurvePath.MOVETO, CurvePath.CURVE4, CurvePath.CURVE4, CurvePath.CURVE4])
    ax.add_patch(FancyArrowPatch(
        posA=None if path else start, posB=None if path else end, path=path,
        arrowstyle="-|>", mutation_scale=23, linewidth=2.6,
        linestyle=(0, (6, 4)) if dashed else "solid", color=color,
        shrinkA=0, shrinkB=0, zorder=2,
    ))


def edge_label(ax, x, y, value, color):
    text(ax, x, y, value, 17, color, ha="center",
         bbox={"facecolor": "white", "edgecolor": "none", "pad": 5})


def legend(ax, x, y, value, color, dashed=False):
    arrow(ax, (x, y), (x + .56, y), color, dashed=dashed)
    text(ax, x + .72, y, value, 16, COLORS["muted"])


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=240)
    fig.savefig(OUT / f"{name}.svg")
    plt.close(fig)
    print(f"Created {name}.png (3840 × 2160) and {name}.svg")


def prerequisite_diagram(inference):
    title = "Traversal reveals indirect prerequisites" if inference else "The recorded prerequisite graph"
    subtitle = "Algorithms (CS202) · two indirect requirements found by graph traversal" if inference else (
        "Algorithms (CS202) · a focused view of the asserted catalog"
    )
    fig, ax = canvas(title, subtitle, "02" if inference else "01")
    courses = ["CS202", "CS201", "CS102", "CS101"]
    xs = [2.6, 6.2, 9.8, 13.4]
    y = 4.6
    for course_id, x in zip(courses, xs):
        course_node(ax, course_id, x, y, indirect=inference and course_id in {"CS102", "CS101"})
    for index in range(3):
        # Every displayed edge is verified against the actual graph.
        assert (EX[courses[index]], EX.hasDirectPrerequisite, EX[courses[index + 1]]) in asserted_graph
        arrow(ax, (xs[index] + 1.45, y), (xs[index + 1] - 1.45, y), COLORS["blue"])

    if inference:
        indirect_ids = {item["id"] for item in prerequisite_facts(EX.CS202)["indirect"]}
        for prerequisite in (EX.CS102, EX.CS101):
            assert course_brief(prerequisite)["id"] in indirect_ids
            assert (EX.CS202, EX.hasPrerequisite, prerequisite) not in asserted_graph
        arrow(ax, (xs[0], y + 1.06), (xs[2], y + 1.06), COLORS["amber"], True,
              controls=[(xs[0], 7.27), (xs[2], 7.27)])
        edge_label(ax, 6.2, 6.87, "indirect prerequisite  ·  traversal", COLORS["amber"])
        arrow(ax, (xs[0], y - 1.06), (xs[3], y - 1.06), COLORS["amber"], True,
              controls=[(xs[0], 1.64), (xs[3], 1.64)])
        edge_label(ax, 8, 2.11, "indirect prerequisite  ·  traversal", COLORS["amber"])
        legend(ax, .75, .97, "hasDirectPrerequisite · asserted", COLORS["blue"])
        legend(ax, 8.25, .97, "indirect requirement · traversal", COLORS["amber"], True)
        footer = "Arrow direction: course → requirement. Dashed shortcuts are traversal results; no new triples are stored."
    else:
        text(ax, 8, 2.52, "Three recorded edges. One prerequisite chain.", 23, ha="center", weight="bold")
        text(ax, 8, 1.95, "Names, credits, and terms are read directly from the catalog.", 18, COLORS["muted"], ha="center")
        legend(ax, .75, .97, "hasDirectPrerequisite · asserted", COLORS["blue"])
        footer = "Arrow direction: course → required course. All prerequisite edges on this slide are asserted."
    text(ax, .75, .37, footer, 14, COLORS["muted"])
    save(fig, "02-inferred-prerequisites" if inference else "01-asserted-prerequisites")


def subclass_diagram():
    fig, ax = canvas("Why Deep Learning is an AI course", "Following subclass edges finds the parent AI category", "03")
    xs = [2.6, 6.2, 9.8, 13.4]
    y = 4.6
    course_node(ax, "ML301", xs[0], y)
    classes = [EX.DeepLearningCourse, EX.MachineLearningCourse, EX.AICourse]
    for x, category in zip(xs[1:], classes):
        class_node(ax, category, x, y)
    assert (EX.ML301, RDF.type, classes[0]) in asserted_graph
    arrow(ax, (xs[0] + 1.45, y), (xs[1] - 1.45, y), COLORS["teal"])
    for index in range(2):
        assert (classes[index], RDFS.subClassOf, classes[index + 1]) in asserted_graph
        arrow(ax, (xs[index + 1] + 1.45, y), (xs[index + 2] - 1.45, y), COLORS["purple"])
    assert EX.AICourse in course_categories(EX.ML301)
    assert (EX.ML301, RDF.type, EX.AICourse) not in asserted_graph
    arrow(ax, (xs[0], y + 1.06), (xs[3], y + 1.06), COLORS["amber"], True,
          controls=[(xs[0], 7.27), (xs[3], 7.27)])
    edge_label(ax, 8, 6.87, "category membership  ·  traversal", COLORS["amber"])
    text(ax, 8, 2.49, "ML301 is retrieved when a student asks for AI courses.", 23, ha="center", weight="bold")
    text(ax, 8, 1.93, "Class membership and prerequisite relationships are separate facts.", 18, COLORS["muted"], ha="center")
    legend(ax, .75, .97, "rdf:type · asserted", COLORS["teal"])
    legend(ax, 5.25, .97, "rdfs:subClassOf · asserted", COLORS["purple"])
    legend(ax, 11.15, .97, "category · traversal", COLORS["amber"], True)
    text(ax, .75, .37, "Course instances appear in blue; classes in purple. Dashed category matches are derived without adding triples.", 14, COLORS["muted"])
    save(fig, "03-subclass-inference")


if __name__ == "__main__":
    prerequisite_diagram(inference=False)
    prerequisite_diagram(inference=True)
    subclass_diagram()
