from __future__ import annotations


class TaskMessageGenerationMixin:
    def _prepare_messages(self, system_prompt, user_prompt):
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
