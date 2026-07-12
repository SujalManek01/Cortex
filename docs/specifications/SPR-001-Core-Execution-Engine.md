# SPR-001 — Core Execution Engine (Version 1.0 Final)

This specification freezes the architecture for Sprint 001.

## Executive Summary
Cortex is an AI operating layer that converts natural language into safe deterministic computer actions.

## Objectives
- Natural language input
- Planner abstraction
- Immutable ActionPlan
- Validator
- Safety Policy
- Deterministic execution
- Structured logging

## Non Objectives
Voice, Memory, Plugins, Browser Automation, Cloud Sync, Database, Authentication.

## Technology
Backend: Python 3.12+, FastAPI, Pydantic
Frontend: React, TypeScript, Vite
OS: Windows 11

## Architecture
Frontend -> Planner -> ActionPlan -> Validator -> Safety Policy -> Execution Engine -> Action Registry -> Executors -> Windows

Validation/Safety failures return structured errors to frontend.

## Action Language
domain.verb

Examples:
application.open
application.close
folder.open

Future examples (not Sprint 1):
browser.open
terminal.run
music.play
ai.ask

## ActionPlan
Fields:
- plan_id (UUID)
- goal
- version
- created_by
- steps[]

Each step:
- id
- action
- parameters

ActionPlan is immutable.

## Execution State
Maintained separately from ActionPlan.
States:
pending, running, completed, failed, skipped.

## Validator
Checks:
- schema
- version
- supported actions
- parameter types

Unknown versions rejected.

## Safety Policy
- Application allow-list
- Alias validation
- Reject raw executable paths
- Reject unsafe plans

## Application Registry
Only registered applications may launch.

## Alias Configuration
config/aliases.json
Only aliases resolve to folders.

## Executor Interface

execute(context, parameters) -> ActionResult

## ActionContext
Contains:
- logger
- read-only config
- workspace metadata
- runtime services

## ActionResult
Fields:
- step_id
- success
- message
- error_code
- duration_ms
- metadata

## Registry
Self-registering executors.
Engine never contains action-specific conditionals.

## Execution Engine
- Sequential execution
- Stop on failure
- One plan at a time
- 30 second timeout per step
- Structured events

## Logging
JSON Lines.
Fields:
plan_id, step_id, action, parameters, timestamps, duration, status, error_code.

## Project Structure
backend/
 planner/
 validator/
 safety/
 engine/
 registry/
 executors/

frontend/
config/
tests/
docs/

## Error Handling
Unknown application
Invalid alias
Invalid plan
Timeout
Launch failure

All failures are structured.

## Acceptance Tests
1. Open VS Code
2. Open Chrome
3. Open chatbot project
4. Invalid application rejected
5. Invalid ActionPlan rejected
6. Partial failure stops execution
7. Concurrent execution rejected
8. Timeout handled

## Definition of Done
- Tests pass
- Modular architecture
- Safety policy enforced
- Deterministic execution
- Structured logging
- No out-of-scope features

## Engineering Rules
1. AI plans. Executors execute.
2. Every capability is an Action.
3. ActionPlans are immutable.
4. Execution state is separate.
5. Every executor implements one interface.
6. Every executor receives ActionContext.
7. Every executor returns ActionResult.
8. Configuration lives outside code.
9. Centralized logging.
10. Allow-list application execution.
11. Alias-only folder resolution.
12. Safety before convenience.

## Future Compatibility
LLM planners, voice, memory, plugins and browser automation must integrate without changing the execution engine.
