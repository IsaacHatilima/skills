---
name: feature-verification
description: Verify a feature or review its evidence against acceptance criteria, package checks, and the scope actually exercised.
---

# Verify what the feature does

Use the invoking workflow's acceptance criteria, test targets, or review scope as the evidence map. For each criterion, record the relevant check, observed result, package, and any limit. Existing tests may provide evidence; add focused behavioural coverage where a changed behaviour needs it. Avoid tests that merely match implementation wording.

## Checks

- Run the checks required by the invoking workflow and project for the requested scope. Implementation verification may include focused tests, type checks, build, and changed-file lint; an E2E or security-only workflow uses its assigned checks and prerequisites. Respect project rules for serial suites and shared databases. Do not broaden a focused check into a repository-wide autofix.

- Exercise allowed and refused cases for server permissions in scope, including record ownership or tenant scope. A mocked UI test establishes UI behaviour, not API enforcement. Add or change tests only when the workflow assigns that work.

- For a UI criterion, distinguish source inspection, component tests, and actual browser interaction. Test the states and roles the criterion requires. A screenshot of an anonymous page does not establish an authenticated flow.

- When the project's verification environment permits browser writes, use its documented test accounts and disposable data. Otherwise record the missing runtime evidence without claiming the interaction succeeded.

- If a required check fails or cannot run, preserve its command and output. Separate an introduced failure from a pre-existing failure or missing prerequisite. None of these is a passing check; apply the agent's verdict/blocking contract.

## Report

State exactly what passed and what remains unverified in the invoking workflow's assigned report. Mark a required criterion complete only when the evidence supports its promised behaviour. Unverified required criteria prevent a completed verification result. Reviewers independently inspect the evidence and repeat the checks their role requires. This skill can run against existing code without a feature-building workflow, spec file, or build report.

Documentation and approval use the same evidence map. Passing lint, a clean diff, or a review verdict is not proof of a database migration, authenticated workflow, deployment, or downstream installation. Do not expand permissions to obtain missing evidence.

