Cortex
An AI operating layer for safe, deterministic desktop actions on
Windows.

Cortex connects a React/TypeScript dashboard to a Python/FastAPI
backend. Its execution pipeline is designed to turn structured action
requests into controlled desktop operations through planning,
validation, safety checks, a capability registry and dedicated
executors.

Current implementation status: Cortex is an actively developed
desktop-automation foundation. The backend currently uses StubPlanner.
It accepts structured capability-and-target steps; it does not yet
understand arbitrary natural-language instructions or operate as a fully
autonomous AI assistant. This README distinguishes implemented
functionality from future plans.
Contents
- Overview
- Current capabilities
- Architecture
- Technology stack
- Repository structure
- Requirements
- Installation
- Running locally
- Configuration
- API reference
- Example request
- Execution lifecycle
- Safety model
- Testing
- Logging and troubleshooting
- Adding a capability
- Limitations
- Roadmap
- Engineering principles
- Contributing
- License
Overview
Cortex aims to provide a safe operating layer between user intent and
local computer actions. Rather than allowing a model or UI component to
execute arbitrary commands, Cortex routes actions through a controlled
backend pipeline.

The current application includes: - A React dashboard for submitting
execution plans and viewing results. - A FastAPI backend that validates
and executes plans. - A planner abstraction, currently implemented by
StubPlanner. - An action registry that maps capability names to
executor implementations. - A validator and safety policy that run
before execution. - Application, folder and website registries populated
from configuration. - Sequential execution, timeouts, structured results
and logging.
Project status
  Area                                Status in current code
  React + TypeScript frontend         Implemented

  FastAPI backend                     Implemented

  Structured execution request        Implemented

  Stub planner                        Implemented

  Free-form natural-language          Not implemented
understanding                       

  Plan validation                     Implemented

  Application allow-list              Implemented

  Folder alias validation             Implemented

  Sequential execution engine         Implemented

  Application open/close              Registered

  Folder open                         Registered

  Website open                        Registered

  Structured API errors and results   Implemented

  Voice, memory, plugins, cloud sync  Not implemented in current scope
LLM-backed autonomous planner       Future work
The backend application currently declares version 0.1.0. Sprint
specifications under docs/specifications/ describe architecture and
intended direction; a specification is not proof that every described
feature has shipped.
Current capabilities
The backend registers these action names:
  Capability              Function                Target
  application.open      Launch an approved      Application alias
application             

  application.close     Close an approved       Application alias
application             

  folder.open           Open a configured       Folder alias
folder                  
website.open          Open a registered       Website alias
website
Use the metadata endpoints to see what is actually loaded by your local
configuration.

The sample config/apps.json contains aliases for VS Code (vscode),
Chrome (chrome), Edge (edge), Firefox (firefox), Notepad
(notepad), Explorer (explorer), Calculator (calculator), Paint
(paint) and Task Manager (taskmgr). These entries depend on local
installation paths; edit the configuration to match your computer.

The sample config/aliases.json includes desktop, downloads,
documents, pictures, music and chatbot_project. Website aliases
are provided by the website configuration loaded into WebsiteRegistry.
Architecture
React + TypeScript Frontend
            |
         HTTP/JSON
            v
       FastAPI Backend
            |
         Planner
       (StubPlanner)
            |
        ActionPlan
            |
        Validator
            |
       Safety Policy
            |
     Execution Engine
            |
      Action Registry
       /     |      \
      v      v       v
 Application Folder Website
  Executor Executor Executor
       \      |      /
            Windows
               |
      Structured Results
               |
        React Dashboard
Component responsibilities
Frontend: React components collect execution input, show registry
information, display execution state and render results. API
communication is centralized in frontend/src/api/cortexApi.ts. The
frontend does not perform desktop operations directly.

Planner: StubPlanner converts a structured request into an
ActionPlan. It generates the plan UUID, assigns step IDs, sets the
version and records the planner identity. It does not parse free-form
natural language.

ActionPlan and schemas: The plan describes the requested work and
its ordered steps. Execution state and step results are maintained
separately.

