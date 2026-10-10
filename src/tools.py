"""Four fixed graph tools; the LLM supplies arguments, never SPARQL."""

from langchain_core.tools import tool
from rdflib import Literal, RDF, RDFS

from .kg import (
    EX, graph,
    category_key, course_brief, course_categories, direct_prerequisites, label, prerequisite_facts,
    recorded_terms, resolve_course, resolve_filter,
)


@tool
def list_courses(category: str | None = None, term: str | None = None) -> dict:
    """Discover course IDs and names, optionally by category and recorded term.

    Category accepts a class key or label (e.g. AICourse, AI, Machine Learning).
    Parent categories include members found by subclass traversal. Term accepts Fall,
    Spring, or Summer. A term filter matches recorded offerings only; courses
    with unknown terms are excluded, without implying they are not offered.
    """
    # Find category classes that have a recorded parent class.
    category_nodes = graph.subjects(RDFS.subClassOf, None)
    categories = set(category_nodes)
    categories.add(EX.Course)
    categories = sorted(categories, key=str)

    # Find individuals declared as offering terms.
    term_nodes = graph.subjects(RDF.type, EX.OfferingTerm)
    terms = sorted(term_nodes, key=str)
    category_node = resolve_filter(category, categories) if category else None
    term_node = resolve_filter(term, terms) if term else None
    if (category and category_node is None) or (term and term_node is None):
        return {
            "status": "unknown_filter",
            "available_categories": [
                {"key": category_key(item), "label": label(item)} for item in categories
            ],
            "available_terms": [label(item) for item in terms],
        }

    courses = []
    # Fetch course nodes to apply the requested filters.
    course_nodes = graph.subjects(EX.courseId, None)
    for course in course_nodes:
        if category_node and category_node not in course_categories(course):
            continue
        if term_node and (course, EX.offeredIn, term_node) not in graph:
            continue
        item = course_brief(course)
        if category_node:
            item["category_match"] = {
                "category": category_key(category_node),
                "source": "asserted" if (course, RDF.type, category_node) in graph
                else "subclass_traversal",
            }
        courses.append(item)
    courses.sort(key=lambda item: item["id"])
    return {"courses": courses}


@tool
def get_course_details(course: str) -> dict:
    """Read asserted details using a course ID, name, or unique name fragment.

    Return credits, recorded categories and terms, and direct prerequisites.
    Ambiguous names return candidates for clarification. An empty offering-term
    list means availability is unknown, rather than the course is never offered.
    """
    node = resolve_course(course)
    if isinstance(node, dict):
        return node
    terms = recorded_terms(node)
    # Get the course's explicitly assigned categories.
    category_nodes = graph.objects(node, RDF.type)
    categories = [
        label(item) for item in category_nodes
        if item == EX.Course or (item, RDFS.subClassOf, None) in graph
    ]
    # Fetch direct prerequisites before formatting their IDs and names.
    prerequisite_nodes = direct_prerequisites(node)
    prerequisites = [course_brief(item) for item in prerequisite_nodes]
    return {
        **course_brief(node),
        "description": str(graph.value(node, EX.description)),
        "credits": int(graph.value(node, EX.credits)),
        "recorded_categories": sorted(categories),
        "recorded_offering_terms": terms,
        "direct_prerequisites": prerequisites,
    }


@tool
def get_prerequisites(course: str) -> dict:
    """Retrieve direct and indirect requirements by traversing recorded prerequisites.

    Include supporting direct edges so answers can explain prerequisite chains.
    Every prerequisite is mandatory in this simplified catalog.
    """
    node = resolve_course(course)
    return node if isinstance(node, dict) else prerequisite_facts(node)


@tool
def check_prerequisites(course: str, completed_course_ids: list[str]) -> dict:
    """Check all direct and indirect requirements against supplied completed IDs.

    Treat the supplied list as the complete completion record for this demo.
    An empty list means no courses completed. Completion of an advanced course
    does not automatically mark its prerequisites completed. This checks only
    prerequisite satisfaction, not enrollment eligibility or university policy.
    """
    node = resolve_course(course)
    if isinstance(node, dict):
        return node
    completed = {item.strip().upper() for item in completed_course_ids}
    unknown_ids = sorted(
        item for item in completed if (None, EX.courseId, Literal(item)) not in graph
    )
    if unknown_ids:
        return {"status": "unknown_completed_course_ids", "unknown_ids": unknown_ids}
    facts = prerequisite_facts(node)
    required = sorted(facts["direct"] + facts["indirect"], key=lambda item: item["id"])
    return {
        "course": facts["course"],
        "satisfied": [item for item in required if item["id"] in completed],
        "missing": [item for item in required if item["id"] not in completed],
        "all_prerequisites_satisfied": all(item["id"] in completed for item in required),
        "supporting_direct_relationships": facts["supporting_direct_relationships"],
    }


TOOLS = [list_courses, get_course_details, get_prerequisites, check_prerequisites]
