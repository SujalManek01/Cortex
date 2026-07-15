Sprint 004 — Advanced Command Planning
Chapter 1 — Introduction
1.1 Purpose

Sprint 004 evolves Cortex's deterministic planning engine from understanding single-intent commands to understanding complex command sequences while preserving the execution architecture introduced in previous sprints.

Sprint 003 introduced the Natural Language Planning Layer, allowing users to issue simple commands such as:

Open Chrome

or

Open GitHub

These commands are converted into deterministic ActionPlan objects before entering the Validation, Safety, and Execution pipeline.

Sprint 004 extends this capability by introducing grammatical understanding, intent grouping, verb scope resolution, and conflict analysis.

The result is a planner capable of understanding commands such as:

Open Chrome, GitHub and Downloads,
then close VS Code.

while maintaining deterministic behavior.

No probabilistic planning or large language model reasoning is introduced in this sprint.

1.2 Background

The Cortex architecture is intentionally layered.

Each sprint has introduced functionality without violating previously established boundaries.

Sprint 001

Introduced:

Execution Engine
Validator
Safety Policy
ActionPlan
ActionStep
Executor Framework
Sprint 002

Introduced:

Desktop automation
Application Registry
Folder Registry
Website Registry
Specialized Executors
Sprint 003

Introduced:

Tokenizer
Normalizer
Intent Detector
Target Resolver
Rule Planner
PlannerResult
Planning API
Plan Preview UI

Sprint 004 does not replace these systems.

Instead, it extends the Planning Layer by inserting additional deterministic processing stages before the Rule Planner.

1.3 Motivation

The Sprint 003 planner intentionally supports only one canonical intent per command.

Examples:

Supported:

Open Chrome

Supported:

Open Downloads

Rejected:

Open Chrome and close VS Code

Although deterministic, this limitation forces users to issue multiple independent commands for common workflows.

Sprint 004 removes this restriction while preserving predictability.

1.4 Design Philosophy

Sprint 004 follows five architectural principles.

Deterministic Planning

The same command shall always produce the same ActionPlan.

No randomness is permitted.

Immutable Execution

Planning becomes more sophisticated.

Execution remains unchanged.

Layer Separation

Every planning stage performs one responsibility.

Example:

Tokenizer

↓

Normalizer

↓

Grammar Parser

↓

Intent Grouper

↓

Scope Resolver

↓

Conflict Analyzer

↓

Target Resolver

↓

Rule Planner

No component performs responsibilities belonging to another stage.

Explainability

Every planner decision must be observable.

Users and developers shall be able to determine:

how tokens were interpreted
how intents were grouped
why warnings were generated
how targets were resolved

Planner behavior must remain explainable without requiring internal implementation knowledge.

Extensibility

Future planning implementations, including AI-powered planners, shall continue producing the same deterministic PlannerResult interface introduced in Sprint 003.

Chapter 2 — Goals and Scope
2.1 Primary Goals

Sprint 004 has six primary goals.

Goal 1

Support multiple targets.

Example:

Open Chrome,
GitHub
and Downloads.
Goal 2

Support multiple intents.

Example:

Open Chrome
then
close VS Code.
Goal 3

Introduce grammatical understanding.

The planner shall recognize:

connectors
separators
sequencing words
grouped targets
Goal 4

Produce richer diagnostics.

Planner output shall include:

grammar information
intent groups
conflict warnings
duplicate warnings
planning diagnostics
Goal 5

Maintain complete backward compatibility.

All Sprint 003 commands shall continue functioning without modification.

Goal 6

Preserve the existing execution architecture.

No changes shall be required to:

Execution Engine
Validator
Safety Policy
Executors
Capability Registry
2.2 Non-Goals

The following are explicitly outside the scope of Sprint 004.

Artificial Intelligence

No LLM integration.

No GPT.

No Claude.

No Gemini.

Conversational Context

Commands remain independent.

Example:

Open Chrome.

Open it again.

The second command remains unsupported.

Conversation memory is reserved for a future sprint.

Voice Recognition

Voice input is outside the scope of this sprint.

Browser Automation

Opening websites remains supported.

Interacting with browser content is not.

File Manipulation

Creating, deleting, moving, or renaming files remains outside Sprint 004.

Desktop Window Management

Window positioning, minimizing, maximizing, and focus switching are reserved for later releases.

Chapter 3 — Architecture Overview
3.1 Existing Planning Pipeline

Sprint 003 introduced the following pipeline.

Natural Language

↓

Tokenizer

↓

Normalizer

↓

Intent Detector

↓

Target Resolver

↓

Rule Planner

↓

PlannerResult

This architecture successfully handles simple commands.

3.2 Sprint 004 Pipeline

Sprint 004 expands the planning layer.

Natural Language

↓

Tokenizer

↓

Normalizer

↓

Grammar Parser

↓

Intent Grouper

↓

Verb Scope Resolver

↓

Conflict Analyzer

↓

Target Resolver

↓

Rule Planner

↓

PlannerResult

Each newly introduced stage performs one isolated responsibility.

3.3 Responsibilities
Tokenizer

