from __future__ import annotations

from dataclasses import dataclass

from tarantino_control.model.next_step import Action, NextStep
from tarantino_control.model.outcome import Outcome


@dataclass(frozen=True)
class StepReport:
    step: NextStep
    outcome: Outcome

    def idle(self) -> bool:
        return self.step.action == Action.IDLE

    def description(self) -> str:
        return f"{self.step.action.name} {self.step.books()}: {self.outcome.detail}"
