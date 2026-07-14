# Sprint 003 — Natural Language Planning

**Document ID:** SPR-003  
**Version:** 1.0  
**Status:** Draft (Pending Engineering Review)  
**Project:** Cortex  
**Sprint:** 003  
**Author:** Cortex Architecture Team  
**Created:** July 2026  
**Last Updated:** July 2026

---

## Prerequisites

- Sprint 001 — Core Execution Engine
- Sprint 002 — Desktop Automation
- Sprint 002.1 — Configuration Hotfix

---

## Summary

Sprint 003 introduces Cortex's deterministic Natural Language Planning Engine. It enables users to issue plain English commands that are transformed into validated ActionPlans while preserving the existing Execution Engine, Validator, Safety Policy, and Capability architecture. The planner is intentionally rule-based, providing deterministic behavior, explainability, and a stable abstraction layer for future AI-powered planners.


SPR-003 — Natural Language Planning Engine

Version: 1.0

Sprint: 003

Status: Draft

Author: Cortex Architecture Team

Prerequisites:

Sprint 001 – Core Execution Engine
Sprint 002 – Desktop Automation
Sprint 002.1 – Configuration Hotfix
Chapter 1 — Vision & Objectives
1.1 Overview

Sprint 001 established Cortex as a deterministic execution engine capable of executing validated action plans.

Sprint 002 extended the execution engine with desktop automation capabilities by introducing application, folder, and website registries together with corresponding executors.

Although these sprints created a robust automation platform, Cortex still requires users or external systems to manually construct structured JSON ActionPlans.

Example:

{
  "plan": {
    "steps": [
      {
        "capability": "application.open",
        "target": "chrome"
      }
    ]
  }
}

While technically correct, this interface is unsuitable for a desktop assistant.

Users naturally think in language, not JSON.

Sprint 003 bridges this gap by introducing a deterministic Natural Language Planning Engine capable of translating user commands into validated ActionPlans without changing the Execution Engine.

1.2 Vision

The long-term vision of Cortex is to become an extensible desktop assistant capable of accepting multiple forms of input while preserving deterministic execution.

Future input methods may include:

Natural language
Voice recognition
AI planners
Local LLMs
Remote LLM providers
Workflow automation
Scheduled tasks

Regardless of the input source, every request must ultimately produce the same internal representation:

ActionPlan

The Execution Engine must remain completely independent from the planning strategy.

1.3 Primary Goal

Transform Cortex from:

User
    ↓
Manual JSON
    ↓
Execution Engine

into:

User
    ↓
Natural Language
    ↓
Planning Engine
    ↓
ActionPlan
    ↓
Execution Engine

without modifying the Execution Engine architecture.

1.4 Non-Goals

Sprint 003 intentionally excludes the following features:

AI Integration

No OpenAI

No Claude

No Gemini

No Local LLM

No cloud inference

Memory

No conversation history

No long-term memory

No context persistence

Browser Automation

No clicking

No typing

No DOM interaction

No Playwright

No Selenium

Vision

No OCR

No screenshots

No image understanding

Voice

No microphone

No speech recognition

No text-to-speech

These capabilities are intentionally deferred to later sprints.

1.5 Design Philosophy

Sprint 003 follows five engineering principles.

Deterministic

The same input always produces the same ActionPlan.

Explainable

Every planning decision must be traceable.

The planner must never behave like a black box.

Testable

Every planning stage must be independently testable.

Tokenizer

Normalizer

Intent Detection

Target Resolution

Planner

Replaceable

The planner must be replaceable without modifying downstream components.

Safe

Natural language must never bypass:

Validator
Safety Policy
Capability Registry

Every generated ActionPlan must pass through the same validation pipeline as manually created plans.

Chapter 2 — Existing Architecture Review

Sprint 003 builds upon the architecture introduced in previous sprints.

No existing subsystem will be replaced.

Instead, a new Planning Layer will be inserted before the Validator.

2.1 Current Architecture
                JSON ActionPlan
                      │
                      ▼
             Plan Validator
                      │
                      ▼
             Safety Policy
                      │
                      ▼
           Execution Engine
                      │
                      ▼
          Capability Registry
                      │
                      ▼
               Executors
                      │
                      ▼
              Operating System

This architecture has already been validated through Sprint 001 and Sprint 002.

Sprint 003 preserves every downstream component.

2.2 Architectural Strengths

Current architecture already provides:

Separation of Responsibilities

Validator validates.

Safety Policy authorizes.

Execution Engine executes.

Executors interact with Windows.

No component performs multiple unrelated responsibilities.

Deterministic Execution

Execution always follows:

