# Presentation graph figures

Three 16:9 diagrams extracted from `data/course_catalog.ttl` and checked against
its recorded triples and graph traversal results. Insert the PNGs into PowerPoint, Google
Slides, or Keynote. Each is 3840 × 2160 pixels with an opaque white background.
The SVGs provide editable vector shapes and text; install DejaVu Sans if your
editor needs an exact font match. At full slide size, graph labels use 18–25 pt
and titles use 34 pt in the original 16-inch-wide layout.

1. **01-asserted-prerequisites**: Algorithms → Data Structures → Object-Oriented
   Programming → Introduction to Programming. Solid blue edges show recorded
   `hasDirectPrerequisite` relationships. Credits and terms are catalog attributes.
2. **02-inferred-prerequisites**: The same layout, with two dashed amber
   shortcuts from Algorithms to its indirect requirements, found by following
   recorded prerequisite edges. The dashed edges illustrate traversal results;
   they are not added to the RDF graph. Amber-filled course
   nodes mark indirect requirements relative to Algorithms.
3. **03-subclass-inference**: ML301 is explicitly typed as DeepLearningCourse,
   a subclass of MachineLearningCourse, which is a subclass of AICourse.
   The dashed amber edge is the parent-category match found through traversal;
   there is no stored `ML301 rdf:type AICourse` triple.
   Blue nodes are course instances, purple nodes are ontology classes.

Use figures 1 and 2 consecutively to reveal indirect requirements without moving
the nodes. Follow with figure 3 to demonstrate traversal of a class hierarchy.
Prerequisite arrows point from the course to its requirement. Class arrows point
from the specific class to its parent. The figures intentionally show small
subgraphs, with other classes, courses, and traversal results omitted.

To regenerate after editing the catalog, activate the project virtual environment
and install the optional plotting dependency (not required by the chatbot):

```bash
python -m pip install matplotlib
python figures/render_graph.py
```

Rendering is local, makes no GPT API calls, and reads no `.env` credentials.
