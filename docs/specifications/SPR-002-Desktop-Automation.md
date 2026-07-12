SPR-002 — Desktop Automation Foundation

Document ID: SPR-002
Project: Cortex
Sprint: 002
Version: 1.0 (Draft)
Status: Engineering Specification
Prerequisite: Sprint 001 (v0.1.0)
Owner: Cortex Architecture Team
Implementation Target: Antigravity


Chapter 1 — Executive Summary, Vision & Engineering Principles
1. Executive Summary

Sprint 001 established Cortex as a deterministic execution engine capable of validating, planning, and executing structured action plans. While this provided the architectural foundation, the product itself remained largely invisible to the end user because it did not yet perform meaningful desktop automation.

Sprint 002 transforms Cortex from an execution engine into a practical desktop assistant.

Instead of merely accepting structured plans, Cortex will now interact with the Windows desktop by launching applications, opening folders, opening websites, and executing deterministic multi-step workflows.

This sprint deliberately avoids introducing artificial intelligence. Every action performed by Cortex must remain deterministic, fully validated, auditable, and reversible where applicable. Intelligence will be introduced only after the execution layer has demonstrated production-level reliability.

The objective is to ensure that by the conclusion of Sprint 002, Cortex becomes a tool that its primary user can realistically use every day.

2. Product Vision

The long-term vision of Cortex is not to become another chatbot.

Instead, Cortex aims to become a desktop operating layer capable of executing complex workflows across applications while remaining predictable, transparent, and safe.

Conceptually:

Human

↓

Natural Language

↓

Planner

↓

Execution Plan

↓

Validator

↓

Safety Engine

↓

Execution Engine

↓

Capabilities

↓

Operating System

The Planner may eventually be powered by an LLM, but the planner will never interact with the operating system directly.

All operating system interaction must occur exclusively through validated capabilities executed by the Execution Engine.

This separation is one of Cortex's fundamental architectural principles.

3. Sprint Vision

Sprint 002 focuses on one simple question:

Can Cortex perform useful desktop work without AI?

If the answer is yes, the project has successfully built the "hands" of the future assistant.

Examples include:

Open VS Code
Open Chrome
Open Spotify
Open Downloads
Open ChatGPT
Open the Cortex project
Execute several of these actions sequentially

No reasoning is required.

Only reliable execution.

4. Sprint Objectives

Sprint 002 shall achieve the following objectives.

Objective 1

Enable Cortex to discover and launch common Windows applications.

Objective 2

Enable Cortex to resolve registered folder aliases into filesystem locations.

Objective 3

Enable Cortex to launch registered websites using the user's default browser.

Objective 4

Expose sequential workflow execution through the existing execution engine.

Objective 5

Present users with detailed execution summaries rather than binary success/failure responses.

Objective 6

Expand automated testing to verify every newly introduced capability.

5. Success Criteria

Sprint 002 is considered complete only when all of the following conditions are satisfied.

Functional

The following actions execute successfully:

Open VS Code

Open Chrome

Open Spotify

Open Downloads

Open ChatGPT

Open VS Code then Open Cortex
Technical
All unit tests pass.
All integration tests pass.
Acceptance tests pass on a supported Windows machine.
Manual verification succeeds.
Product

The user should be able to replace manual desktop navigation with Cortex for common startup workflows.

6. Out of Scope

The following features are intentionally excluded.

Artificial Intelligence

No GPT

No Claude

No Gemini

No reasoning

No planning

Browser Automation

No Selenium

No Playwright

No DOM interaction

No clicking buttons

No typing

Input Automation

No keyboard automation

No mouse automation

No OCR

No vision

Long-Term Memory

No persistent conversation memory

No scheduling

No reminders

7. Engineering Philosophy

Sprint 002 adopts several engineering principles that shall remain valid throughout the Cortex project.

Principle 1

Deterministic execution always takes precedence over intelligent execution.

A predictable assistant is more valuable than an unpredictable intelligent assistant.

Principle 2

The Execution Engine owns all operating system interaction.

Neither the planner nor the frontend may interact with Windows directly.

Principle 3

Every action must correspond to an explicit capability.

There shall be no hidden behavior.

Principle 4

Every capability must be independently testable.

Capabilities are expected to evolve independently without modifying unrelated subsystems.

Principle 5

Configuration shall be data-driven.

New applications, folders, and websites should primarily be added through configuration rather than source code changes.