Plan

↓

Validation

↓

Safety

↓

Execution

No shortcuts exist.

Capability-Based Design

The Execution Engine does not know how applications are opened.

It simply invokes a registered capability.

Example:

application.open

may internally launch VS Code,

while

website.open

may open GitHub in the default browser.

Registry-Based Resolution

Applications

Folders

Websites

are already resolved through registries rather than hardcoded paths.

This architecture naturally supports Natural Language Planning.

2.3 Existing Limitations

Despite its strengths, Cortex still has several usability limitations.

Manual JSON

Users must construct ActionPlans manually.

This is error-prone.

No Intent Understanding

Cortex cannot understand:

Open Chrome

It only understands structured plans.

No Alias Resolution

Users naturally type:

VS Code

instead of

vscode

Natural language normalization is currently absent.

No Planning Preview

Users cannot inspect generated plans before execution.

No Confidence Information

Current execution assumes ActionPlans are already correct.

There is no mechanism to indicate planning certainty.

2.4 Why Not Modify the Execution Engine?

A common architectural mistake is allowing natural language parsing to leak into execution.

Sprint 003 explicitly avoids this.

The Execution Engine must remain unaware of:

English grammar
Synonyms
Intent detection
Parsing
Tokenization

Its only responsibility is executing validated ActionPlans.

This separation ensures future AI planners can replace the deterministic Rule Planner without changing the execution pipeline.

Chapter 3 — Target Architecture

Sprint 003 introduces a dedicated Planning Layer.

3.1 High-Level Pipeline
User
        │
        ▼
Natural Language
        │
        ▼
Tokenizer
        │
        ▼
Normalizer
        │
        ▼
Intent Detector
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
Plan Validator
        │
        ▼
Safety Policy
        │
        ▼
Execution Engine
        │
        ▼
Capability Registry
        │
        ▼
Executors
        │
        ▼
Operating System
3.2 Responsibilities
Tokenizer

Breaks raw text into normalized tokens.

Example:

Open Chrome and GitHub

↓

["open","chrome","and","github"]
Normalizer

Standardizes spelling, whitespace, separators, and aliases.

Example:

VS Code

↓

vscode
Intent Detector

Determines user intention.

Examples:

open

close

launch

start

run

↓

Canonical Intent

Target Resolver

Maps normalized targets to registered resources.

Applications

Folders

Websites

Unknown targets produce deterministic planning errors.

Rule Planner

Builds ActionPlans.

No execution occurs.

PlannerResult

Returns:

ActionPlan
Confidence
Warnings
Planning Time
Normalized Input
3.3 Architectural Principle

The Execution Engine must never know whether an ActionPlan originated from:

JSON
Rule Planner
Future AI Planner
Voice Input
Workflow Engine

Every source produces the same ActionPlan model.

3.4 Future Compatibility

This architecture intentionally prepares Cortex for future AI planners.

Example:

RulePlanner

↓

Planner Interface

↓

Execution Pipeline

Future:

ClaudePlanner

GeminiPlanner

GPTPlanner

LocalPlanner

All planners implement the same interface and produce identical PlannerResult objects.

The Execution Engine remains completely unchanged.

Chapter 4 — Functional Requirements
4.1 Overview

The Natural Language Planning Engine shall convert supported English commands into deterministic ActionPlan objects without ambiguity. The planner is not a conversational AI. It interprets commands using a finite, well-defined grammar.

The planner shall reject unsupported or ambiguous commands rather than attempting to guess user intent.

4.2 Functional Requirements
FR-001 — Accept Natural Language

The planner shall accept a plain-text command.

Example:

Open Chrome
FR-002 — Produce ActionPlan

The planner shall generate a valid ActionPlan conforming to the existing Sprint 001 schema.

Example:

Open Chrome

↓

application.open(chrome)
FR-003 — Multiple Actions

The planner shall support multiple sequential actions within a single command.

Example:

Open Chrome and VS Code

↓

Step 1
application.open(chrome)

Step 2
application.open(vscode)
FR-004 — Sequential Order

Actions shall execute in the exact order provided by the user.

Input:

Open VS Code then Chrome

Execution:

1. VS Code

2. Chrome

Never reordered.

FR-005 — Registry Resolution

Targets must resolve only through:

Application Registry
Folder Registry
Website Registry

No raw executable paths.

No raw URLs.

FR-006 — Validation

Every generated ActionPlan must pass through:

Plan Validator
Safety Policy

before execution.

FR-007 — Preview

The planner shall support preview mode.

Planning:

User

↓

Planner

↓

PlannerResult

Execution is optional.

FR-008 — Determinism