Responsible for lexical analysis.

Produces ordered tokens.

Normalizer

Responsible for canonical token conversion.

Examples:

launch

↓

open
google chrome

↓

chrome
Grammar Parser

Responsible for understanding sentence structure.

Produces a Grammar Tree.

Intent Grouper

Creates groups of actions sharing a common intent.

Example:

Open Chrome
GitHub
Downloads

↓

One Intent Group.

Verb Scope Resolver

Determines which targets inherit which verbs.

Example:

Open Chrome,
GitHub
and Downloads

↓

Three OPEN actions.

Conflict Analyzer

Detects:

duplicate actions
contradictory actions
ambiguous groupings

Produces warnings only.

Execution continues unless validation later fails.

Target Resolver

Converts aliases into registered resources.

Rule Planner

Produces the immutable PlannerResult consumed by downstream systems.

## Chapter 4 — Grammar Engine

### 4.1 Overview

Sprint 004 introduces Cortex's first deterministic grammar engine.

Unlike the Sprint 003 planner, which directly interpreted normalized tokens, the Sprint 004 planner first constructs a grammatical representation of the user's command before any planning decisions are made.

The Grammar Engine is responsible only for understanding sentence structure.

It does **not**:

- resolve aliases,
- identify applications,
- create execution plans,
- perform validation,
- or execute actions.

Those responsibilities remain assigned to later pipeline stages.

---

### 4.2 Position in Pipeline

```text
Natural Language
        │
Tokenizer
        │
Normalizer
        │
Grammar Engine
        │
Intent Grouper
        │
Verb Scope Resolver
        │
Conflict Analyzer
        │
Target Resolver
        │
Rule Planner
```

The Grammar Engine always operates on normalized tokens.

---

### 4.3 Responsibilities

The Grammar Engine shall:

- classify tokens
- recognize sentence boundaries
- recognize connector words
- recognize sequencing words
- recognize grouped targets
- produce a deterministic Grammar Tree

The Grammar Engine shall never:

- resolve aliases
- query registries
- create ActionPlans
- detect installed applications
- perform safety checks

---

### 4.4 Input

Input consists of normalized tokens produced by the Normalizer.

Example

Input:

```text
open chrome and github then close vscode
```

Tokenizer Output:

```text
[
open,
chrome,
and,
github,
then,
close,
vscode
]
```

Normalizer Output:

```text
[
open,
chrome,
and,
github,
then,
close,
vscode
]
```

Grammar Engine receives the normalized list exactly as produced.

---

### 4.5 Output

The Grammar Engine produces a Grammar Tree.

Example

```text
Sentence
│
├── Clause
│      │
│      ├── Verb(open)
│      ├── Target(chrome)
│      ├── Connector(and)
│      └── Target(github)
│
└── Clause
       │
       ├── Sequence(then)
       ├── Verb(close)
       └── Target(vscode)
```

The Grammar Tree contains structure only.

No planning decisions have been made.

---

### 4.6 Deterministic Parsing

The Grammar Engine shall always produce identical Grammar Trees for identical normalized token streams.

No heuristics.

No probabilistic parsing.

No machine learning.

No ambiguity resolution.

Grammar parsing is entirely rule-driven.

---

## Chapter 5 — Grammar Tree

### 5.1 Purpose

The Grammar Tree is the canonical structural representation of a normalized command.

Every planning stage after the Grammar Engine operates on the Grammar Tree rather than raw tokens.

---

### 5.2 Design Goals

The Grammar Tree shall be:

- immutable
- deterministic
- serializable
- independent of execution
- independent of operating system
- independent of planner implementation

Future AI planners may also produce Grammar Trees provided they satisfy the same schema.

---

### 5.3 Structure

```text
GrammarTree
│
├── clauses[]
│
├── original_command
│
├── normalized_command
│
└── metadata
```

---

### 5.4 Clause

A Clause represents one grammatical action segment.

Example

```text
Open Chrome and GitHub
```

produces

```text
Clause

Verb

open

Targets

chrome

github
```

---

Example

```text
Close VS Code
```

produces

```text
Clause

Verb

close

Targets

vscode
```

---

### 5.5 Multiple Clauses

Example

```text
Open Chrome and GitHub then close VS Code.
```

Grammar Tree

```text
GrammarTree

Clause 1

Verb
open

Targets
chrome
github

Clause 2

Verb
close

Targets
vscode
```

---

### 5.6 Metadata

Grammar Trees store parsing metadata.

```text
GrammarTree

metadata

version

parser_version

grammar_version

token_count

clause_count
```

Metadata is informational only.

It does not influence planning.

---

### 5.7 Immutability

Once created, Grammar Trees shall never be modified.

Subsequent planner stages create new immutable structures rather than mutating existing ones.

This preserves deterministic debugging and simplifies testing.

---

## Chapter 6 — Token Classification

### 6.1 Purpose

Grammar parsing begins by classifying every normalized token.

Each token belongs to exactly one category.

---

### 6.2 Token Categories

Sprint 004 introduces the following categories.

