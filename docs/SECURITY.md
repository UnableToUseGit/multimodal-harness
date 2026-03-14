# Security

## Key Risks

- `LocalWorkspace` executes shell commands locally.
- Video and subtitle inputs may contain untrusted filenames or content.
- Generated text may be written into shell-driven commands.

## Rules

- avoid broad shell interpolation
- review new workspace writes carefully
- keep secrets and local media out of version control
- prefer explicit escaping and safer file write paths where possible