The same input shall always produce the same ActionPlan.

Example:

Open Chrome

always generates

application.open(chrome)
FR-009 — Explainability

Every planning result shall expose:

normalized input
resolved targets
warnings
confidence
FR-010 — Backward Compatibility

Existing JSON execution must continue functioning unchanged.

Current API:

POST /execute

remains fully supported.

Chapter 5 — Natural Language Grammar
5.1 Scope

Sprint 003 supports a restricted command grammar.

This is intentional.

The planner recognizes commands.

It does not understand arbitrary English.

5.2 Supported Verbs

Canonical intents:

User Input	Intent
open	open
launch	open
start	open
run	open
close	close
exit	close
quit	close

Example:

Launch Chrome

↓

open
5.3 Supported Connectors

Multiple actions may be separated by:

and

then

,

&

All connectors normalize internally.

Example:

Open Chrome & VS Code

↓

Open Chrome then VS Code
5.4 Supported Target Types

The planner recognizes three resource types.

Applications

Examples

chrome

vscode

spotify

notepad
Websites

Examples

github

chatgpt

youtube

gmail
Folders

Examples

downloads

desktop

documents

cortex
5.5 Supported Sentence Patterns
Pattern A
Verb Target

Example

Open Chrome
Pattern B
Verb Target and Target

Example

Open Chrome and VS Code
Pattern C
Verb Target then Target

Example

Open Chrome then GitHub
Pattern D
Close Target

Example

Close Chrome
Pattern E
Verb Target, Target and Target

Example

Open Chrome, VS Code and Downloads
5.6 Unsupported Commands

The following are intentionally unsupported.

Open Chrome if it's installed

Maybe open GitHub

Can you please launch VS Code?

Open Chrome after five minutes

Open everything

Planner returns

PlanningError
5.7 Ambiguous Commands

Example

Open Office

Possible matches

Microsoft Office

LibreOffice

Planner returns

AMBIGUOUS_TARGET

Never guesses.

5.8 Unknown Commands

Example

Destroy Windows

↓

UNKNOWN_INTENT

Example

Open ABCXYZ123

↓

UNKNOWN_TARGET
5.9 Alias Resolution

Aliases normalize before lookup.

Examples

Input	Normalized
vs code	vscode
visual studio code	vscode
google chrome	chrome
chat gpt	chatgpt

Normalization occurs before registry lookup.

Chapter 6 — Tokenizer Specification
6.1 Responsibility

The Tokenizer converts raw user text into lexical tokens.

It performs no interpretation.

Example

Open Chrome and GitHub

↓

["open",
 "chrome",
 "and",
 "github"]
6.2 Responsibilities

The Tokenizer SHALL:

split words
preserve ordering
identify separators
remove redundant whitespace
normalize Unicode whitespace

The Tokenizer SHALL NOT:

detect intent
resolve aliases
access registries
create ActionPlans
6.3 Token Types
WORD
chrome
CONNECTOR
and

then

,

&
UNKNOWN

Unrecognized symbols.

Example

@
#
$
6.4 Processing Pipeline
Raw Input

↓

Trim

↓

Collapse whitespace

↓

Split

↓

Classify

↓

Tokens
6.5 Examples

Example 1

Input

Open Chrome

↓

Tokens

WORD(open)

WORD(chrome)

Example 2

Input

Open Chrome, VS Code

↓

Tokens

WORD(open)

WORD(chrome)

CONNECTOR(,)

WORD(vs)

WORD(code)

Example 3

Input

Open Chrome & GitHub

↓

Tokens

WORD(open)

WORD(chrome)

CONNECTOR(&)

WORD(github)
6.6 Error Handling

Tokenizer errors are extremely rare.

Invalid UTF-8 or malformed input shall return

TOKENIZATION_ERROR

No partial token stream shall be produced.

6.7 Performance Target

The tokenizer should process commands under 2 ms on a typical desktop system.

Memory allocation should remain proportional to the number of tokens (O(n)), where n is the number of lexical units in the input.

Chapter 7 — Normalizer Design
7.1 Purpose

The Tokenizer produces lexical tokens exactly as they appear in the user's command. These tokens may contain inconsistent capitalization, spacing, punctuation, or aliases.

The responsibility of the Normalizer is to transform these raw tokens into a canonical representation suitable for deterministic planning.

The Normalizer performs no intent detection and no registry lookup.

7.2 Responsibilities

The Normalizer SHALL:

Convert all text to lowercase.
Normalize whitespace.
Normalize punctuation.
Expand known aliases.
Standardize connectors.
Preserve token order.

The Normalizer SHALL NOT:

