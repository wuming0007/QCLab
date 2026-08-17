# QCLab / QXtrl Agent Orientation

**Purpose**: Keep future agents and contributors oriented across sessions. Update this file whenever repo structure, major conventions, build commands, architecture authority, or workflow rules change.

This file is public-safe project context. Do not put credentials, private URLs, personal information, non-public customer/lab details, or sensitive security findings here. Put local-only context in `AGENTS.private.md`, which is gitignored.

## 1. Project Snapshot

QCLab is the current working repository for two related tracks:

1. Legacy / reference superconducting quantum measurement-control materials, including QuarkStudio setup, drivers, example experiments, notebooks, device docs, and configuration examples.
2. QXtrl planning materials for a future independently controlled, commercially deliverable quantum measurement-control and automatic calibration platform.

The active strategic direction is QXtrl. Treat legacy code and QuarkStudio examples as reference material unless a task explicitly asks to modify them.

## 2. High-Value File Map

| Path | Role |
| --- | --- |
| `docs/planning/` | Main QXtrl planning workspace and current architecture documents |
| `qxtrl/` | New QXtrl product source trunk (L0+ using short codes: cc, el, ...). Start of independent contracts/runtime (legacy `home/` is reference only). Layers use short codes for packages: cc (L0), el (L1), etc. |
| `docs/planning/QXtrl量子测控软件开发需求.md` | Current PRD, v0.4 discussion draft |
| `docs/planning/QXtrl_架构层号与文档索引.md` | Authority for L0-L9 layer numbering and document ownership |
| `docs/planning/QXtrl模块拆解与接口责任矩阵.md` | Module responsibilities and interface matrix |
| `docs/planning/QXtrl_MVP最薄垂直切片定义.md` | MVP thin vertical slice definition |
| `docs/planning/QXtrl_L1_API说明.md` | Current L1 / EL Python API reference |
| `docs/planning/QXtrl_L2_CPIR_Compiler_PulseIR_设计.md` | Current L2 / CPIR Compiler & PulseIR design entry |
| `docs/planning/QXtrl_L2_API说明.md` | Current L2 / CPIR Python API reference |
| `docs/planning/QXtrl_L3_EB_ExecutionBackend_设计.md` | Current L3 / EB Execution Backend design entry |
| `docs/planning/QXtrl_L3_API说明.md` | Current L3 / EB Python API reference |
| `docs/planning/QXtrl_L4_RS_RuntimeScheduler_设计.md` | Current L4 / RS Runtime & Scheduler design entry |
| `docs/planning/QXtrl_L5_DS_DataState_设计.md` | Current L5 / DS Data & State design entry |
| `docs/planning/QXtrl_L7_TRH_TwinReplayHIL_设计.md` | Current L7 / TRH Twin / Replay / HIL design entry |
| `docs/planning/QXtrl_L9_OI_OperatorInterfaces_设计.md` | Current L9 / OI Operator Interfaces design entry; MVP focuses on thin Python SDK + CLI |
| `docs/planning/QXtrl_第一次讨论会决策清单.md` | First architecture discussion decision list |
| `docs/planning/HANDOFF_TEMPLATE.md` | Session/agent handoff template + usage guide for seamless context transfer across token quota switches, forks, and new sessions |
| `quarkstudio_docs/` | Locally downloaded QuarkStudio documentation |
| `home/` | QuarkStudio-style runtime home: configs, drivers, gates, run examples |
| `home/cfg/` | QuarkStudio configuration examples |
| `home/dev/` | Legacy/reference instrument drivers |
| `home/run/` | Experiment scripts such as S21 examples |
| `quark_configurator/` | PySide6 configuration UI prototype |
| `V5_docs/` | Chip/device design and calibration reference materials |
| `notebooks/` | Notebook-based experiments and reports |
| `CHANGELOG.md` | Project change history and rationale |
| `template.md` | In-repo replication guide for QXtrl-style architecture/design work |
| `qxtrl/cc/` | L0 / CC (Core Contracts) implementation |
| `qxtrl/el/` | L1 / EL (Experiment Language) implementation (MVP started per design doc) |
| `qxtrl/cpir/` | L2 / CPIR (Compiler / Pulse IR) implementation prototype |
| `qxtrl/eb/` | L3 / EB (Execution Backend) implementation prototype |
| `qxtrl/rs/` | L4 / RS (Runtime & Scheduler) implementation prototype |
| `qxtrl/ds/` | L5 / DS (Data & State) minimal manifest implementation and future ResultStore/DataSink trunk |
| `qxtrl/trh/` | L7 / TRH (Twin / Replay / HIL) virtual runner prototype |
| `qxtrl/viz/` | Publication chip topology maps (L9-facing helper, not a new layer). Circles = qubits, squares = couplers; colour is bound to a metric keyword. User guide: `qxtrl/viz/README.md`. |