Principle 6

All execution must be observable.

Every action shall generate structured logs containing:

Timestamp
Execution ID
Capability
Executor
Duration
Result
Error (if applicable)
Principle 7

Failure shall be explicit.

Silent failures are prohibited.

Whenever Cortex cannot complete an action, the user shall receive a structured explanation rather than a generic failure message.

8. Architectural Goals

Sprint 002 is designed to satisfy the following architectural goals.

Extensibility

Adding a new desktop capability should require implementing a new executor rather than modifying the execution engine.

Maintainability

Subsystems shall have clearly defined responsibilities with minimal coupling.

Testability

Every service introduced during Sprint 002 must support dependency injection and isolated testing.

Safety

Unsafe desktop operations shall be rejected before execution.

Validation occurs before interaction with the operating system.

Future Compatibility

Sprint 002 shall prepare Cortex for future sprints involving:

Natural language parsing
Workspace automation
AI planning
Browser automation
Vision systems
Keyboard automation
Mouse automation

without requiring significant architectural redesign.

9. Sprint Deliverables

Sprint 002 is expected to produce:

Application Discovery subsystem
Folder Registry subsystem
Website Registry subsystem
Workflow execution support
Execution summary reporting
Backend API extensions
Frontend dashboard improvements
Comprehensive automated tests
Updated documentation
Release tag v0.2.0

10. End State

At the completion of Sprint 002, Cortex should no longer be viewed as an execution engine prototype.

Instead, it should be regarded as the first practical layer of a desktop operating assistant capable of reliably executing deterministic workflows.

The project remains intentionally non-intelligent at this stage. Intelligence will be introduced only after the execution layer has demonstrated stability, predictability, and production-quality reliability.


End of Chapter 2



Chapter 2 — System Architecture & Capability Framework
11. System Architecture Overview

Sprint 001 introduced the Execution Engine as the center of Cortex. Sprint 002 expands the surrounding ecosystem while keeping the Execution Engine unchanged.

The guiding architectural rule is:

New functionality should be added by introducing new capabilities, not by modifying the Execution Engine.

This ensures Cortex grows horizontally rather than becoming a monolithic application.

The complete runtime architecture becomes:

                 User
                  │
                  ▼
          Frontend (React)
                  │
                  ▼
            FastAPI Backend
                  │
                  ▼
         Request Validation Layer
                  │
                  ▼
              Planner Layer
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
      ┌───────────┼───────────┐
      ▼           ▼           ▼
 Capability   Event Bus   Structured Logger
   Registry     (future)
      │
      ▼
┌──────────────────────────────────────┐
│ Application Executor                 │
│ Folder Executor                      │
│ Website Executor                     │
│ Future Executors                     │
└──────────────────────────────────────┘
      │
      ▼
 Windows Operating System

Notice something important.

The Execution Engine never knows which executor it is calling.

It only knows capabilities.

12. Layer Responsibilities

Every layer in Cortex has one responsibility.

Presentation Layer

Responsible for:

User Interface
User Input
Progress display
Execution summaries

Never responsible for:

Business logic
Planning
Validation
Desktop automation
API Layer

Responsible for:

HTTP endpoints
Request validation
Response serialization

Never responsible for:

Desktop operations
Registry lookup
Execution
Planning Layer

Responsible for producing Action Plans.

Sprint 002 continues using the Stub Planner introduced in Sprint 001.

Future planners (GPT, Claude, Gemini) must implement the same interface.

Validation Layer

Responsible for:

Schema validation
Capability validation
Registry verification
Action syntax

Validation happens before Safety Policy.

Safety Layer

Responsible for determining whether execution is allowed.

Safety never performs execution.

It only approves or rejects.

Execution Layer

Responsible for:

Sequential execution
Timeouts
Locks
Error propagation
Execution summaries

The Execution Engine owns execution.

Capability Layer

Responsible for mapping abstract capabilities to concrete executors.

Example:

application.open
        │
        ▼
ApplicationOpenExecutor
Executor Layer

Responsible for interacting with Windows.

Executors perform the actual operating system calls.

Nothing else may interact with Windows directly.

13. Capability-Based Architecture

Sprint 002 introduces Cortex's most important architectural concept.

Capability

A capability represents something Cortex knows how to do.

Examples:

application.open

application.close

folder.open

website.open

Future examples:

browser.click

browser.type

browser.read

