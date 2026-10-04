"""Four fixed graph tools; the LLM supplies arguments, never SPARQL."""

from langchain_core.tools import tool
from rdflib import RDF

from kg import (
    CATEGORIES, COURSES, TERMS, EX, asserted_graph,
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
    category_node = resolve_filter(category, CATEGORIES) if category else None
    term_node = resolve_filter(term, TERMS) if term else None
    options = {
        "available_categories": [
            {"key": category_key(item), "label": label(item)} for item in CATEGORIES
        ],
        "available_terms": [label(item) for item in TERMS],
    }
    if (category and category_node is None) or (term and term_node is None):
        return {"status": "unknown_filter", **options}

    courses = []
    for course in COURSES:
        if category_node and category_node not in course_categories(course):
            continue
        if term_node and (course, EX.offeredIn, term_node) not in asserted_graph:
            continue
        item = course_brief(course)
        if category_node:
            item["category_match"] = {
                "category": category_key(category_node),
                "source": "asserted" if (course, RDF.type, category_node) in asserted_graph
                else "subclass_traversal",
            }
        courses.append(item)
    return {
        "courses": courses,
        **options,
        "offering_note": "Only recorded terms are matched; missing terms mean unknown.",
    }


@tool
def get_course_details(course: str) -> dict:
    """Read asserted details using a course ID, name, or unique name fragment.

    Return credits, recorded categories and terms, and direct prerequisites.
    Ambiguous names return candidates for clarification. Missing offering terms
    are explicitly unknown, rather than evidence the course is never offered.
    """
    node = resolve_course(course)
    if isinstance(node, dict):
        return node
    terms = recorded_terms(node)
    return {
        **course_brief(node),
        "description": str(asserted_graph.value(node, EX.description)),
        "credits": int(asserted_graph.value(node, EX.credits)),
        "recorded_categories": sorted(
            label(item) for item in asserted_graph.objects(node, RDF.type)
            if item in CATEGORIES
        ),
        "recorded_offering_terms": terms,
        "offering_information": "recorded" if terms else "unknown (not recorded)",
        "direct_prerequisites": [course_brief(item) for item in direct_prerequisites(node)],
        "evidence": "asserted catalog facts; an empty prerequisite list means none recorded",
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
    known_ids = {course_brief(item)["id"] for item in COURSES}
    if completed - known_ids:
        return {"status": "unknown_completed_course_ids", "unknown_ids": sorted(completed - known_ids)}
    facts = prerequisite_facts(node)
    required = sorted(facts["direct"] + facts["indirect"], key=lambda item: item["id"])
    return {
        "course": facts["course"],
        "completed_course_ids": sorted(completed),
        "assumption": "The supplied completed-course list is the complete record for this demonstration.",
        "satisfied": [item for item in required if item["id"] in completed],
        "missing": [item for item in required if item["id"] not in completed],
        "all_prerequisites_satisfied": all(item["id"] in completed for item in required),
        "scope": "Prerequisite satisfaction only; not a complete enrollment decision.",
        "supporting_direct_relationships": facts["supporting_direct_relationships"],
    }


TOOLS = [list_courses, get_course_details, get_prerequisites, check_prerequisites]