| Category | Description |
|-----------|-------------|
| VERB | Canonical action words |
| TARGET | Potential application, folder, or website |
| CONNECTOR | Grouping words |
| SEQUENCE | Ordering words |
| UNKNOWN | Unrecognized tokens |

---

### 6.3 Verb Tokens

Examples

```text
open
```

```text
close
```

Future verbs introduced in later sprints shall continue using this category.

---

### 6.4 Target Tokens

Examples

```text
chrome
```

```text
downloads
```

```text
github
```

Target classification does not imply successful resolution.

Resolution occurs later.

---

### 6.5 Connector Tokens

Connectors group targets sharing a common verb.

Examples

```text
and
```

```text
&
```

```text
,
```

Example

```text
Open Chrome, GitHub and Downloads
```

contains three targets connected by grouping tokens.

---

### 6.6 Sequence Tokens

Sequence tokens separate execution order.

Examples

```text
then
```

```text
after
```

Example

```text
Open Chrome then Close VS Code
```

creates two independent clauses.

---

### 6.7 Unknown Tokens

Tokens that do not match any known category remain classified as UNKNOWN.

Example

```text
open chrome blablabla github
```

Token

```text
blablabla
```

↓

Classification

```text
UNKNOWN
```

Unknown tokens are preserved.

Later planner stages determine whether they produce warnings or planning failures.

---

### 6.8 Classification Rules

Classification follows the following priority:

```text
VERB

↓

SEQUENCE

↓

CONNECTOR

↓

TARGET

↓

UNKNOWN
```

Each token receives exactly one classification.

No token may belong to multiple categories simultaneously.

---

### 6.9 Configuration

Classification rules shall be driven by configuration files wherever practical.

Example

```text
config/

grammar.json
planner_aliases.json
```

Adding new connectors or sequencing words should require configuration updates rather than source-code modifications.

---

### 6.10 Performance Requirement

Token classification shall execute in linear time.

Target complexity:

```text
O(n)
```

where **n** equals the number of normalized tokens.

Implementations shall avoid nested scans of the token stream whenever possible.

## Chapter 7 — Intent Grouping

### 7.1 Overview

Following grammar parsing, Cortex groups related actions into deterministic **Intent Groups**.

An Intent Group represents one canonical verb and every target governed by that verb.

Intent Groups become the primary planning units consumed by downstream planner stages.

Grammar parsing identifies sentence structure.

Intent Grouping identifies semantic action groups.

---

### 7.2 Position in Pipeline

```text
Grammar Tree
        │
        ▼
Intent Grouper
        │
        ▼
Intent Groups
        │
Verb Scope Resolver
```

---

### 7.3 Responsibilities

The Intent Grouper shall:

- create deterministic action groups
- preserve command order
- preserve original grouping
- assign one canonical verb to each group
- preserve unresolved targets

The Intent Grouper shall never:

- resolve aliases
- validate targets
- detect conflicts
- access registries
- generate execution plans

---

### 7.4 Intent Group Model

Conceptually each Intent Group contains:

```text
IntentGroup

verb

targets[]

sequence_index

source_clause

metadata
```

---

### 7.5 Single Target Example

Input

```text
Open Chrome
```

Output

```text
Intent Group 1

Verb

open

Targets

chrome
```

---

### 7.6 Multiple Targets Example

Input

```text
Open Chrome, GitHub and Downloads
```

Output

```text
Intent Group 1

Verb

open

Targets

chrome

github

downloads
```

Only one group is created because all targets inherit the same verb.

---

### 7.7 Multiple Intent Example

Input

```text
Open Chrome and GitHub then Close VS Code
```

Output

```text
Intent Group 1

Verb

open

Targets

chrome

github

-------------------------

Intent Group 2

Verb

close

Targets

vscode
```

Execution order remains identical to user input.

---

### 7.8 Nested Connectors

Input

```text
Open Chrome, GitHub, Downloads and Documents
```

Output

```text
Intent Group

open

chrome

github

downloads

documents
```

The grouping logic treats commas and conjunctions as equivalent grouping connectors.

---

### 7.9 Ordering Guarantee

Intent Groups preserve user ordering.

Example

Input

```text
Open Chrome

then

Open GitHub

then

Close VS Code
```

Output

```text
Group 1

open chrome

↓

Group 2

open github

↓

Group 3

close vscode
```

Planner stages shall never reorder groups.

---

### 7.10 Empty Groups

Intent Groups containing no targets shall never be produced.

Example

```text
Open and then Close
```

The parser may recognize grammatical components, but the Intent Grouper shall reject empty action groups.

---

### 7.11 Performance Requirement

Intent grouping shall execute in

```text
O(n)
```

where **n** equals the number of Grammar Tree nodes.

---

# Chapter 8 — Verb Scope Resolution

## 8.1 Purpose

Natural language frequently omits repeated verbs.

Humans infer them automatically.

Sprint 004 introduces deterministic verb inheritance.

Example

```text
Open Chrome, GitHub and Downloads
```

contains one explicit verb.

The planner expands it into three independent actions.

---

### 8.2 Position in Pipeline