terminal.run

python.run

clipboard.copy

clipboard.paste

window.focus

file.rename

spotify.play

Notice that capabilities describe behavior, not implementation.

14. Why Capabilities?

Without capabilities:

Planner

↓

ApplicationExecutor

The planner becomes tightly coupled to implementation.

Instead:

Planner

↓

Capability

↓

Registry

↓

Executor

The planner knows nothing about Windows.

It only understands capabilities.

This allows future planners to remain completely independent from implementation details.

15. Capability Registry

Sprint 002 introduces the Capability Registry.

Responsibilities:

Register executors
Register supported capabilities
Resolve executor by capability
Prevent duplicate registrations
Verify capability existence

Example:

registry.register(
    capability="application.open",
    executor=ApplicationOpenExecutor()
)

Lookup:

executor = registry.resolve("application.open")

The Execution Engine never imports executors directly.

16. Registry Architecture

Sprint 002 introduces multiple specialized registries.

Registry
│
├── Capability Registry
│
├── Application Registry
│
├── Folder Registry
│
└── Website Registry

Each registry has one responsibility.

Application Registry

Stores:

Application aliases
Executable paths
Discovery metadata

Example:

chrome

↓

C:\Program Files\Google\Chrome\Application\chrome.exe
Folder Registry

Stores:

chatbot

↓

E:\College Projects\Chatbot

No raw user paths.

Website Registry

Stores:

chatgpt

↓

https://chat.openai.com

No arbitrary URLs.

17. Registry Design Rules

Registries shall:

be immutable during execution
support dependency injection
load configuration once
cache lookups
expose read-only APIs

Registries shall never:

launch applications
modify files
perform execution
18. Dependency Injection

Sprint 002 standardizes constructor injection.

Example:

ExecutionEngine(
    registry,
    validator,
    safety_policy,
    logger,
    event_bus
)

The engine never constructs dependencies itself.

Benefits:

Easier testing
Better maintainability
Mock-friendly
Reduced coupling
19. Folder Structure

Backend:

backend/

app/

api/

config/

engine/

executors/

planner/

registry/

validator/

safety/

models/

schemas/

services/

events/

logging/

tests/

Each package owns one responsibility.

20. Execution Pipeline

Every request follows exactly the same lifecycle.

HTTP Request

↓

Planner

↓

Action Plan

↓

Validator

↓

Safety Policy

↓

Execution Engine

↓

Capability Registry

↓

Executor

↓

Operating System

↓

Execution Summary

↓

HTTP Response

No shortcuts.

Every execution follows the same pipeline.

21. Event Bus

Sprint 002 introduces the EventBus interface.

Only the interface.

No implementation.

Example future events:

ExecutionStarted

CapabilityStarted

CapabilityCompleted

CapabilityFailed

ExecutionFinished

Future sprints can subscribe to these events without modifying the Execution Engine.

22. Logging Architecture

Logging remains centralized.

Every subsystem logs through the Structured Logger.

Required fields:

Timestamp
Execution ID
Capability
Executor
Duration
Result
Error
Severity

Executors never write directly to log files.

23. Design Constraints

The following constraints are mandatory.

The Execution Engine:

must not know Windows APIs
must not read configuration files
must not construct executors
must not parse JSON
must not contain application-specific logic

Executors:

must perform exactly one responsibility.

Registries:

must never execute actions.

Planners:

must never interact with Windows.
24. Architectural Invariants

These rules shall remain true for all future sprints.

1.Every desktop action is represented by a capability.
2.Every capability resolves to exactly one executor.
3.Every execution passes through Validation and Safety.
4.The Execution Engine remains deterministic.
5.The Planner never interacts with Windows.
6.Registries remain read-only during execution.
7.Logging is mandatory.
8.Dependency Injection is mandatory.
9.Execution order is controlled exclusively by the Execution Engine.
10.Future AI planners shall integrate without changing the execution layer.


End of Chapter 2


Chapter 3 — Capability Specifications, Registries & Configuration
25. Purpose

Sprint 002 introduces the first production capabilities of Cortex.

Unlike Sprint 001, which focused on execution infrastructure, Sprint 002 defines concrete desktop operations.

Every desktop operation is represented as a capability.

Capabilities are:

deterministic
independently testable
independently deployable
independently replaceable

The Execution Engine treats every capability identically.

26. Capability Contract

Every capability must satisfy the following interface.

