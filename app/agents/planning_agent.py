from app.models import PlanStep, Scenario


class PlanningAgent:
    def create_plan(self, task: str, scenario: Scenario | None) -> list[PlanStep]:
        operation = scenario.value if scenario else "general"
        return [
            PlanStep(
                id="research", agent_id="research",
                description="Review the supplied task context and identify assumptions.",
                expected_output="Findings, assumptions, and limitations.",
            ),
            PlanStep(
                id="execute", agent_id="execution",
                description=f"Apply the safe {operation} workflow to the supplied text.",
                dependencies=["research"],
                expected_output="A structured result grounded in the task input.",
            ),
            PlanStep(
                id="validate", agent_id="validation",
                description="Check the generated result for required fields and unsupported claims.",
                dependencies=["execute"],
                expected_output="Validation status and actionable feedback.",
            ),
            PlanStep(
                id="summarize", agent_id="summarization",
                description="Present the result with evidence and limitations clearly labeled.",
                dependencies=["validate"],
                expected_output="A readable final report.",
            ),
        ]