Resolve applications.
Resolve folders.
Resolve websites.
Detect user intent.
Create ActionPlans.
7.3 Normalization Pipeline
Raw Tokens
      │
      ▼
Lowercase
      │
      ▼
Whitespace Cleanup
      │
      ▼
Connector Normalization
      │
      ▼
Alias Expansion
      │
      ▼
Normalized Tokens
7.4 Alias Dictionary

Aliases are deterministic mappings.

Examples:

User Input	Normalized
vs code	vscode
visual studio code	vscode
google chrome	chrome
chat gpt	chatgpt
git hub	github
downloads folder	downloads

The alias dictionary shall be maintained separately from application, folder, and website registries.

7.5 Connector Normalization

The following connectors become a single canonical connector.

Input	Canonical
and	then
&	then
,	then
afterwards	then

Example:

Open Chrome, VS Code & GitHub

↓

Open Chrome then VS Code then GitHub
7.6 Whitespace Rules

The Normalizer shall:

Collapse:

Open     Chrome

↓

Open Chrome

Remove leading and trailing whitespace.

Normalize tabs and Unicode spaces.

7.7 Canonical Output

Example

Input

OPEN   Google Chrome  &  Git Hub

↓

Normalized Tokens

open
chrome
then
github
7.8 Error Handling

Normalization failures are extremely rare.

Possible errors:

Invalid Unicode
Empty command
Unsupported control characters

Planner Error:

NORMALIZATION_ERROR
Chapter 8 — Intent Detection
8.1 Purpose

Intent Detection converts normalized verbs into canonical Cortex intents.

It answers one question:

What does the user want to do?

It does not determine what should be acted upon.

8.2 Canonical Intents

Sprint 003 supports only two execution intents.

Canonical Intent	Description
open	Launch a resource
close	Terminate a running application

Future sprints may introduce:

create
delete
move
copy
rename

These are intentionally excluded from Sprint 003.

8.3 Verb Mapping

Examples:

Input	Canonical Intent
open	open
launch	open
start	open
run	open
close	close
exit	close
quit	close
8.4 Unknown Verbs

Example

Destroy Chrome

↓

Planner Error

UNKNOWN_INTENT

The planner shall never guess.

8.5 Intent Consistency

A single command may only contain one canonical intent.

Valid:

Open Chrome and GitHub

Invalid:

Open Chrome and close VS Code

Mixed intents are rejected in Sprint 003.

Planner Error:

MIXED_INTENTS

Support for mixed-intent workflows is deferred to a future sprint.

8.6 Confidence

Rule-based intent detection is deterministic.

Known intent:

confidence = 1.0

Unknown:

confidence = 0.0
Chapter 9 — Target Resolution
9.1 Purpose

The Target Resolver determines which registered resource each normalized target represents.

This component is the only planning stage permitted to access Cortex registries.

9.2 Registry Access

The resolver may query:

ApplicationRegistry
FolderRegistry
WebsiteRegistry

No filesystem scanning.

No executable discovery.

No internet requests.

9.3 Resolution Order

To ensure deterministic behavior, Cortex resolves targets in the following order:

Explicit Alias Table
Application Registry
Folder Registry
Website Registry

The first successful match wins.

9.4 Resolution Examples

Example

Input

chrome

↓

Application Registry

↓

application.open(chrome)

Example

Input

downloads

↓

Folder Registry

↓

folder.open(downloads)

Example

Input

github

↓

Website Registry

↓

website.open(github)
9.5 Unknown Target

Input

Open ABCXYZ123

↓

Planner Error

UNKNOWN_TARGET
9.6 Ambiguous Target

Example

Open Office

Possible matches:

Microsoft Office
LibreOffice

Planner returns:

AMBIGUOUS_TARGET

The planner shall never choose arbitrarily.

9.7 PlannerResult

The planner SHALL NOT return an ActionPlan directly.

Instead it returns:

PlannerResult
PlannerResult Model
class PlannerResult:
    plan: ActionPlan | None
    confidence: float
    normalized_input: str
    warnings: list[str]
    planning_time_ms: float
    success: bool

This model becomes the universal contract for every planner implementation.

9.8 Warning System

Planning may succeed while still producing warnings.

Example:

Open Chrome then Chrome

Warnings:

Duplicate target detected.

Execution remains valid.

9.9 Planning Errors

Standardized planner errors:

Code	Description
UNKNOWN_INTENT	Unsupported verb
UNKNOWN_TARGET	Resource not found
AMBIGUOUS_TARGET	Multiple matches
MIXED_INTENTS	Multiple canonical intents
TOKENIZATION_ERROR	Invalid lexical input
NORMALIZATION_ERROR	Failed normalization
EMPTY_COMMAND	No command supplied