Capability

name: str
version: str
executor: BaseExecutor
timeout: float
safe: bool
parallel: bool
description: str

Each capability must declare:

its unique identifier
supported version
responsible executor
timeout
safety classification
whether parallel execution is allowed

Capabilities never contain business logic.

27. Capability Naming Standard

All capabilities follow the format

<object>.<action>

Examples

application.open

application.close

folder.open

website.open

Future examples

browser.open

browser.click

browser.type

browser.read

terminal.run

python.execute

clipboard.copy

clipboard.paste

window.focus

window.resize

spotify.play

This naming convention becomes mandatory for every future sprint.

28. Application Discovery

Application discovery is responsible for locating executable programs on Windows.

Applications may be discovered automatically or loaded from configuration.

Discovery occurs only once during startup.

Supported Applications

Sprint 002 officially supports

VS Code
Chrome
Edge
Firefox
Spotify
Windows Terminal
Notepad
Calculator
Explorer

Support for additional applications is configuration-driven.

Discovery Algorithm

Applications are resolved in the following order.

Known Installation Locations

↓

Windows PATH

↓

User Configuration

↓

Failure

Future Sprint

Windows Registry

will be inserted before user configuration.

Discovery Cache

Application discovery shall occur once.

Results are cached.

Executors never rescan the system.

Failure

If discovery fails

ApplicationNotFound

is returned.

No fallback guessing.

29. Application Registry

Purpose

Maintain known applications.

Responsibilities

register
resolve
cache
validate

Never

execute
modify Windows
launch applications

Example

{
    "chrome": {
        "display_name": "Google Chrome",
        "path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "auto_discovered": true
    }
}
30. Folder Registry

Folder aliases replace raw filesystem paths.

Instead of

E:\College Projects\Chatbot

the user writes

chatbot
Configuration
{
    "chatbot":"E:\\College Projects\\Chatbot",
    "cortex":"E:\\College Projects\\Cortex",
    "downloads":"C:\\Users\\User\\Downloads",
    "desktop":"C:\\Users\\User\\Desktop"
}
Rules

Unknown aliases

↓

Reject

Raw paths

↓

Reject

Traversal

↓

Reject

Only registered aliases are accepted.

31. Website Registry

The Website Registry maps aliases to trusted URLs.

Example

{
    "chatgpt":"https://chat.openai.com",
    "github":"https://github.com",
    "gmail":"https://mail.google.com",
    "youtube":"https://youtube.com",
    "gemini":"https://gemini.google.com"
}
Rules

Unknown websites

↓

Reject

Only HTTPS

↓

Allow

HTTP

↓

Reject

Localhost

↓

Future decision

32. Configuration Architecture

Sprint 002 introduces versioned configuration.

config/

apps.json

folders.json

websites.json

aliases.json

Every configuration file contains

{
    "version":"1.0",
    "generated_at":"...",
    "entries":[]
}

Future migrations become possible.

33. Configuration Loader

Configuration Loader responsibilities

validate schema
load JSON
cache
expose read-only access

Never

modify files during execution
execute actions
34. Capability Resolution

Example

User requests

Open Chrome

Planner

↓

application.open

Registry

↓

Chrome

↓

Application Executor

↓

Windows

No layer skips another.

35. Workflow Execution

Sprint 002 introduces user-facing workflows.

Example

Open Chrome

↓

Open ChatGPT

↓

Open VS Code

↓

Open Cortex Folder

Internally

Execution Plan

↓

Step 1

↓

Step 2

↓

Step 3

↓

Step 4

Execution stops immediately on failure.

36. Workflow Rules

Sequential only.

No branching.

No loops.

No retries.

No conditions.

Future sprints may introduce

if
else
parallel
retry
wait

but Sprint 002 remains deterministic.

37. Execution Summary

Every execution returns structured output.

Example

Execution Summary

────────────────────

✓ Chrome

✓ ChatGPT

✓ VS Code

✓ Cortex Folder

────────────────────

Duration

1.83 seconds

4 / 4 completed

On failure

✓ Chrome

✓ ChatGPT

✗ VS Code

Execution stopped

Reason

ApplicationNotFound
38. Performance Requirements

Application lookup

< 10 ms

Folder lookup

< 2 ms

Website lookup

< 2 ms

Execution Engine overhead

< 20 ms

Configuration loading

Startup only

Memory footprint

Minimal

39. Security Requirements

