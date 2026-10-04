# LW-KG root-cause analysis diagrams

Presentation exports made from the actual graph at
`~/projects/LW-KG/src/manufacturing_rca/data/knowledge_graph.ttl`, namespace
`http://example.org/airend#`. Each PNG is 3840 × 2160 (16:9), with a white
background. SVGs contain editable shapes and text. The design matches the course
advisor figures: large typography, pastel node fills, and distinct relation colors.

## 1. QC symptom → candidate causes

`01-qc-candidate-causes` shows the recorded `Symptom_QC_Eff_Low` branch:

- Test setup error → Wrong QC ingoing pressure for variant.
- Insufficient hardening of coating → Oven control drift / cycle deviation.
- Rotor geometry deviation → Tool wear high.

The first edges are `suggestsFailureMode`; the second are `hasCause`.
Blue nodes are symptoms, purple nodes are failure modes, amber nodes are causes.
These are graph-linked candidate causes, not confirmed diagnoses. Names are
read from `rdfs:label`, including the symptom label's 99.99% threshold. The
application's efficiency trigger is implemented in Python; the figure does not
invent a QC efficiency `Rule` individual that is absent from the Turtle file.

## 2. Evidence for investigating QC pressure

`02-qc-pressure-evidence` follows the pressure branch through four actual edges:

```text
Cause_WrongQCPressure --affectsParameter--> qc_ingoing_pressure
Check_Verify_QC_Pressure --measuresParameter--> qc_ingoing_pressure
Action_Adjust_QC_Pressure_Retest --mitigatesCause--> Cause_WrongQCPressure
Rule_QC_Pressure_A12 --ruleAboutParameter--> qc_ingoing_pressure
```

The A12 example range **4.8–5.2 bar** comes directly from the rule's minimum,
maximum, and unit literals. Parameter display names replace underscores with
spaces. Cause, check, action, and rule labels come from the Turtle source.
The action points to the cause, and the check points to the parameter, preserving
the graph's original predicate directions.

Use the first figure to explain how a symptom leads to multiple candidates.
Use the second to explain how the shared parameter retrieves a relevant check
and range, while an action links directly to the candidate cause.

These are selected asserted subgraphs. There are no dashed inferred triples or
new causal claims. Other symptoms, affected parameters, procedures, steps, and
document links are omitted. All 10 displayed edge triples were checked against
the graph; `graph-excerpt.json` records their IDs, predicates, and source labels.

## Regenerate

From the ontology project root, activate its virtual environment with the
already-installed RDFLib and Matplotlib, then run:

```bash
python figures/lw-kg/render_graph.py
```

An alternative Turtle path can be supplied with `--source PATH`. The renderer
only parses the Turtle file and exports local figures; it makes no LLM calls.
Use DejaVu Sans in your vector editor for the original font appearance.