Validator: Checks the plan structure, supported version and whether
each requested action is registered.

Safety Policy: Rejects raw filesystem paths, checks application
aliases against the configured allow-list and verifies folder aliases
against configured mappings.

Execution Engine: Runs steps sequentially, dispatches each step
through the registry, applies the configured 30-second per-step timeout
and rejects a concurrent plan while another is running.

Action Registry: Maps domain.verb capability names to executor
objects. The engine does not need a separate action-specific branch for
every capability.

Executors: Each executor implements one operation and returns a
structured result.

Configuration and registries: JSON configuration is loaded at
startup and used to populate application, folder and website registries.
Technology stack
Backend
- Python 3.12+
- FastAPI
- Pydantic
- Uvicorn
- HTTPX
- Pytest and pytest-asyncio
- Ruff
- Mypy
Frontend
- React 18
- TypeScript
- Vite 5
- npm
Platform
- Windows 11 is the target platform in the current core specification.
- Desktop actions depend on local Windows applications, paths and
  configuration.
Repository structure
High-level guide (not every internal file is shown):
Cortex/
├── backend/
│   ├── api/                 # FastAPI routes
│   ├── config/              # Configuration loading
│   ├── engine/              # Execution engine
│   ├── executors/           # Application/folder/website actions
│   ├── logging/             # Structured logging
│   ├── models/              # ActionPlan and execution models
│   ├── planner/             # Planner implementation
│   ├── registry/            # Action and resource registries
│   ├── safety/              # Safety policy
│   ├── schemas/             # API schemas
│   ├── validator/           # Plan validation
│   ├── main.py              # FastAPI entry point and dependency wiring
│   └── requirements.txt
├── config/
│   ├── apps.json            # Application configuration
│   └── aliases.json         # Folder aliases
├── docs/
│   └── specifications/      # Sprint and architecture documents
├── frontend/
│   ├── src/
│   │   ├── api/             # API client
│   │   ├── components/      # Dashboard components
│   │   ├── types/           # TypeScript API contracts
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── start_backend.ps1
│   └── start_frontend.ps1
├── tests/
│   ├── integration/
│   └── conftest.py
└── README.md
Requirements
Install: - Windows 11 - Python 3.12 or newer - Node.js 18 or newer -
npm - Git

Verify:
python --version
node --version
npm --version
git --version
Installation
1. Clone the repository
git clone https://github.com/SujalManek01/Cortex.git
cd Cortex
2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
If PowerShell blocks activation, follow your machine's PowerShell policy
or invoke .venv\Scripts\python.exe directly.
3. Install backend packages
Run from the repository root:
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
4. Install frontend packages
cd frontend
npm install
cd ..
5. Review local configuration
Before running Cortex, inspect config/apps.json, config/aliases.json
and the website configuration used by the repository. Replace
machine-specific paths with valid paths on your computer. Keep only the
applications and folders you intend to allow.
Running locally
Run the backend and frontend in separate PowerShell terminals from the
repository root.
Option A: Included scripts
Terminal 1:
.\scripts\start_backend.ps1
Terminal 2:
.\scripts\start_frontend.ps1
Option B: Manual startup
Backend:
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
Frontend:
cd frontend
npm run dev
Open the frontend at http://localhost:5173.

Backend addresses: - API: http://localhost:8000 - Swagger UI:
http://localhost:8000/docs - ReDoc: http://localhost:8000/redoc -
Health: http://localhost:8000/health

Vite proxies the frontend API paths to the FastAPI backend on port
8000.

Build the frontend:
cd frontend
npm run build
This runs TypeScript checking and the Vite production build.
Configuration
Applications: config/apps.json
An application entry has this general shape:
{
  "name": "Google Chrome",
  "alias": "chrome",
  "executable": "chrome.exe",
  "path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
}
- name: display name.
- alias: identifier used in an execution request.
- executable: executable name.
- path: configured executable path, where applicable.
The checked-in sample includes machine-specific paths. Verify them
locally; a sample path does not guarantee the application exists on
another computer.
Folders: config/aliases.json
Folder operations use registered aliases, for example:
{
  "downloads": "C:\\Users\\YourUser\\Downloads",
  "documents": "C:\\Users\\YourUser\\Documents"
}
The repository sample contains {username} placeholders. Confirm how
the current configuration loader resolves these placeholders or replace
them with valid local paths. Restart the backend after configuration
changes because registries are loaded at startup.