The following are forbidden.

Raw filesystem paths
Arbitrary URLs
Arbitrary executables
Shell injection
Dynamic imports
Runtime code execution

Sprint 002 remains allow-list based.

40. Extensibility

Adding a capability must require

New Executor
Register Capability
Tests

No Execution Engine changes.

41. Sprint 002 Completion State

At the end of Sprint 002 Cortex understands

Open Chrome

Open VS Code

Open Spotify

Open Downloads

Open ChatGPT

Open Cortex

and executes them through exactly the same pipeline regardless of capability.

This completes the first usable desktop automation layer.

End of Chapter 3


Chapter 4 — API Contracts, Data Models & Runtime Specification
42. Purpose

This chapter defines the public contract between the frontend, backend, execution engine, and future AI planners.

The objectives are:

Stable APIs
Predictable runtime behavior
Strict schemas
Version compatibility
Deterministic execution

Every API defined in this chapter shall remain backward compatible within the same major version.

43. API Design Principles

All Cortex APIs follow these rules:

Stateless HTTP requests.
JSON request/response bodies.
Structured error responses.
Versioned schemas.
Predictable status codes.
No hidden side effects.

Every endpoint must be fully documented before implementation.

44. API Overview
Existing Endpoints
POST /execute
GET  /status
GET  /health
New Endpoints
GET /applications
GET /folders
GET /websites
GET /capabilities

Future versions may add:

POST /planner
GET  /history
GET  /metrics

without modifying existing endpoints.

45. Execute Request Schema
{
  "version": "1.0",
  "plan": {
    "steps": [
      {
        "capability": "application.open",
        "target": "chrome"
      }
    ]
  }
}

Rules:

version is mandatory.
plan.steps cannot be empty.
Steps execute sequentially.
Maximum 100 steps.
Unknown capabilities are rejected.
46. Execute Response Schema
{
  "execution_id": "...",
  "status": "completed",
  "duration_ms": 1830,
  "summary": {
    "successful": 4,
    "failed": 0,
    "total": 4
  },
  "results": [
    {
      "step": 1,
      "capability": "application.open",
      "target": "chrome",
      "status": "success"
    }
  ]
}

The response must contain results for every executed step.

47. Health Endpoint

Purpose:

Verify backend availability.

Example:

{
  "status": "healthy",
  "version": "0.2.0",
  "uptime_seconds": 512,
  "planner": "StubPlanner",
  "engine": "ready"
}

This endpoint never performs desktop operations.

48. Status Endpoint

Returns runtime information.

Example:

{
  "busy": false,
  "active_execution": null,
  "queued": 0
}

Future versions may include resource usage.

49. Applications Endpoint

Returns registered applications.

Example:

[
  {
    "alias": "chrome",
    "display_name": "Google Chrome",
    "discovered": true
  },
  {
    "alias": "code",
    "display_name": "Visual Studio Code",
    "discovered": true
  }
]

No executable paths should be exposed to the frontend.

50. Folder Endpoint

Example:

[
  {
    "alias": "chatbot"
  },
  {
    "alias": "downloads"
  }
]

Actual filesystem paths remain backend-only.

51. Website Endpoint

Example:

[
  {
    "alias": "chatgpt"
  },
  {
    "alias": "github"
  }
]

URLs may optionally be hidden from the frontend to reduce unnecessary exposure.

52. Capability Endpoint

Returns every capability supported by Cortex.

Example:

[
  "application.open",
  "application.close",
  "folder.open",
  "website.open"
]

This endpoint is essential for future AI planners, allowing them to discover available functionality dynamically.

53. Runtime Data Models
ExecutionPlan

Represents the complete plan.

Fields:

id
version
created_at
steps

Immutable after creation.

ExecutionStep

Fields:

capability
target
timeout
metadata

One ExecutionStep represents exactly one desktop action.

ExecutionResult

Fields:

step_index
capability
target
status
duration
error

Results are immutable after completion.

ExecutionSummary

Fields:

total
successful
failed
duration

Generated automatically after execution.

54. Execution State Machine
Created
    │
    ▼
Validated
    │
    ▼
Safety Checked
    │
    ▼
Executing
    │
 ┌──┴──────────────┐
 │                 │
 ▼                 ▼
Completed      Failed

No state transitions may bypass Validation or Safety.

55. Step State Machine

Each individual step follows:

Pending

↓

Running