## 3. Architecture Authority

Use stable names first and layer numbers second. Current authoritative layer map:

| Layer | Stable Name | Main Responsibility |
| --- | --- | --- |
| L0 | Core Contracts | Schema, units, names, versions, safety policy, errors, governance discipline |
| L1 | Experiment Language | `ExperimentSpec`, Atom/Task/Session, recursive PDCA intent |
| L2 | Compiler / Pulse IR | `PulseIR`, frame events, delayed binding, compiled bundles |
| L3 | Execution Backend | Real, virtual, replay, HIL, and instrument backends |
| L4 | Runtime & Scheduler | Run lifecycle, queue, resources, cancellation, retries, events |
| L5 | Data & State | `ConfigStore`, `ResultStore`, `DataSink`, `RunManifest` |
| L6 | Calibration & Optimization | Calibration DAG, observations, patch proposals, records, blackboard |
| L7 | Twin / Replay / HIL | Virtual QPU/instrument, replay backend, digital twin stages |
| L8 | AI & Diagnostics Gateway | Action proposals, policy gates, diagnosis knowledge base |
| L9 | Operator Interfaces | CLI, SDK, Web console, diagnostics, delivery tools |

Product view:

1. Contract Discipline is cross-cutting.
2. Execution Backend is the bottom execution foundation.
3. Runtime & Middleware owns parsing, scheduling, compiling, state, calibration, twin, and AI safety entry.
4. Frontend Workbench owns user interaction, visualization, parameter review, waveform review, diagnostics, and delivery UI.

## 4. Current Design Commitments

Preserve these unless the user explicitly asks to revisit them:

1. QXtrl should become an independent product trunk with controlled IP/source boundaries.
2. L0 contract discipline applies to every layer.
3. Experiment intent should be structured and typed; avoid hiding semantics in ad hoc scripts.
4. Final waveform arrays should be produced at compile/render boundaries, not embedded directly in high-level experiment specs.
5. `ConfigStore`, `ResultStore`, and `DataSink` are separate responsibilities.
6. Automatic calibration should generate candidate `ParameterPatchProposal` / `CalibrationRecord`; it should not directly write active config.
7. AI should submit constrained `ActionProposal` or diagnostics, not raw device commands.
8. Virtual QPU / VirtualInstrument / Replay / Twin should consume the same contracts as real execution where feasible.
9. MVP should stay thin: Rabi is the required demo path; S21 is optional enhancement.
10. Historical L2/L3 docs have layer-number drift. Check `QXtrl_架构层号与文档索引.md` before renaming or extending them.
11. Schema version prefixes use implementation short codes where defined, e.g. `qxtrl.cc.*` for L0/Core Contracts and `qxtrl.el.*` for L1/Experiment Language. Cross-layer data `kind` values may still use layer semantic labels such as `l0_snapshot`; do not confuse those with Python package names.

## 5. Development And Documentation Workflow (Evolving Context Workflow)

This project follows a lightweight **evolvable context workflow** (originally inspired by "An Evolving Context Workflow"). The goal is to give agents and humans a reliable "map" so they can orient quickly without re-reading everything.

### 5.1 Core Rules (always follow these)

1. **Read this `AGENTS.md` first** before any significant work. It is the single current source of orientation, file map, architecture authority, and operational rules.
2. Use `template.md` when creating a new module design, API contract, planning document, or architecture pattern.
3. Update `AGENTS.md` when repo structure, conventions, build commands, architecture authority, or workflow rules change.
4. Update `template.md` when a project pattern becomes reusable beyond a single document.
5. Update `CHANGELOG.md` for significant project changes, especially new architecture decisions, generated artifacts, or workflow changes.
6. For private lab details, local credentials, private endpoints, or personal notes, use `AGENTS.private.md`; do not commit it.
7. When adding or renaming planning documents, update the relevant index (`QXtrl_架构层号与文档索引.md` or this file) if ownership or authority changes.

### 5.2 Daily Usage (start of task)

1. Read `AGENTS.md` to confirm current architecture conventions and the High-Value File Map.
2. For module design, interface definition, or architecture documents, reference `template.md`.
3. For layer numbering or document ownership, use `docs/planning/QXtrl_架构层号与文档索引.md` as authority.

### 5.3 After Important Changes (maintenance checklist)

Check these three things:

1. Does `AGENTS.md` need updating (directories, commands, architecture authority, workflow rules, gotchas)?
2. Does `template.md` need updating (new reusable pattern or checklist)?
3. Does `CHANGELOG.md` need an entry (new document, architecture decision, interface draft, or workflow change)?

### 5.4 Private Information Handling

Never write the following into `AGENTS.md` or other committed files:

- Passwords, tokens, keys, certificates.
- Internal URLs, VPNs, private service addresses.
- Non-public customer, lab station, chip batch, or personnel information.
- Specific security vulnerability or mitigation details.
- Third-party / previous employer material not confirmed public.