```text
Intent Groups
        │
        ▼
Verb Scope Resolver
        │
        ▼
Expanded Intent Groups
```

---

### 8.3 Responsibilities

The Verb Scope Resolver shall:

- propagate verbs across grouped targets
- preserve ordering
- preserve grouping
- detect incomplete clauses

The resolver shall never:

- validate aliases
- resolve applications
- execute actions

---

### 8.4 Simple Expansion

Input

```text
Open Chrome and GitHub
```

Expanded

```text
Open Chrome

Open GitHub
```

---

### 8.5 Folder Expansion

Input

```text
Open Downloads and Documents
```

Expanded

```text
Open Downloads

Open Documents
```

---

### 8.6 Website Expansion

Input

```text
Open GitHub and ChatGPT
```

Expanded

```text
Open GitHub

Open ChatGPT
```

Target type remains unknown until Target Resolution.

---

### 8.7 Mixed Resource Expansion

Input

```text
Open Chrome, Downloads and GitHub
```

Expanded

```text
Open Chrome

Open Downloads

Open GitHub
```

The Scope Resolver performs verb inheritance only.

Target categorization occurs later.

---

### 8.8 Multiple Verb Example

Input

```text
Open Chrome then Close VS Code then Open Downloads
```

Expanded

```text
Open Chrome

↓

Close VS Code

↓

Open Downloads
```

No verb crosses sequence boundaries.

---

### 8.9 Invalid Scope

Example

```text
Chrome and GitHub
```

No governing verb exists.

Planner shall produce a deterministic planning error.

---

### 8.10 Future Compatibility

Future verbs introduced in later sprints shall automatically participate in scope inheritance provided they are classified as canonical verbs.

No Scope Resolver modifications should be required.

---

# Chapter 9 — Target Resolution

## 9.1 Overview

Following verb inheritance, Cortex resolves every target into a concrete resource.

Resolution remains deterministic.

Only registered resources may be resolved.

---

### 9.2 Position in Pipeline

```text
Expanded Groups
        │
        ▼
Target Resolver
        │
        ▼
Resolved Targets
```

---

### 9.3 Responsibilities

The Target Resolver shall:

- resolve aliases
- query registries
- identify resource type
- preserve unresolved targets

The Target Resolver shall never:

- modify grammar
- modify grouping
- change execution order

---

### 9.4 Registry Lookup Order

Resolution follows a fixed order.

```text
Applications

↓

Folders

↓

Websites

↓

Unknown
```

The first successful match terminates resolution.

---

### 9.5 Application Example

Input

```text
chrome
```

↓

Resolved

```text
Application

chrome
```

---

### 9.6 Folder Example

Input

```text
downloads
```

↓

Resolved

```text
Folder

downloads
```

---

### 9.7 Website Example

Input

```text
github
```

↓

Resolved

```text
Website

github
```

---

### 9.8 Unknown Target

Input

```text
magicbrowser
```

↓

Resolved

```text
UNKNOWN
```

Planner shall later generate an appropriate planning error.

---

### 9.9 Alias Resolution

Aliases remain configuration-driven.

Example

```text
google chrome
```

↓

Alias

```text
chrome
```

↓

Registry

```text
Application
```

---

### 9.10 Deterministic Resolution

Registry lookup order shall never change during execution.

The same alias must always resolve to the same registered target.

---

### 9.11 Performance Requirement

Target resolution shall execute in

```text
O(n)
```

where **n** equals the number of expanded targets.

Registry implementations should utilize hash-based lookups whenever possible.

## Chapter 10 — Conflict Analysis

### 10.1 Overview

Sprint 004 introduces a dedicated Conflict Analyzer responsible for identifying logical inconsistencies within the generated planning model.

Conflict analysis improves planner transparency by detecting situations that may indicate unintended user input while preserving deterministic execution.

The Conflict Analyzer **never modifies the execution plan**.

Instead, it produces structured diagnostics that are returned to the frontend and API consumers.

---

### 10.2 Position in Pipeline

```text
Resolved Targets
        │
        ▼
Conflict Analyzer
        │
        ▼
Planner Diagnostics
        │
        ▼
Rule Planner
```

---

### 10.3 Responsibilities

The Conflict Analyzer shall:

- detect duplicate actions
- detect contradictory actions
- detect redundant operations
- assign warning severity
- preserve execution order

The Conflict Analyzer shall never:

- remove actions
- reorder actions
- resolve aliases
- modify targets
- prevent execution

---

### 10.4 Conflict Categories

Sprint 004 defines four conflict categories.

| Conflict | Description | Severity |
|------------|-------------|----------|
| Duplicate | Same action repeated | Warning |
| Contradictory | Opposite actions on same target | Warning |
| Redundant | Action produces no meaningful difference | Information |
| Ambiguous | Multiple possible interpretations | Planning Error |

---

### 10.5 Duplicate Actions

Example

```text
Open Chrome

Open Chrome
```

Produces

```text
Warning

Duplicate action detected

Target:
Chrome
```

Both actions remain in the ActionPlan.

---

### 10.6 Contradictory Actions

Example

```text
Open Chrome

Close Chrome
```