↓

Succeeded

or

Failed

or

Timed Out

Once complete, a step is immutable.

56. Error Model

Every error consists of:

{
  "code": "APPLICATION_NOT_FOUND",
  "message": "Chrome could not be located.",
  "details": {},
  "execution_id": "..."
}

Human-readable messages are separate from machine-readable codes.

57. Standard Error Codes

Sprint 002 defines:

APPLICATION_NOT_FOUND

FOLDER_NOT_FOUND

WEBSITE_NOT_FOUND

UNKNOWN_CAPABILITY

INVALID_PLAN

VALIDATION_FAILED

SAFETY_REJECTED

EXECUTION_TIMEOUT

EXECUTION_IN_PROGRESS

INTERNAL_ERROR

Future sprints may extend this list but must not rename existing codes.

58. Logging Contract

Every execution generates:

Execution Started

↓

Step Started

↓

Step Finished

↓

Summary Generated

↓

Execution Finished

Required log fields:

execution_id
timestamp
capability
executor
target
duration_ms
result
error_code (if any)

Logs must be structured (JSON or equivalent), never plain text only.

59. Sequence Diagram
User
 │
 ▼
Frontend
 │
 ▼
FastAPI
 │
 ▼
Planner
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
Executor
 │
 ▼
Windows
 │
 ▼
Execution Result
 │
 ▼
Frontend

Every request follows this exact sequence.

60. API Versioning Strategy

All requests include:

{
  "version": "1.0"
}

Major version changes indicate breaking changes.

Minor versions remain backward compatible.

This allows future planners and frontends to evolve independently.

61. Performance Requirements
API response validation: < 5 ms
Registry lookup: < 2 ms
Capability resolution: < 2 ms
Logging overhead: < 5 ms
Engine overhead (excluding OS launch): < 20 ms

These targets ensure Cortex's internal architecture does not become the bottleneck.

62. Compatibility Rules

New capabilities may be added.

Existing capabilities may not change behavior in incompatible ways within the same major version.

Deprecated capabilities must remain functional for at least one major release before removal.

63. Chapter Completion

At the end of this chapter, the backend has a complete contract covering:

API surface
Request/response formats
Runtime models
Execution lifecycle
Error handling
Logging
State transitions
Versioning

Implementation should now be possible without ambiguity regarding how components communicate.

End of Chapter 4


Chapter 5 — Frontend Specification, User Experience & Testing
64. Purpose

The frontend is the user's primary interaction point with Cortex.

Its responsibility is to:

Accept execution requests
Display execution progress
Present execution summaries
Surface structured errors
Expose registered capabilities

The frontend must never contain business logic or perform desktop operations directly.

65. Frontend Architecture

The frontend shall be implemented using:

React
TypeScript
Vite

Structure:

frontend/
│
├── src/
│   ├── api/
│   ├── components/
│   ├── hooks/
│   ├── pages/
│   ├── types/
│   ├── styles/
│   └── App.tsx
│
├── public/
└── package.json

Responsibilities:

Components → Presentation
API Layer → HTTP communication
Types → Shared models
Hooks → State management
66. Design Principles

The UI should feel:

Fast
Minimal
Professional
Calm
Developer-focused

Avoid:

Excessive animations
Bright colors
Dashboard clutter
Modal-heavy workflows

Cortex is a productivity tool, not a social application.

67. Primary Dashboard

The dashboard contains:

┌───────────────────────────────┐
│ Cortex                        │
├───────────────────────────────┤
│ Command Input                 │
│                               │
│ Open Chrome                   │
│                               │
│ [ Execute ]                   │
├───────────────────────────────┤
│ Execution Summary             │
├───────────────────────────────┤
│ Registered Applications       │
├───────────────────────────────┤
│ Folder Aliases                │
├───────────────────────────────┤
│ Website Aliases               │
└───────────────────────────────┘

The interface should fit on one screen without unnecessary scrolling.

68. Command Input

The primary input accepts desktop commands.

Examples:

Open Chrome

Open VS Code

Open Downloads

Open ChatGPT

Future versions may support natural language, but Sprint 002 focuses on deterministic command execution.

69. Execution Progress

During execution:

Executing...

✓ Open Chrome

✓ Open ChatGPT

○ Open VS Code

○ Open Cortex

Legend:

○ Pending
▶ Running
✓ Success
✗ Failed

Progress updates in real time as steps complete.