Such information belongs in `AGENTS.private.md` (gitignored) or a company-controlled knowledge base.

### 5.5 Evolvable Context Maintenance Layers

These four (plus `template.md`) work together as a layered system so context remains usable across long sessions, agent switches, and time:

| Layer | File | Role (current operational) |
|-------|------|----------------------------|
| Orientation | `AGENTS.md` (root) | The living map. Read first every time. Contains snapshot, authority, rules, and current workflow. |
| Rationale & History | `docs/planning/QXtrl_项目上下文工作流.md` | Records why the workflow was adopted (2026-06-07), adaptation decisions, and evolution notes. Not the daily checklist. |
| Event Log | `CHANGELOG.md` (root) | Chronological compressed history of what changed and why. |
| Cross-session Continuity | `docs/planning/HANDOFF_TEMPLATE.md` | Template + guide for producing state snapshots when switching agents/sessions due to quotas, compaction, or parallel work. Use before `/compact`, `/fork`, or long breaks. |
| Reusable Patterns | `template.md` (root) | Document shape, checklists, and patterns for new architecture/API/planning work. |

See `docs/planning/QXtrl_项目上下文工作流.md` for the original design rationale and adoption reasoning. The workflow is intentionally evolvable — add or adjust layers (e.g. HANDOFF) when new friction appears.

### 5.6 Future Enhancements (when the project matures)

| Phase | Suggestion |
|-------|------------|
| Architecture discussion | Manual maintenance of `AGENTS.md`, `template.md`, `CHANGELOG.md`, and handoff files is sufficient. |
| MVP development | Consider light post-commit or pre-push reminders to update context files. |
| Multi-person collaboration | Add checklist item in PR template: "Did you update AGENTS / template / CHANGELOG / handoff as needed?" |
| Commercial delivery | Include context hygiene in release checklists. |

## 6. Working Rules For Agents

1. Prefer `rg` / `rg --files` for search.
2. Keep edits scoped to the user's request.
3. Do not revert user changes in a dirty worktree.
4. For important planning documents, preserve earlier versions unless the user asks to overwrite.
5. For review requests, give findings first, then summary.
6. For document artifacts requested by the user, create the file, not just chat text.
7. For QuarkStudio/QXtrl interface work, separate observed APIs from inferred or proposed contracts.
8. For public-safe project context, scan for secrets and private details before committing.

## 7. Known Commands And Checks

These commands appear in project guides; verify them in the current environment before relying on them for release evidence.

| Purpose | Command |
| --- | --- |
| Initialize QuarkStudio local files | `uv run quark init` |
| Start QuarkServer | `uv run quark server` |
| Run Quark Configurator UI | `uv run python quark_configurator/main.py` |
| Search files | `rg --files` |
| Search content | `rg "pattern"` |
| Run L0/CC tests (MVP) | `PYTHONPATH=. python3 -m pytest qxtrl/cc/tests/ -q` |
| Run L1/EL tests (MVP) | `PYTHONPATH=. python3 -m pytest qxtrl/el/tests/ -q` (when added). See short codes in 架构层号与文档索引.md. |
| Run L2/CPIR tests (MVP) | `PYTHONPATH=. python3 -m pytest qxtrl/cpir/tests/ -q` |
| Run L5/DS tests (MVP) | `PYTHONPATH=. python3 -m pytest qxtrl/ds/tests/ -q` |
| Run L7/TRH tests (MVP) | `PYTHONPATH=. python3 -m pytest qxtrl/trh/tests/ -q` |
| Run topology-map tests | `PYTHONPATH=. python3 -m pytest qxtrl/viz/tests/ -q` |
| Render Willow topology figure | `PYTHONPATH=. python3 -m qxtrl.viz --qubit-metric t1 --coupler-metric cz_fidelity --out figures/chip_topology/willow105` |
| Chip topology map user guide | `qxtrl/viz/README.md` |

For documentation-only changes, structural checks such as heading search, link inspection, and code-block closure checks are usually enough.

## 8. Gotchas

1. The worktree is often dirty with many historical or generated files. Check target-file status before editing.
2. Chinese filenames are common; use exact paths and quote shell arguments when needed.
3. Some docs and generated artifacts may be untracked even though they are important to the planning workflow.
4. QuarkStudio parameter paths currently appear in more than one style, such as `gate.Measure.Q0.params.frequency` and `Q0.Measure.frequency`; do not assume they are equivalent without an explicit mapping.
5. DOCX render QA may fail in some environments because LibreOffice headless rendering can crash; disclose structural-only QA if that happens.
6. `qxtrl.viz.willow105_layout()` uses the public Cirq Willow105 occupancy. Per-site colours are illustrative samples from published Chip-1 aggregates, not a measured Google device map, and must not be used for control.