Do not pass raw absolute filesystem paths in execution requests. Use
configured aliases.
Websites
Website entries are loaded into WebsiteRegistry. Use GET /websites
to inspect the aliases currently available. Follow the website
configuration schema in the repository when adding or changing entries.
API reference
  Method   Route             Purpose
  POST   /execute        Validate and execute a structured plan
GET    /status         Return engine busy/idle state
GET    /health         Liveness check
GET    /applications   List configured applications
GET    /folders        List configured folder aliases
GET    /websites       List registered website aliases
GET    /capabilities   List registered actions
GET /health
{
  "status": "ok"
}
This confirms that the API process responds. It does not verify that
every configured application can launch.
GET /status
{
  "busy": false,
  "status": "idle"
}
GET /capabilities
Example shape (the actual list comes from registered executors):
{
  "capabilities": [
    "application.close",
    "application.open",
    "folder.open",
    "website.open"
  ]
}
The other metadata endpoints return arrays of the resources loaded by
the local registries. Use /docs for the exact live response schemas.
Example request
The current backend expects a structured plan, not a plain
natural-language sentence.

Request to open the registered Chrome alias:
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
PowerShell example:
$body = @{
    version = "1.0"
    plan = @{
        steps = @(
            @{
                capability = "application.open"
                target = "chrome"
            }
        )
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://localhost:8000/execute" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
A multi-step plan can include multiple registered actions:
{
  "version": "1.0",
  "plan": {
    "steps": [
      {"capability": "application.open", "target": "chrome"},
      {"capability": "application.open", "target": "vscode"},
      {"capability": "folder.open", "target": "downloads"}
    ]
  }
}
Every action and target must be registered and pass validation and
safety checks. Steps execute sequentially.

The response includes an execution identifier, overall status, duration,
a summary of successful/failed/total steps and per-step results. Use
/docs as the authoritative contract for the current checked-out
version.
Execution lifecycle
HTTP request
    |
    v
Build ActionPlan
    |
    v
Validate schema/version/action
    |
    v
Enforce safety policy
    |
    v
Execution engine
    |
    v
Sequential executor dispatch
    |
    v
Collect results and summary
    |
    v
HTTP response
Important HTTP error categories:

  Status   Meaning
  400    Invalid plan or unsupported action
403    Safety policy rejected the request
409    Another execution is already running
500    Unexpected backend error

The execution engine is designed for sequential execution and stops the
plan on failure, as described in the core execution specification.
Safety model
Current safeguards include:
1. Application allow-list: application actions must use a
   registered alias.
2. Folder alias validation: folder actions must use a configured
   alias.
3. Raw-path rejection: raw absolute filesystem paths are rejected.
4. Registered actions only: unsupported capabilities are rejected
   by validation/registry checks.
5. Validation before execution: plans are checked before dispatch.
6. Single active plan: concurrent execution is rejected.
7. Per-step timeout: the backend configures a 30-second timeout per
   step.
These safeguards are not a complete operating-system sandbox. Cortex is
a local development project. Do not expose the backend to untrusted
networks, do not add untrusted executables to the allow-list, and review
all configuration changes.

The current API does not implement user authentication. Keep the
development backend bound to localhost unless suitable access controls
have been deliberately implemented and reviewed.
Testing
Backend tests use Pytest, pytest-asyncio and HTTPX.

Run the suite from the repository root:
python -m pytest
Run selected integration tests:
python -m pytest tests/integration/test_api_execute.py -v
python -m pytest tests/integration/test_api_metadata.py -v
The tests cover health/status endpoints, successful execution, generated
execution IDs, invalid actions, safety violations, raw-path rejection,
unknown aliases, concurrency behavior and metadata endpoints.
Integration tests use an ASGI test client; OS side effects are mocked
where appropriate.

Some acceptance tests launch real Windows applications. They are marked
separately and excluded from the default run by the repository's pytest
configuration. Review tests/integration/test_acceptance.py before
running them on a Windows machine.
Logging and troubleshooting
The backend initializes a structured logger and writes to:
logs/cortex.log
It also echoes log output to the backend terminal.

When something fails:
1. Confirm the backend starts without import or configuration errors.
2. Check terminal output and logs/cortex.log.
3. Request GET /health.
4. Request GET /capabilities and confirm the action exists.
5. Check /applications, /folders or /websites for the target
   alias.
6. Verify local paths and configuration.
7. Inspect the structured error returned by /execute.
Do not publish diagnostic logs without checking for personal filesystem
paths or other machine-specific information.
Adding a capability
The registry architecture is intended to make capabilities extensible
without adding action-specific logic to the execution engine.
1. Choose a domain.verb capability name.
2. Implement an executor using the existing base-executor interface.
3. Validate and normalize the executor's parameters.
4. Add the required safety checks and configuration.
5. Register the executor during startup in backend/main.py.
6. Add unit and integration tests for success and failure cases.
7. Update the API contract and documentation.
Executors are registered in startup wiring using the action registry,
for example:
registry.register(MyNewExecutor())
Follow the constructor and return-value conventions of the existing
executors in backend/executors/. Never bypass validation, safety or
registry dispatch to make a capability work.
Limitations
- StubPlanner does not understand free-form natural language.
- The API expects structured capability/target steps.
- Windows 11 is the target platform; support for other operating
  systems is not established.
- Application launching depends on local installation and correct
  configuration.
- Folder actions depend on configured aliases.
- Website opening uses registered website entries, not unrestricted
  browser automation.
- Authentication and multi-user authorization are not part of the
  current implementation.
- Voice, memory, plugins, cloud synchronization and autonomous LLM
  workflows are not implemented in the current scope.
- A healthy API response does not guarantee every configured desktop
  action will work.
Roadmap
The project specifications describe future directions. Treat these as
planned capabilities until implemented and tested:
- Natural-language parsing and structured plan generation.
- LLM-backed planner integration through the planner abstraction.
- Workspace and multi-application automation.
- Controlled browser automation.
- Vision and OCR capabilities.
- Mouse and keyboard automation.
- A capability/plugin extension system.
- Voice interaction.
- User-approved memory and workflow context.
- More advanced autonomous workflows with visibility and safety
  controls.
Future intelligence must continue to operate through the same
validation, safety and execution boundaries. A model should propose a
plan, not receive unrestricted access to the operating system.
Engineering principles
1. AI plans; executors execute.
2. Every capability is an action using the domain.verb naming
   convention.
3. Plans and execution state are separate.
4. Each executor has one responsibility.
5. The registry owns dispatch; the engine stays generic.
6. Configuration stays outside business logic.
7. Validation and safety happen before execution.
8. Errors remain structured and observable.
9. Safe defaults take priority over convenience.
Contributing
Contributions should preserve the architecture and safety boundaries.
- Keep modules focused on one responsibility.
- Follow existing executor and registry interfaces.
- Avoid hard-coded machine-specific paths in business logic.
- Add tests for new capabilities and failure paths.
- Keep Python API schemas and TypeScript types synchronized.
- Update relevant specifications and documentation.
- Run backend tests and the frontend production build.
- Do not describe a capability as supported until it is implemented
  and tested.
A useful pull request explains what changed, why it changed, how it was
tested and whether configuration changes are needed.
License
No LICENSE file was confirmed in the repository files reviewed for
this README. Until a license is added, do not assume that others have
permission to redistribute, modify or use the project.
Repository
GitHub: https://github.com/SujalManek01/Cortex\
Default branch: main

Cortex is a work in progress. APIs, configuration and capabilities may
evolve as the execution foundation develops.
