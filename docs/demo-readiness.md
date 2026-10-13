# Functional work and demo recording handoff

Each project is recorded from its tested code commit, after its functional work
is complete. Recheck the commit when recording begins; changes after a test run
invalidate that recording handoff.

The functional owner supplies:

- Repository, branch, full commit SHA, and PR link.
- A reproducible install/start/reset command and prerequisites.
- Verification commands and their actual exit statuses. Separate unit tests,
  contract tests, frontend builds, and live end-to-end checks.
- A complete core workflow with its expected result and persistence behavior.
- Known unfinished features, simulated data, hardware requirements, external
  credentials, and checks that could not run.

The media owner confirms the working tree matches that commit before filming.
Use local or seeded data for demos. Label mock/paper/replay output where it is
shown, and demonstrate the actual interface for projects with a frontend.
Verify the finished GIF/video represents the tested workflow and link it from
the project's README after that verification.

Empty repositories and historical coursework are tracked separately from
runnable applications. A visual concept is not proof that a product exists.
Failed tests or unimplemented advertised functionality keep that workflow on
hold until the code is fixed and retested. Partial test coverage only authorizes
the specific verified lane, not an untested cloud, hardware, or live API lane.

`scripts/ecosystem-smoke.sh` now fails while live cross-product scenario
execution is unwired. The pipeline correction is coordinated in
[PR #4](https://github.com/jadenfix/ecosystem/pull/4).
`run-ecosystem-e2e.py --list` remains an inventory command.
Neither a scenario list nor metadata checks establish end-to-end readiness.