Produces

```text
Warning

Contradictory actions detected.

Target:
Chrome
```

Execution continues sequentially.

The planner never attempts to optimize or remove either action.

---

### 10.7 Redundant Actions

Example

```text
Open Downloads

Open Downloads

Open Downloads
```

Produces

```text
Information

Repeated identical operation.
```

No planning error is generated.

---

### 10.8 Ambiguous Commands

Example

```text
Open Chrome then it.
```

Because Sprint 004 has no conversational memory or pronoun resolution,

the planner cannot determine the meaning of

```text
it
```

Result

```text
Planning Error

AMBIGUOUS_REFERENCE
```

Planning terminates.

---

### 10.9 Conflict Ordering

Conflicts shall be reported in the same order they are detected.

Example

```text
Duplicate

↓

Contradiction

↓

Redundancy
```

This deterministic ordering simplifies automated testing.

---

### 10.10 Future Compatibility

Future planner stages may introduce additional conflict categories.

Existing categories shall remain backward compatible.

---

# Chapter 11 — Planner Diagnostics

## 11.1 Purpose

Planner Diagnostics provide complete visibility into Cortex's deterministic planning process.

Diagnostics exist for:

- developers
- testers
- frontend visualization
- debugging
- API consumers

Diagnostics never influence execution.

---

### 11.2 Diagnostic Model

Conceptually the planner produces

```text
Planner Diagnostics

Tokens

Normalized Tokens

Grammar Tree

Intent Groups

Expanded Actions

Resolved Targets

Warnings

Information

Planning Time
```

---

### 11.3 Token Diagnostics

Example

Input

```text
Open Chrome and GitHub
```

Diagnostics

```text
Tokens

open

chrome

and

github
```

---

### 11.4 Grammar Diagnostics

Example

```text
Grammar Tree

Clause 1

Verb

open

Targets

chrome

github
```

---

### 11.5 Intent Diagnostics

Example

```text
Intent Groups

Group 1

Verb

open

Targets

chrome

github
```

---

### 11.6 Resolution Diagnostics

Example

```text
chrome

↓

Application

github

↓

Website
```

---

### 11.7 Warning Diagnostics

Example

```text
Duplicate target

Chrome
```

---

Example

```text
Contradictory actions

Chrome
```

---

### 11.8 Information Diagnostics

Information messages explain planner behavior.

Example

```text
Expanded grouped targets.

Generated 3 actions.

Resolved alias:

google chrome

↓

chrome
```

These are informational only.

---

### 11.9 Planning Metrics

Diagnostics shall include

```text
Planning Time

Token Count

Clause Count

Intent Count

Resolved Targets

Warning Count
```

These values are intended for observability and performance monitoring.

---

### 11.10 Frontend Visibility

The frontend shall display:

- warnings
- planning duration
- resolved aliases
- grouped actions
- detected conflicts

Raw Grammar Trees remain optional for the user interface.

---

# Chapter 12 — API Changes

## 12.1 Overview

Sprint 004 extends the planning API without introducing breaking changes.

Existing Sprint 003 endpoints remain fully supported.

---

### 12.2 Existing Endpoints

The following endpoints remain unchanged.

```text
POST /plan

POST /command

POST /execute

GET /status

GET /health

GET /applications

GET /folders

GET /websites

GET /capabilities
```

---

### 12.3 Enhanced Plan Response

Sprint 004 extends the existing PlannerResult.

New optional fields include

```text
diagnostics

warnings

information

planning_metrics
```

Existing clients remain compatible.

---

### 12.4 Diagnostics Example

```json
{
  "diagnostics": {
    "planning_time_ms": 4,
    "token_count": 8,
    "intent_groups": 2,
    "resolved_targets": 3
  }
}
```

---

### 12.5 Warning Example

```json
{
  "warnings": [
    {
      "code": "DUPLICATE_ACTION",
      "message": "Duplicate action detected for target 'chrome'."
    }
  ]
}
```

---

### 12.6 Information Example

```json
{
  "information": [
    {
      "message": "Expanded grouped targets into three independent actions."
    }
  ]
}
```

---

### 12.7 Error Responses

Sprint 004 introduces additional deterministic planning errors.

Examples

```text
AMBIGUOUS_REFERENCE

EMPTY_GROUP

INVALID_SEQUENCE

UNKNOWN_CONNECTOR
```

Each error shall expose

- code
- message
- planner stage
- recoverability

---

### 12.8 Backward Compatibility

Clients written for Sprint 003 shall continue functioning without modification.

New fields are additive.

No existing response fields are removed.

---

### 12.9 Performance Requirement

Planning API response time target

```text
< 20 ms
```

for commands containing

- up to 10 actions
- up to 100 normalized tokens

on reference development hardware.

---

### 12.10 Design Principle

API consumers shall never depend upon internal parser implementation details.

Only stable PlannerResult contracts are considered public API.

## Chapter 13 — Frontend User Experience

### 13.1 Overview

Sprint 004 enhances the planning interface introduced in Sprint 003 by providing complete visibility into the planning pipeline before execution.