These errors shall map cleanly to HTTP responses in Chapter 12.

9.10 Performance Target

The entire planning pipeline:

Tokenizer
Normalizer
Intent Detector
Target Resolver
Rule Planner

should complete in under 20 ms for a command containing up to 10 actions on a typical desktop system.

Chapter 10 — Planner Architecture
10.1 Overview

The Rule Planner is the final stage of the Natural Language Planning Engine.

Its responsibility is to transform structured planning data into a valid ActionPlan.

The planner does not execute actions.

The planner does not validate actions.

The planner does not perform safety checks.

Those responsibilities remain delegated to existing Sprint 001 components.

10.2 Responsibilities

The Rule Planner SHALL:

Receive normalized planning data.
Build sequential ActionPlans.
Preserve execution order.
Produce deterministic output.
Return PlannerResult.

The Rule Planner SHALL NOT:

Launch applications.
Open folders.
Open websites.
Access the operating system.
Skip validation.
Skip safety policy.
10.3 Internal Pipeline
Natural Language
        │
        ▼
Tokenizer
        │
        ▼
Normalizer
        │
        ▼
Intent Detector
        │
        ▼
Target Resolver
        │
        ▼
Rule Planner
        │
        ▼
PlannerResult
10.4 Planner Interface

All planners must implement the same interface.

class BasePlanner(ABC):

    @abstractmethod
    async def plan(
        self,
        command: str
    ) -> PlannerResult:
        ...

Future implementations:

BasePlanner
      │
      ├─────────────┐
      │             │
RulePlanner     ClaudePlanner
      │             │
GeminiPlanner   LocalPlanner

Every planner produces exactly the same output.

10.5 ActionPlan Generation

Example

Input

Open Chrome then GitHub

↓

Planner creates

ActionPlan

Step 1

Capability:
application.open

Target:
chrome

Step 2

Capability:
website.open

Target:
github

No execution occurs.

10.6 Planning Rules

The planner shall:

✓ Preserve user order

✓ Preserve user intent

✓ Resolve aliases

✓ Resolve registries

✓ Generate immutable ActionPlans

The planner shall never:

invent targets
guess unknown applications
guess websites
reorder commands
silently ignore failures
10.7 Duplicate Targets

Input

Open Chrome then Chrome

Planner:

Produces two steps.

PlannerResult contains warning:

Duplicate target detected.

Execution still proceeds.

10.8 Planner Metrics

PlannerResult records:

planning_time_ms
token_count
step_count
warning_count

These metrics are informational only.

Chapter 11 — PlannerResult Lifecycle
11.1 Purpose

PlannerResult is the official contract between every planner and the execution pipeline.

Instead of returning only an ActionPlan, every planner returns structured planning metadata.

11.2 PlannerResult Model
class PlannerResult(BaseModel):

    success: bool

    plan: ActionPlan | None

    normalized_input: str

    confidence: float

    warnings: list[str]

    planning_time_ms: float

    token_count: int

    step_count: int

    planner_name: str
11.3 Lifecycle
Command
      │
      ▼
Planner
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
11.4 Confidence

Sprint 003 RulePlanner returns:

Successful planning

1.0

Planning failure

0.0

Future AI planners may return intermediate values.

11.5 Planner Metadata

Example

Planner:
RulePlanner

Planning Time:
2.3 ms

Steps:
3

Warnings:
0

Confidence:
1.0
11.6 Failure Example
Input

Open ABCXYZ123

↓

PlannerResult

success = false

plan = null

confidence = 0.0

warnings = []

error = UNKNOWN_TARGET
11.7 Why PlannerResult Exists

Without PlannerResult:

Planner

↓

ActionPlan

Future AI compatibility becomes difficult.

With PlannerResult:

Planner

↓

PlannerResult

↓

Execution

Every planner shares one common interface.

Chapter 12 — API Contracts
12.1 Overview

Sprint 003 introduces two new REST endpoints while preserving backward compatibility.

12.2 POST /plan

Purpose

Generate an ActionPlan without executing it.

Request
{
    "command":"Open Chrome and GitHub"
}
Response
{
    "success":true,

    "planner":"RulePlanner",

    "confidence":1.0,

    "normalized_input":"open chrome then github",

    "plan":{

        ...

    }
}
12.3 POST /command

Purpose

Plan

↓

Validate

↓

Safety

↓

Execute

in one request.

Request
{
    "command":"Open Chrome"
}
Response

Existing ExecuteResponse.

No schema changes.

12.4 POST /execute

