from app.models import Scenario


class ResearchAgent:
    def analyze(self, task: str, scenario: Scenario | None) -> dict[str, object]:
        return {
            "source": "user-supplied task text",
            "findings": [task[:500]],
            "assumptions": ["Only information present in the request is treated as evidence."],
            "limitations": ["No live web search or external data sources were used."],
            "simulated": True,
            "scenario": scenario.value if scenario else "general",
        }