The frontend continues following the **Plan → Review → Execute** workflow.

No execution occurs until the user explicitly confirms the generated plan.

---

### 13.2 Planning Workflow

```text
User Command
        │
        ▼
POST /plan
        │
        ▼
PlannerResult
        │
        ▼
Plan Preview
        │
        ▼
User Review
        │
        ▼
Execute
        │
        ▼
POST /execute
        │
        ▼
Execution Progress
        │
        ▼
Execution Summary
```

---

### 13.3 Plan Preview

The Sprint 004 planner preview shall display:

- Original command
- Normalized command
- Intent groups
- Expanded actions
- Resolved targets
- Planning confidence
- Warnings
- Planning duration

The preview represents the exact execution plan.

No hidden planner decisions shall exist.

---

### 13.4 Intent Group Visualization

Example

```text
OPEN

• Chrome
• GitHub
• Downloads

------------------------

CLOSE

• VS Code
```

Intent Groups shall be visually separated.

---

### 13.5 Expanded Actions

The frontend shall display the fully expanded execution sequence.

Example

```text
1. Open Chrome

2. Open GitHub

3. Open Downloads

4. Close VS Code
```

Users should never have to infer planner behavior.

---

### 13.6 Warning Panel

Warnings shall appear separately from execution results.

Example

```text
⚠ Duplicate Action

Chrome appears multiple times.
```

---

Example

```text
⚠ Contradictory Actions

Chrome is opened and later closed.
```

Warnings shall never be displayed as execution failures.

---

### 13.7 Information Panel

Informational planner messages explain deterministic planner decisions.

Example

```text
Expanded grouped targets.

Resolved alias

google chrome

↓

chrome
```

Information messages are optional but recommended.

---

### 13.8 Confidence Display

Confidence remains deterministic.

Planner confidence is calculated from:

- successful parsing
- successful grouping
- successful resolution
- warning count
- ambiguity detection

Confidence values shall range from

```text
0%

↓

100%
```

---

### 13.9 Execute Confirmation

Execution remains a separate user action.

The Execute button shall remain disabled when:

- planning fails
- grammar errors occur
- ambiguous commands exist

Warnings alone shall not disable execution.

---

### 13.10 Design Principles

The user interface shall remain:

- deterministic
- transparent
- explainable
- minimal
- responsive

The frontend shall visualize planner behavior rather than hide it.

---

# Chapter 14 — Validation, Safety & Performance

## 14.1 Existing Architecture

Sprint 004 introduces **no modifications** to:

- Validator
- Safety Policy
- Execution Engine

Planning enhancements remain isolated from execution.

---

### 14.2 Validation Flow

```text
Planner

↓

PlannerResult

↓

Validator

↓

Safety Policy

↓

Execution Engine
```

Planning success does not imply execution approval.

Validation remains authoritative.

---

### 14.3 Planner Validation

Before producing an ActionPlan, the planner shall verify:

- grammar integrity
- clause completeness
- intent consistency
- verb scope integrity
- target presence

These checks occur before the Validator.

---

### 14.4 Execution Validation

Execution validation remains unchanged.

Existing validation rules continue applying to every ActionStep.

Examples

- capability exists
- target exists
- required parameters present

---

### 14.5 Safety Policy

Planner stages shall never bypass the Safety Policy.

Every generated ActionPlan shall continue passing through:

```text
Safety Policy

↓

Execution Engine
```

No planner component may execute operating system actions directly.

---

### 14.6 Performance Targets

Target planning performance.

| Metric | Target |
|----------|---------|
| Tokenization | < 2 ms |
| Grammar Parsing | < 5 ms |
| Intent Grouping | < 2 ms |
| Scope Resolution | < 2 ms |
| Conflict Analysis | < 2 ms |
| Target Resolution | < 5 ms |
| Total Planning | < 20 ms |

Reference hardware:

Modern desktop development workstation.

---

### 14.7 Complexity Targets

| Component | Complexity |
|------------|------------|
| Tokenizer | O(n) |
| Normalizer | O(n) |
| Grammar Parser | O(n) |
| Intent Grouper | O(n) |
| Scope Resolver | O(n) |
| Conflict Analyzer | O(n) |
| Target Resolver | O(n) |

No planner stage should exceed linear complexity.

---

### 14.8 Memory Targets

Planner memory usage shall remain proportional to the number of parsed tokens.

Target complexity

```text
O(n)
```

Intermediate representations should remain immutable.

---

### 14.9 Security Requirements

Planner components shall never:

- execute shell commands
- access the filesystem
- modify configuration
- communicate over the network
- invoke operating system APIs

The planner is a pure transformation pipeline.

---

### 14.10 Failure Isolation

Planning failures shall never corrupt:

- registries
- execution state
- configuration
- frontend state

Every planning request shall be independent.

---

# Chapter 15 — Engineering Standards

## 15.1 Coding Standards

All Sprint 004 planner components shall follow:

- single responsibility principle
- dependency injection
- immutable models
- deterministic outputs
- complete unit test coverage

---

### 15.2 Error Handling

Planner components shall never throw unhandled exceptions.