70. Execution Summary

After completion:

Execution Summary

✓ Chrome
✓ ChatGPT
✓ VS Code
✓ Cortex Folder

Completed in 1.82 seconds

4 / 4 successful

If execution fails:

✓ Chrome

✓ ChatGPT

✗ VS Code

Execution stopped.

Reason:

ApplicationNotFound

The summary should always explain what happened.

71. Registered Applications Panel

Display:

Applications

Chrome

VS Code

Spotify

Explorer

Notepad

Purpose:

Help users understand available capabilities.
Aid troubleshooting when an application is unavailable.
72. Folder Aliases Panel

Example:

Folders

chatbot

cortex

downloads

desktop

Only aliases are displayed.

Filesystem paths remain hidden.

73. Website Aliases Panel

Example:

Websites

ChatGPT

GitHub

YouTube

Gemini

URLs are not displayed unless debugging mode is enabled.

74. Error Display

Errors should be clear and actionable.

Example:

Application Not Found

Chrome is not registered.

Register it in:

config/apps.json

Avoid technical stack traces in the UI.

75. User Flow

Example:

User

↓

Enter command

↓

Execute

↓

Validation

↓

Execution

↓

Summary

↓

Ready

Every command follows the same lifecycle.

76. Frontend State Model

The frontend maintains:

Idle

↓

Executing

↓

Completed

or

Failed

↓

Idle

No additional transient states are introduced in Sprint 002.

77. Performance Requirements

Frontend targets:

Initial load < 2 seconds
Command submission < 100 ms
Summary render < 100 ms
API latency indicator displayed if > 500 ms
78. Accessibility

Minimum requirements:

Full keyboard navigation
Visible focus indicators
High-contrast theme
Semantic HTML
Responsive layout for common desktop resolutions

Accessibility is a quality requirement, not an optional enhancement.

79. Testing Strategy

Testing is divided into three layers.

Unit Tests

Verify:

Registry behavior
Executors
Validator
Safety Policy
API serialization
Frontend components
Integration Tests

Verify:

Backend endpoints
Workflow execution
Registry integration
Execution summaries
Acceptance Tests

Run on a Windows machine.

Verify:

Chrome launches
VS Code launches
Folder aliases resolve
Websites open
Sequential workflows execute correctly
80. Manual Verification Checklist

Before release:

Backend starts without errors.
Frontend loads successfully.
Health endpoint returns healthy status.
Applications launch correctly.
Folder aliases work.
Website aliases work.
Execution summary matches actual execution.
Logs are generated.
No unhandled exceptions appear.

Every item must pass before tagging the release.

81. Quality Gates

Sprint 002 cannot be considered complete unless:

All automated tests pass.
Manual verification passes.
No critical defects remain.
Documentation is updated.
Code is reviewed.
Release tag (v0.2.0) is created.

These gates ensure every sprint ends in a deployable state.

82. Future UI Compatibility

The dashboard should be designed to accommodate future features without redesign.

Reserved areas include:

Voice interaction
Conversation history
AI planner status
Active workflow queue
Plugin management
Execution history timeline

This allows Sprint 003+ features to integrate without replacing the existing interface.

End of Chapter 5


Chapter 6 — Implementation Plan, Engineering Standards & Release
83. Purpose

This chapter defines how Sprint 002 will be built, not just what will be built.

Every implementation must follow the milestones, coding standards, testing requirements, and release process described here.

The goal is to make Sprint 002 repeatable, maintainable, and production-ready.

84. Implementation Strategy

Sprint 002 shall be implemented bottom-up.

The recommended order is:

Configuration
        ↓
Registries
        ↓
Capabilities
        ↓
Executors
        ↓
Execution Engine Integration
        ↓
API Layer
        ↓
Frontend
        ↓
Tests
        ↓
Manual Verification

Higher layers must never be implemented before their dependencies are complete.

85. Milestone Breakdown
Milestone 1 — Registry Infrastructure

Deliverables:

ApplicationRegistry
FolderRegistry
WebsiteRegistry
Registry interfaces
Configuration loader updates

Tests:

Registry loading
Invalid configuration handling
Alias lookup
Cache behavior
Milestone 2 — Application Discovery

Deliverables:

Windows discovery service
PATH lookup
Built-in installation lookup
Application cache

Tests:

Known applications
Missing applications
Duplicate registrations
Milestone 3 — Website & Folder Capabilities

