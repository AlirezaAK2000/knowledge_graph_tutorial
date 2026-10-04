"""Load one catalog graph and traverse its recorded relationships."""

from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS, URIRef

EX = Namespace("https://example.org/course-advisor#")
CATALOG_PATH = Path(__file__).parent / "data" / "course_catalog.ttl"

asserted_graph = Graph().parse(CATALOG_PATH, format="turtle")

# Identifiers select catalog individuals without counting ontology classes.
COURSES = sorted(asserted_graph.subjects(EX.courseId, None), key=str)
CATEGORIES = sorted(
    {EX.Course} | set(asserted_graph.subjects(RDFS.subClassOf, None)), key=str
)
TERMS = sorted(asserted_graph.subjects(RDF.type, EX.OfferingTerm), key=str)


def course_brief(course: URIRef) -> dict:
    """Return a JSON-friendly identifier and name from the asserted graph."""
    return {
        "id": str(asserted_graph.value(course, EX.courseId)),
        "name": str(asserted_graph.value(course, EX.name)),
    }


def label(resource: URIRef) -> str:
    return str(asserted_graph.value(resource, RDFS.label))


def category_key(category: URIRef) -> str:
    return str(category).removeprefix(str(EX))


def resolve_course(reference: str) -> URIRef | dict:
    """Accept a case-insensitive ID, exact name, or unambiguous name fragment."""
    reference = reference.strip().casefold()
    exact = [
        course for course in COURSES
        if reference in {value.casefold() for value in course_brief(course).values()}
    ]
    matches = exact or [
        course for course in COURSES
        if reference and reference in course_brief(course)["name"].casefold()
    ]
    if len(matches) == 1:
        return matches[0]
    return {
        "status": "ambiguous_course" if matches else "course_not_found",
        "candidates": [course_brief(course) for course in matches],
        "next_step": "Ask which candidate the user means, or use list_courses to discover IDs.",
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
    return sorted(label(term) for term in asserted_graph.objects(course, EX.offeredIn))


def direct_prerequisites(course: URIRef) -> list[URIRef]:
    return sorted(asserted_graph.objects(course, EX.hasDirectPrerequisite), key=str)


def course_categories(course: URIRef) -> set[URIRef]:
    """Follow each recorded category's subclass edges, including the category itself."""
    categories = set()
    for category in asserted_graph.objects(course, RDF.type):
        categories.update(asserted_graph.transitive_objects(category, RDFS.subClassOf))
    return categories


def prerequisite_facts(course: URIRef) -> dict:
    """Follow direct edges to find all requirements and their supporting chains."""
    direct = set(direct_prerequisites(course))
    all_required = set()

    # Collect the reachable direct edges once, even when chains share a course.
    pending = [course]
    visited = set()
    edges = []
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        for prerequisite in direct_prerequisites(current):
            all_required.add(prerequisite)
            edges.append({
                "course_id": course_brief(current)["id"],
                "relationship": "hasDirectPrerequisite",
                "prerequisite_id": course_brief(prerequisite)["id"],
            })
            pending.append(prerequisite)

    return {
        "course": course_brief(course),
        "direct": [course_brief(item) for item in sorted(direct, key=str)],
        "indirect": [course_brief(item) for item in sorted(all_required - direct, key=str)],
        "supporting_direct_relationships": sorted(
            edges, key=lambda edge: (edge["course_id"], edge["prerequisite_id"])
        ),
        "evidence": {
            "direct": "asserted hasDirectPrerequisite edges",
            "indirect": "graph traversal over recorded hasDirectPrerequisite edges",
        },
    }