Failures shall be represented using structured planning errors.

Example

```text
PlanningError

↓

PlannerResult

↓

API Response
```

---

### 15.3 Logging

Planner logging shall remain structured.

Recommended fields:

```text
Planner Stage

Execution Time

Warnings

Planning Result

Correlation ID
```

Logs shall never contain stack traces for expected planning failures.

---

### 15.4 Test Coverage

Every planner module shall include:

- unit tests
- integration tests
- regression tests

Target project coverage after Sprint 004:

```text
500+

Automated Tests
```

---

### 15.5 Documentation

Every public planner class shall include:

- purpose
- responsibilities
- inputs
- outputs
- examples

All configuration schemas shall be documented.

---

### 15.6 Backward Compatibility

Sprint 004 shall preserve compatibility with:

- Sprint 001
- Sprint 002
- Sprint 002.1
- Sprint 003

Existing API consumers shall continue functioning without modification.

---

### 15.7 Configuration Standards

Planner behavior shall remain configuration-driven wherever practical.

Examples:

```text
grammar.json

planner_aliases.json

planner_rules.json
```

Hardcoded grammar rules should be avoided unless necessary for deterministic parsing.

---

### 15.8 Review Requirements

Sprint 004 implementation shall not be considered complete until:

- all milestones pass
- regression suite passes
- frontend builds successfully
- documentation updated
- walkthrough completed
- release summary written

---

### 15.9 Release Target

Sprint 004 produces

```text
Release

v0.4.0
```

---

### 15.10 Definition of Done

Sprint 004 shall be considered complete when:

- Grammar Engine implemented
- Intent Grouper implemented
- Scope Resolver implemented
- Conflict Analyzer implemented
- Planner Diagnostics implemented
- API updated
- Frontend updated
- All automated tests passing
- Walkthrough completed
- Release tagged as **v0.4.0**


## Chapter 16 — Testing Strategy

### 16.1 Overview

Sprint 004 introduces the largest expansion of Cortex's automated test suite since project inception.

Testing shall continue following the layered testing philosophy established in previous sprints.

Every planner stage shall be independently testable.

---

### 16.2 Testing Pyramid

```text
                Acceptance Tests
                      ▲
                      │
              Integration Tests
                      ▲
                      │
                 Unit Tests
```

The majority of planner tests shall remain unit tests.

---

### 16.3 Unit Testing

Each planner component shall include comprehensive unit tests.

Required coverage:

| Component | Minimum Tests |
|------------|--------------:|
| Tokenizer | 30 |
| Normalizer | 30 |
| Grammar Parser | 50 |
| Intent Grouper | 40 |
| Scope Resolver | 40 |
| Conflict Analyzer | 35 |
| Target Resolver | 35 |
| Rule Planner | 70 |

---

### 16.4 Integration Testing

Integration tests shall verify interaction between planner stages.

Required scenarios include:

- single command
- grouped targets
- mixed intents
- duplicate actions
- contradictory actions
- unknown targets
- planner diagnostics
- API responses

---

### 16.5 Acceptance Testing

Acceptance tests verify complete user workflows.

Example scenarios:

```text
Open Chrome

↓

Plan Generated

↓

User Reviews

↓

Execute

↓

Chrome Opens
```

---

### 16.6 Regression Testing

Every Sprint 003 command shall continue passing.

Examples:

```text
Open Chrome
```

```text
Open Downloads
```

```text
Close VS Code
```

Regression failures shall block release.

---

### 16.7 Performance Testing

Planner benchmarks shall verify:

- execution time
- memory usage
- parser scalability

Planning performance shall remain below target thresholds.

---

### 16.8 Test Naming Convention

Recommended naming convention:

```text
test_tokenizer.py

test_normalizer.py

test_grammar_parser.py

test_intent_grouper.py

test_scope_resolver.py

test_conflict_analyzer.py

test_rule_planner.py

test_api_plan.py
```

---

### 16.9 Continuous Verification

The complete test suite shall execute before every release.

Release candidates shall never be tagged while automated tests are failing.

---

### 16.10 Success Criteria

Expected project size after Sprint 004:

| Category | Estimated Tests |
|-----------|----------------:|
| Unit | 420+ |
| Integration | 60+ |
| Acceptance | 20+ |

Expected total:

```text
≈500 Automated Tests
```

---

# Chapter 17 — Future Compatibility

## 17.1 Purpose

Sprint 004 intentionally separates grammatical understanding from execution.

This enables future planners to reuse the existing execution pipeline without modification.

---

### 17.2 Future Planner Interface

Future planners may include:

```text
RulePlanner

ClaudePlanner

GeminiPlanner

LocalPlanner
```

Each planner shall produce the same PlannerResult contract.

---

### 17.3 Stable Interfaces

The following interfaces are considered stable.

```text
PlannerResult

ActionPlan

ActionStep

Execution Engine

Validator

Safety Policy
```

Future planners shall depend upon these contracts.

---

### 17.4 Future Features

Sprint 004 prepares Cortex for:

- conversational memory
- AI-assisted planning
- voice recognition
- browser automation
- desktop interaction
- filesystem automation