Deliverables:

website.open
folder.open improvements
Registry integration

Tests:

Alias resolution
Invalid aliases
Unknown websites
Milestone 4 — Workflow Execution

Deliverables:

Sequential execution
Execution summary
Failure propagation

Tests:

Multi-step workflows
Stop-on-first-failure
Summary generation
Milestone 5 — API Layer

Deliverables:

GET /applications
GET /folders
GET /websites
GET /capabilities

Tests:

Response schemas
Status codes
Error handling
Milestone 6 — Frontend

Deliverables:

Registry panels
Execution summary
Progress indicators
Error display

Tests:

Component rendering
API integration
User interaction
Milestone 7 — Verification

Deliverables:

Unit tests
Integration tests
Acceptance tests
Manual verification
86. Coding Standards

Every contribution must follow these rules.

Naming

Classes:

ApplicationRegistry
WebsiteExecutor
ExecutionSummary

Methods:

resolve_application()
load_registry()
execute_step()

Variables:

execution_id
application_alias
workflow_result

Avoid abbreviations unless universally understood.

File Organization

One primary responsibility per file.

Example:

application_registry.py
website_registry.py
folder_registry.py

Do not combine unrelated functionality.

Dependency Rules

Allowed:

API
    ↓
Services
    ↓
Engine
    ↓
Executors

Forbidden:

Executor
    ↓
Frontend

or

Planner
    ↓
Windows API
87. Error Handling Standards

Errors must never be swallowed.

Every exception should:

Be logged.
Be converted into a structured error.
Preserve the execution ID.
Return an appropriate HTTP status code.

Avoid generic except Exception unless re-raising with context.

88. Logging Standards

Every log entry must include:

Timestamp
Execution ID
Component
Capability
Duration
Result
Severity

Preferred format:

{
  "timestamp": "...",
  "execution_id": "...",
  "component": "ExecutionEngine",
  "capability": "application.open",
  "duration_ms": 143,
  "result": "success"
}

Structured logging is mandatory.

89. Performance Targets

Startup time:

< 2 seconds

Registry lookup:

< 2 ms

Capability resolution:

< 2 ms

Engine overhead:

< 20 ms

Memory usage:

Minimal growth with additional capabilities

Performance regressions should be detected during testing.

90. Security Rules

Sprint 002 follows an allow-list security model.

Allowed:

Registered applications
Registered folders
Registered websites

Rejected:

Arbitrary executables
Raw filesystem paths
Unknown URLs
Shell commands
Runtime code execution

Future sprints may extend permissions but must preserve secure defaults.

91. Release Checklist

Before tagging v0.2.0, verify:

 Backend builds successfully.
 Frontend builds successfully.
 All automated tests pass.
 Manual verification passes.
 Documentation updated.
 Configuration examples included.
 Release notes written.
 Git tag created.
 No critical defects remain.
92. Future Compatibility

Sprint 002 lays the foundation for:

Sprint 003

Natural Language Parser

Sprint 004

Workspace Automation

Sprint 005

LLM Planner Integration

Sprint 006

Browser Automation

Sprint 007

Vision & OCR

Sprint 008

Mouse & Keyboard Automation

Sprint 009

Plugin System

Sprint 010

Jarvis-style Autonomous Workflows

Every future sprint should extend the capability system rather than bypass it.

93. Risks

Known risks:

Application discovery differences across Windows versions.
User-specific installation paths.
Browser URL handling differences.
Registry corruption or invalid configuration files.

Mitigations:

Configuration fallback.
Validation before execution.
Structured error reporting.
Extensive automated tests.
94. Definition of Done

Sprint 002 is complete when:

All milestones are implemented.
Every acceptance criterion is satisfied.
The system is stable under expected workloads.
Documentation is frozen.
Git tag v0.2.0 is created.
95. Conclusion

Sprint 002 marks the transition of Cortex from an architectural prototype to a genuinely useful desktop automation platform.

After this sprint, Cortex should reliably launch applications, open folders, navigate to registered websites, and execute deterministic workflows while maintaining strict validation, safety, and observability.

This capability-first architecture ensures that future additions such as natural language parsing, AI planning, browser automation, and vision can be integrated without redesigning the execution layer.

Sprint 002 therefore serves not only as a feature release but as the long-term foundation for Cortex's evolution into a Jarvis-inspired desktop assistant.

End of Chapter 6