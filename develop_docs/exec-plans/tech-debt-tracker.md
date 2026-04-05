# Tech Debt Tracker

## Open

- Add a real test suite for `video_utils.py` and `canonical_atlas_agent.py`.
- Replace shell `echo` file writes with safer file-writing helpers.
- Harden workspace command construction against quoting issues in generated text.
- Decide whether compiled `__pycache__` files should be ignored or purged from the repository.

## Rules

- Put planned debt work in `exec-plans/active/`.
- Move completed work summaries into `exec-plans/completed/`.