without requiring execution engine changes.

---

### 17.5 Architectural Principle

Future capabilities shall integrate through:

```text
Planner

↓

PlannerResult

↓

Execution
```

Direct execution from external systems is prohibited.

---

# Chapter 18 — Acceptance Criteria

## 18.1 Functional Requirements

Sprint 004 shall satisfy all of the following.

### Grammar Parsing

- Parse grouped commands.
- Parse sequencing connectors.
- Produce deterministic Grammar Trees.

---

### Intent Grouping

- Group related targets.
- Preserve ordering.
- Reject empty groups.

---

### Scope Resolution

- Expand inherited verbs.
- Preserve execution sequence.
- Detect missing governing verbs.

---

### Conflict Analysis

Detect:

- duplicate actions
- contradictory actions
- redundant operations
- ambiguous commands

---

### Planner Diagnostics

Provide:

- planning metrics
- warnings
- information
- grouped actions
- resolved aliases

---

### API

Maintain backward compatibility while exposing new planner metadata.

---

### Frontend

Display:

- grouped actions
- expanded execution plan
- warnings
- diagnostics
- confidence

---

## 18.2 Non-Functional Requirements

Sprint 004 shall:

- remain deterministic
- remain platform-independent at planning level
- remain fully testable
- preserve linear complexity
- preserve execution architecture

---

# Chapter 19 — Deliverables

Sprint 004 implementation shall include:

## Backend

- Grammar Parser
- Intent Grouper
- Scope Resolver
- Conflict Analyzer
- Planner Diagnostics
- Updated Rule Planner

---

## Configuration

New configuration files:

```text
config/

grammar.json

planner_rules.json
```

---

## Frontend

Updated components:

- Plan Preview
- Diagnostics Panel
- Warning Panel
- Planner Metrics
- Expanded Action View

---

## Documentation

Required documentation:

```text
SPR-004-Advanced-Command-Planning.md

walkthrough.md

release_summary.md

CHANGELOG.md
```

---

## Testing

Complete automated verification.

Expected:

```text
≈500 Passing Tests
```

---

# Chapter 20 — Release Summary

## Release Information

| Field | Value |
|--------|-------|
| Sprint | Sprint 004 |
| Release | v0.4.0 |
| Status | Planned |
| Implementation Strategy | Milestone-based |
| Planning Architecture | Deterministic |
| Backward Compatibility | Full |

---

## Major Features

Sprint 004 introduces:

- Grammar Engine
- Grammar Tree
- Intent Groups
- Verb Scope Resolution
- Conflict Analyzer
- Planner Diagnostics
- Enhanced Planning API
- Improved Planning UI

---

## Compatibility

Fully compatible with:

- Sprint 001
- Sprint 002
- Sprint 002.1
- Sprint 003

No breaking API changes.

---

## Implementation Milestones

| Milestone | Description |
|-----------|-------------|
| M1 | Grammar Models & Configuration |
| M2 | Grammar Parser |
| M3 | Intent Grouper |
| M4 | Scope Resolver |
| M5 | Conflict Analyzer |
| M6 | Rule Planner Integration |
| M7 | API Layer |
| M8 | Frontend Integration |
| M9 | Verification & Release |

---

## Definition of Success

Sprint 004 is complete when:

- All milestones are implemented.
- All automated tests pass.
- Existing functionality remains unchanged.
- Planning supports grouped and mixed-intent commands.
- Planner diagnostics are available through both the API and frontend.
- Documentation is updated.
- Release **v0.4.0** is tagged and published.

---

# Appendix A — Example Commands

| User Command | Expected Outcome |
|--------------|------------------|
| Open Chrome | Single application action |
| Open Chrome and GitHub | One intent, two targets |
| Open Chrome, GitHub and Downloads | One intent, three targets |
| Open Chrome then Close VS Code | Two sequential intent groups |
| Open Chrome then Open Downloads then Close Chrome | Three sequential actions |
| Open Chrome and Open Chrome | Duplicate warning |
| Open Chrome then Close Chrome | Contradictory warning |
| Chrome and GitHub | Planning error (missing verb) |
| Open magicbrowser | Unknown target error |

---

# Appendix B — Planner Pipeline

```text
Natural Language
        │
        ▼
Tokenizer
        │
        ▼
Normalizer
        │
        ▼
Grammar Parser
        │
        ▼
Intent Grouper
        │
        ▼
Verb Scope Resolver
        │
        ▼
Conflict Analyzer
        │
        ▼
Target Resolver
        │
        ▼
Rule Planner
        │
        ▼
PlannerResult
        │
        ▼
Validator
        │
        ▼
Safety Policy
        │
        ▼
Execution Engine
        │
        ▼
Operating System
```

---

# Appendix C — Architecture Principles

Sprint 004 follows these principles:

1. Deterministic planning.
2. Immutable intermediate models.
3. Layered architecture.
4. Explainable planner decisions.
5. Configuration-driven behavior.
6. Full backward compatibility.
7. Single responsibility per planner stage.
8. Execution engine independence.
