# General Codex Instructions

## Tool Execution

Long-running tooling (tests, Docker Compose, migrations, builds, dev servers, etc.)
must always be invoked with sensible timeouts or in non-interactive batch mode.

Never leave a shell command waiting indefinitely.

Prefer:
- explicit timeouts
- non-interactive commands
- scripted runs
- background execution followed by log inspection
- bounded polling when waiting for services

Do not start interactive processes that wait indefinitely for user input.

When running development servers or Docker containers, verify that they started
successfully using logs or health checks instead of waiting on the process forever.