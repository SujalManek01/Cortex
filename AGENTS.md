# AGENTS.md

# Cortex Development Rules

- Always read the current Sprint specification before making changes.
- Always read implementation_plan.md before implementation.
- Make routine engineering decisions independently.
- Only ask for approval when a decision would fundamentally change Cortex's architecture.
- Implement milestone-by-milestone.
- Write tests alongside implementation, never afterward.
- Run regression tests after every milestone.
- Maintain backward compatibility unless the Sprint explicitly permits breaking changes.
- Keep the architecture deterministic.
- Never bypass Validator, Safety Policy, or the Execution Engine.
- Update walkthrough.md, release_summary.md, and task.md before declaring a sprint complete.


## Cortex Engineering Rules

This repository is developed sprint-by-sprint using engineering specifications located in:

docs/specifications/

Every implementation MUST follow the active sprint specification.

## Core Principles

- Never bypass the Execution Engine.
- Every desktop action must be represented as a capability.
- Prefer adding capabilities instead of modifying the engine.
- Use constructor dependency injection.
- One responsibility per class.
- Follow SOLID principles where appropriate.
- Use structured logging.
- Avoid global mutable state.

## Development Workflow

Specification
→ Engineering Review
→ Implementation Plan
→ Implementation
→ Tests
→ Manual Verification
→ Git Commit
→ Git Tag

Every milestone must leave the project in a buildable state.

## Testing

All new functionality requires:

- Unit tests
- Integration tests
- Manual verification where applicable

No implementation is complete until tests pass.

## Scope Discipline

Do not implement features outside the active sprint.

If an improvement is discovered during implementation:

- implement it only if it reduces technical debt **without expanding sprint scope**
- otherwise document it for a future sprint

## Code Quality

- Keep files focused on a single responsibility.
- Avoid unnecessary abstractions.
- Prefer readability over cleverness.
- Use explicit error handling.
- Do not silently ignore failures.

## Architecture

The execution pipeline is:

Planner
→ Validator
→ Safety Policy
→ Execution Engine
→ Capability Registry
→ Executor
→ Windows

This architecture must not be bypassed.

## Documentation

Update documentation whenever architecture or public APIs change.

Do not change sprint specifications without explicit approval.