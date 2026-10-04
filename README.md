# Ontology-grounded course advisor

An educational chatbot for **fictional Cedar University**, with a catalog of
20 courses in programming, mathematics, AI, machine learning, and robotics.
Ask about course details, offering terms, and prerequisites through a Chainlit
chat interface.

The [catalog Turtle file](data/course_catalog.ttl) contains both the ontology
and the course instances. The ontology defines course categories, offering
terms, and properties such as names, credits, and prerequisites. The instances
provide each course's details and relationships using that vocabulary.

Categories form a subclass hierarchy: Computing includes Programming, Robotics,
and AI; AI includes Machine Learning, which includes Deep Learning. Offering
terms are Fall, Spring, and Summer.

![Course catalog ontology](img/ontology.jpg)

RDFLib loads this knowledge graph, and graph traversal finds indirect
prerequisites and parent categories. For example, Algorithms requires Data
Structures, which requires Object-Oriented Programming, which requires
Introduction to Programming. Following the category hierarchy also includes
Deep Learning when searching for AI courses.

Four tools expose this graph to the chatbot: list_courses finds courses by
category or offering term; get_course_details returns a course's description,
credits, terms, and direct prerequisites; get_prerequisites finds direct and
indirect requirements; and check_prerequisites compares those requirements with
your completed courses to identify what is satisfied or missing. You can refer
to courses by ID or name.

LangGraph connects the LLM to these tools. For each question, the model selects
the tools it needs, receives graph results, and explains them in the Chainlit
chat interface.

```mermaid
flowchart LR
    TTL[course_catalog.ttl] --> Catalog[RDFLib catalog graph]
    Catalog --> Tools[Graph tools]
    Chat[Chainlit chat] --> Assistant[LLM assistant]
    Assistant -->|tool calls| Tools
    Tools -->|results| Assistant
    Assistant -->|answer| Chat
```

## Setup and run

Use **Python 3.11 or newer**. Run these commands from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set your OpenAI API key and model in `.env`:

```dotenv
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4.1-mini
```

Choose a model your API account can access that supports tool calling through
the Responses API. Start the app:

```bash
chainlit run app.py
```

Open [localhost:8000](http://localhost:8000) to chat. Expand the tool steps to
inspect the queries and graph results behind each answer. Restart the app after
changing `.env`.

## Example questions

Try these questions in one chat:

1. “Tell me about Algorithms: its credits, offering terms, and direct prerequisites.”
2. “List the AI courses. Why is Deep Learning included?”
3. “What are the direct and indirect prerequisites for Algorithms? Explain the chain.”
4. “For Deep Learning, I have completed CS101, MA102, MA201, and ML201. Which prerequisites are satisfied and which are missing?”
   The missing requirements are MA101 (Calculus) and MA202 (Optimization).
5. “And if I also completed those two missing courses?”
6. “Is Autonomous Robotics offered in Spring?”
   Its offering terms are not recorded in the catalog, so availability is unknown.