This endpoint remains unchanged.

Purpose:

Execute manually supplied ActionPlans.

Example

{
    "plan":{

        ...

    }
}

No natural language accepted.

This endpoint exists primarily for:

integrations
automation
developers
testing
12.5 Error Responses

Planner errors

HTTP 400

{
    "error":"UNKNOWN_TARGET",

    "message":"Target 'office' is not registered."
}

Validation errors

HTTP 422

Safety violations

HTTP 403

Execution errors

HTTP 500

12.6 API Compatibility

Sprint 003 guarantees:

✓ Existing clients continue working.

✓ Existing tests continue passing.

✓ Existing JSON execution unchanged.

12.7 Sequence Diagram
User
 │
 │ POST /command
 ▼
Planner
 │
 ▼
PlannerResult
 │
 ▼
Validator
 │
 ▼
Safety
 │
 ▼
Execution Engine
 │
 ▼
Operating System
 │
 ▼
ExecuteResponse
12.8 Dry Run Support

The /plan endpoint enables "preview mode."

Frontend flow:

Command

↓

POST /plan

↓

Preview

↓

User confirms

↓

POST /command

This ensures users can inspect Cortex's interpretation before execution.

Design Revision (Important)

While writing this section, I identified one architectural improvement that I want to include in the final specification instead of the original idea:

Instead of making POST /command always execute immediately, I recommend a two-step UX as the default:

User types command
        │
        ▼
POST /plan
        │
        ▼
Frontend shows generated plan
        │
        ▼
User presses "Execute"
        │
        ▼
POST /execute

Notice that in this flow, the frontend sends the generated ActionPlan to the existing /execute endpoint rather than calling /command. This has two advantages:

The existing /execute endpoint remains the single execution entry point.
The frontend can edit or inspect the generated plan before execution.

With this design, POST /command becomes an optional convenience endpoint for API consumers who want planning and execution in one request, while the Cortex UI itself follows the safer preview-first workflow.

I believe this is a cleaner architecture than making /command the primary path, and I'd adopt it as the official Sprint 003 design before implementation begins.


Chapter 13 — Frontend User Experience
13.1 Overview

Sprint 003 transforms the Cortex frontend from a developer-oriented JSON interface into a user-friendly natural language assistant while preserving transparency.

Users should never be required to manually construct JSON ActionPlans.

However, Cortex shall always display the generated execution plan before execution.

This design balances usability with deterministic behavior.

13.2 Design Principles

The frontend shall follow five principles:

Simplicity

The primary interaction shall be a single natural language input.

Transparency

Users must always be able to inspect the generated ActionPlan before execution.

Predictability

The interface must clearly distinguish between:

Planning
Validation
Execution
Feedback

Every stage shall provide immediate visual feedback.

Safety

Execution shall never begin without a successfully generated ActionPlan.

13.3 Layout
+-----------------------------------------------------------+
|                       Cortex                              |
+-----------------------------------------------------------+

 Ask Cortex...

 ┌──────────────────────────────────────────────────────┐
 │ Open Chrome and GitHub                               │
 └──────────────────────────────────────────────────────┘

        [ Generate Plan ]

---------------------------------------------------------

 Generated Plan

 ✓ Step 1
 application.open
 chrome

 ✓ Step 2
 website.open
 github

---------------------------------------------------------

 Warnings

 None

---------------------------------------------------------

 Confidence

 100%

---------------------------------------------------------

                [ Execute Plan ]
13.4 Workflow
Step 1

User enters command.

↓

Step 2

Frontend calls

POST /plan

↓

Step 3

PlannerResult displayed.

↓

Step 4

User reviews.

↓

Step 5

User clicks

Execute Plan

↓

Step 6

Frontend submits ActionPlan to

POST /execute
13.5 Planning Preview

Preview includes:

Normalized input
Planned steps
Resolved targets
Confidence
Warnings

Users always know exactly what Cortex intends to execute.

13.6 Error Presentation

Planning errors appear before execution.

Example:

Unknown target

"office"

Suggestion:

Did you mean "vscode"?

(Suggestions are optional and deterministic, based only on registered aliases. No AI-generated guesses.)

13.7 Execution Progress

Execution continues using the existing Sprint 002 interface.

Example:

Planning Complete

Executing...

✓ Chrome

✓ GitHub

✓ Downloads

Completed
Chapter 14 — Validation & Safety
14.1 Existing Validation

Sprint 003 does not replace validation.

Every ActionPlan must pass through:

Planner

↓

Validator

↓

Safety Policy

↓

Execution Engine
14.2 Planner Validation

The planner validates only planning correctness.

Examples:

