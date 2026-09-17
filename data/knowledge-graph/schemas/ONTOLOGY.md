# Canonical Knowledge Graph Ontology

## Purpose

This contract defines the semantic boundary between extracted source material and the canonical RDSO engineering knowledge graph. It is intentionally additive: existing datasets remain compatible while new records can progressively adopt stricter semantics.

## Entity families

### Information entities
`Document`, `DocumentFamily`, `Edition`, `Revision`, `Page`, `Section`, `Clause`, `Table`, `Figure`, `Note`, `Evidence`, `SourceFile`

### Engineering entities
`Drawing`, `Assembly`, `Component`, `Subcomponent`, `Sleeper`, `Fastener`, `Material`, `Geometry`, `Equipment`, `Tool`, `SparePart`, `BOMItem`

### Engineering-semantic entities
`Requirement`, `Specification`, `Measurement`, `Tolerance`, `Procedure`, `InspectionCriterion`, `AcceptanceCriterion`, `FailureMode`, `Defect`, `Hazard`, `Cause`, `Effect`, `Mitigation`

### Authority entities
`Organization`, `Directorate`, `Standard`, `Code`

## Identity rules

1. IDs are stable identifiers, not display labels.
2. Logical documents and physical source files are distinct entities.
3. Editions and revisions are distinct from the document family.
4. Pages belong to a specific source/document representation.
5. Evidence points to the exact document/page location that supports a fact.
6. Aliases are searchable labels and must not replace canonical IDs.

## Provenance rules

Every high-value engineering fact or relationship should be traceable to one or more `Evidence` records. Evidence should identify the document, page, clause/section when available, extraction method, confidence, and verification status. `source: null` is retained only for backward compatibility and should not be the target representation for new records.

## Relationship rules

Relationships use the controlled vocabulary in `vocabularies/relationship-types.json`. Relationship direction is meaningful. A relationship must reference existing canonical entity IDs. New relationship types require an explicit vocabulary update rather than ad-hoc strings.

## Quality gates

Before publication, the KG pipeline should validate:

- unique entity IDs;
- valid entity types;
- valid relationship types;
- no dangling `from` or `to` references;
- no duplicate logical document identities;
- valid evidence references;
- confidence values in `[0,1]`;
- valid verification states;
- normalized measurement units and bounds;
- revision chains without impossible cycles;
- requirement references to existing entities/evidence.

## Migration strategy

Do not rewrite the existing graph in one operation. First publish schemas and validation rules, then migrate high-value datasets incrementally. Existing fields remain readable during migration. New generated records should prefer `evidence_ids`, `confidence`, and `verification_status` over unstructured provenance strings.
