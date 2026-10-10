"""Load one catalog graph and traverse its recorded relationships."""

from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS, URIRef

EX = Namespace("https://example.org/course-advisor#")
CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "course_catalog.ttl"

graph = Graph().parse(CATALOG_PATH, format="turtle")


def course_brief(course: URIRef) -> dict:
    """Return a JSON-friendly identifier and name from the asserted graph."""
    return {
        "id": str(graph.value(course, EX.courseId)),
        "name": str(graph.value(course, EX.name)),
    }


def label(resource: URIRef) -> str:
    return str(graph.value(resource, RDFS.label))


def category_key(category: URIRef) -> str:
    return str(category).removeprefix(str(EX))


def resolve_course(reference: str) -> URIRef | dict:
    """Accept a case-insensitive ID, exact name, or unambiguous name fragment."""
    reference = reference.strip().casefold()
    # Find course nodes with a recorded course ID.
    course_nodes = graph.subjects(EX.courseId, None)
    exact = [
        course for course in course_nodes
        if reference in {value.casefold() for value in course_brief(course).values()}
    ]
    matches = exact
    if not matches:
        # Start a fresh iterator to search for partial name matches.
        course_nodes = graph.subjects(EX.courseId, None)
        matches = [
            course for course in course_nodes
            if reference and reference in course_brief(course)["name"].casefold()
        ]
    matches.sort(key=str)
    if len(matches) == 1:
        return matches[0]
    return {
        "status": "ambiguous_course" if matches else "course_not_found",
        "candidates": [course_brief(course) for course in matches],
    }


def resolve_filter(reference: str, resources: list[URIRef]) -> URIRef | None:
    """Resolve a category or term by its local name or human-readable label."""
    reference = reference.strip().casefold()
    return next(
        (resource for resource in resources
         if reference in {category_key(resource).casefold(), label(resource).casefold()}),
        None,
    )


def recorded_terms(course: URIRef) -> list[str]:
    # Get the offering terms linked to this course.
    term_nodes = graph.objects(course, EX.offeredIn)
    terms = [label(term) for term in term_nodes]
    return sorted(terms)


def direct_prerequisites(course: URIRef) -> list[URIRef]:
    # Get the courses this course directly requires.
    prerequisite_nodes = graph.objects(course, EX.hasPrerequisite)
    return sorted(prerequisite_nodes, key=str)


def course_categories(course: URIRef) -> set[URIRef]:
    """Follow each recorded category's subclass edges, including the category itself."""
    categories = set()
    # Get the categories explicitly assigned to this course.
    category_nodes = graph.objects(course, RDF.type)
    for category in category_nodes:
        # Follow subclass links, including this category and all its ancestors.
        parent_categories = graph.transitive_objects(category, RDFS.subClassOf)
        categories.update(parent_categories)
    return categories


def prerequisite_facts(course: URIRef) -> dict:
    """Follow direct edges to find all requirements and their supporting chains."""
    # Fetch the starting course's immediate requirements.
    prerequisite_nodes = direct_prerequisites(course)
    direct = set(prerequisite_nodes)

    # Follow prerequisite links to find every reachable course.
    reachable_courses = graph.transitive_objects(course, EX.hasPrerequisite)
    all_required = set(reachable_courses)
    # The traversal includes the starting course; it is not its own requirement.
    all_required.discard(course)

    # Collect the direct edges that explain the prerequisite chains.
    supporting_courses = sorted({course} | all_required, key=str)
    edges = []
    for current in supporting_courses:
        # Get the recorded requirements of each course in the subgraph.
        prerequisite_nodes = direct_prerequisites(current)
        for prerequisite in prerequisite_nodes:
            edges.append({
                "course_id": course_brief(current)["id"],
                "prerequisite_id": course_brief(prerequisite)["id"],
            })

    return {
        "course": course_brief(course),
        "direct": [course_brief(item) for item in sorted(direct, key=str)],
        "indirect": [course_brief(item) for item in sorted(all_required - direct, key=str)],
        "supporting_direct_relationships": sorted(
            edges, key=lambda edge: (edge["course_id"], edge["prerequisite_id"])
        ),
    }