✓ known intent

✓ known targets

✓ supported grammar

14.3 Execution Validation

Execution validation remains unchanged.

Examples:

capability exists
parameters valid
plan schema valid
14.4 Safety Policy

Safety Policy remains authoritative.

The planner cannot bypass it.

Examples rejected:

Open C:\Windows\System32
Run powershell.exe
Execute cmd.exe

unless explicitly registered in future sprints.

14.5 Registry Enforcement

Every target must resolve through registries.

Allowed:

chrome
downloads
github

Rejected:

C:\Users\...
https://...
14.6 Immutable Planning

After generation:

PlannerResult

↓

ActionPlan

must remain immutable.

Execution never mutates planning data.

Chapter 15 — Error Handling
15.1 Overview

Errors shall be deterministic, descriptive, and recoverable where possible.

No internal stack traces shall be exposed through the API.

15.2 Planner Errors
Code	Meaning
EMPTY_COMMAND	No input
UNKNOWN_INTENT	Unsupported verb
UNKNOWN_TARGET	Resource not registered
AMBIGUOUS_TARGET	Multiple registry matches
MIXED_INTENTS	Multiple canonical intents
TOKENIZATION_ERROR	Invalid lexical input
NORMALIZATION_ERROR	Failed normalization
15.3 Validation Errors

Examples:

Invalid ActionPlan

Missing capability

Invalid parameter

Returned by the existing Validator.

15.4 Safety Errors

Examples:

Unsafe application

Unsafe path

Unsafe capability

Returned by the Safety Policy.

15.5 Execution Errors

Examples:

Application not installed

Application failed to start

Timeout exceeded

Returned by the Execution Engine.

15.6 Error Flow
Planning

↓

Validation

↓

Safety

↓

Execution

The first failing stage terminates processing.

No subsequent stages execute.

15.7 Logging

Every failure shall produce structured logs including:

timestamp
planner
normalized command
error code
error message
planning duration

Sensitive operating-system information shall not be logged.	


Chapter 16 — Testing Strategy
16.1 Overview

Sprint 003 introduces a completely new planning layer. Since planning directly affects execution, every component of the planning pipeline must be independently testable.

Testing shall follow a layered approach.

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
API
     ↓
Frontend
     ↓
Acceptance Tests

No component may rely solely on end-to-end tests.

16.2 Unit Tests

Each planning component shall have isolated unit tests.

Tokenizer

Verify:

lowercase conversion
whitespace handling
punctuation splitting
connector identification

Example:

Input

Open Chrome & GitHub

↓

Tokens

open

chrome

then

github
Normalizer

Verify:

alias expansion
connector normalization
whitespace normalization

Example:

Google Chrome

↓

chrome
Intent Detector

Verify:

open

launch

run

start

↓

open
Target Resolver

Verify:

applications
folders
websites
unknown targets
ambiguous targets
Rule Planner

Verify:

step ordering
duplicate warnings
PlannerResult generation
confidence
planning time
16.3 Integration Tests

Integration tests shall verify:

Planner

↓

Validator

↓

Safety

↓

Execution

Examples:

Open Chrome

↓

Valid ActionPlan

↓

Execution

Unknown target

↓

Planning failure

↓

Execution never begins

16.4 API Tests

Endpoints requiring verification:

POST /plan

POST /execute

(optional)

POST /command

Verify:

schemas
status codes
planner errors
validation errors
16.5 Frontend Tests

Verify:

planning preview
warning display
confidence display
execute button state
API failures
16.6 Acceptance Tests

Real machine tests.

Examples:

Open Chrome

Chrome opens.

Open Downloads

Downloads opens.

Open Chrome then GitHub

Both execute sequentially.

16.7 Regression Tests

All Sprint 001 and Sprint 002 tests must continue passing.

No existing functionality may regress.

Chapter 17 — Performance Requirements
17.1 Overview

Natural language planning shall introduce minimal overhead.

Planning must feel instantaneous.

17.2 Target Latencies

Tokenizer

< 2 ms

Normalizer

< 2 ms

Intent Detection

< 1 ms

Target Resolution

< 5 ms

Rule Planner

< 10 ms

Entire planning pipeline

< 20 ms

Typical desktop hardware.

17.3 Memory

Planning memory usage shall scale approximately linearly with command size.

Target complexity:

O(n)
17.4 Scalability

Planner shall support:

up to 10 sequential actions
hundreds of registered applications
hundreds of websites
hundreds of folder aliases

without architectural modification.

Chapter 18 — Security Considerations
18.1 Principle

Natural language must never bypass Cortex security.

Planning increases usability, not privilege.

18.2 Registry Enforcement

Planner resolves only registered resources.

Rejected:

C:\Windows

powershell.exe

https://random-site.com

unless explicitly registered in future versions.

18.3 Command Injection

The planner shall never execute arbitrary shell commands.

Example:

Open Chrome && del C:\

↓

Rejected.

18.4 Path Injection

Raw filesystem paths are rejected.

Only aliases are accepted.

18.5 URL Injection

Raw URLs are rejected.

Only registered website aliases are accepted.

18.6 Audit Logging

Every command shall generate:

timestamp
normalized command
planner
planner result
execution result

Logs must never contain sensitive user data beyond what is required for debugging.

Chapter 19 — Future AI Compatibility
19.1 Purpose

Sprint 003 intentionally separates planning from execution.

Future AI models become planner implementations rather than execution engines.

19.2 Planner Interface

Future implementations:

RulePlanner

ClaudePlanner

GeminiPlanner

GPTPlanner

LocalPlanner

All implement:

BasePlanner
19.3 Execution Independence

Execution Engine remains unaware of:

LLM providers
prompts
tokens
conversations
inference

It only executes ActionPlans.

19.4 Future Capabilities

Potential future planners may support:

conversational planning
contextual memory
workflow generation
scheduling
voice commands
multimodal input

without changing downstream architecture.

Chapter 20 — Acceptance Criteria

Sprint 003 is considered complete only if all of the following conditions are satisfied.

Functional
User enters natural language.
Planner generates ActionPlan.
Preview is displayed.
Execution succeeds.
Existing JSON execution still works.
Quality
All previous tests pass.
New planning tests pass.
Manual verification completed.
No regression introduced.
Performance

Planning latency remains below specification.

Architecture

Execution Engine unchanged.

Validator unchanged.

Safety Policy unchanged.

Capability Registry unchanged.

Executors unchanged.

Only the Planning Layer is introduced.

Documentation

Specification updated.

Walkthrough updated.

Release summary written.

API documentation updated.

Appendix A — Supported Commands

Examples:

Open Chrome

Open VS Code

Open Downloads

Open ChatGPT

Open Chrome and GitHub

Open Chrome then Downloads

Close Chrome
Appendix B — High-Level Sequence Diagram
User
 │
 ▼
Frontend
 │
 ▼
POST /plan
 │
 ▼
Rule Planner
 │
 ▼
PlannerResult
 │
 ▼
Preview
 │
 ▼
User Confirms
 │
 ▼
POST /execute
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
 │
 ▼
Response
Appendix C — System Data Flow
Natural Language
        │
        ▼
Tokenizer
        │
        ▼
Normalizer
        │
        ▼
Intent Detector
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
Capability Registry
        │
        ▼
Executors
        │
        ▼
Operating System
Appendix D — Sprint Deliverables

Sprint 003 shall deliver:

Planning Layer
Tokenizer
Normalizer
Intent Detector
Target Resolver
Rule Planner
PlannerResult model
POST /plan endpoint
Planning preview UI
Extended unit tests
Integration tests
Acceptance tests
Updated documentation
Appendix E — Definition of Done

Sprint 003 is complete only when:

✅ All acceptance criteria are met.
✅ Existing functionality remains intact.
✅ 100% of planned deliverables are implemented.
✅ All tests pass.
✅ Manual verification succeeds.
✅ Fresh repository clone builds successfully.
✅ Documentation and release notes are complete.
✅ v0.3.0 is tagged and released.
Sprint 003 Specification Complete

This concludes the complete SPR-003-Natural-Language-Planning.md specification.

Final Architectural Review

Before you hand this to an implementation AI, I want to make two recommendations based on the full document:

1. Add a Planner Alias Configuration

Right now, aliases are described conceptually. Instead of hardcoding them, define a new configuration file:

config/planner_aliases.json

Example:

{
  "version": "1.0",
  "verbs": {
    "launch": "open",
    "start": "open",
    "run": "open",
    "quit": "close"
  },
  "targets": {
    "vs code": "vscode",
    "visual studio code": "vscode",
    "google chrome": "chrome",
    "chat gpt": "chatgpt"
  }
}

This keeps normalization data-driven and makes adding aliases possible without changing code.

2. Keep the Planning Pipeline Observable

I also recommend that the implementation emits structured events (or at least structured log entries) after each stage:

Tokenizer
↓

Normalizer
↓

Intent Detector
↓

Target Resolver
↓

Rule Planner

This isn't for the user. It's for debugging and future AI planners. If something goes wrong, you'll know exactly which stage produced the unexpected result instead of treating the planner as one opaque block.