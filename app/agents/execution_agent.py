import re

from app.models import Scenario


class ExecutionAgent:
    def execute(self, task: str, scenario: Scenario | None) -> dict[str, object]:
        scenario = scenario or self._infer_scenario(task)
        if scenario == Scenario.meeting:
            result = self._meeting(task)
        elif scenario == Scenario.project:
            result = self._project(task)
        elif scenario == Scenario.document:
            result = self._document(task)
        elif scenario == Scenario.support:
            result = self._support(task)
        else:
            result = {"summary": self._summary(task), "operation": "text_summary"}
        return result

    @staticmethod
    def _infer_scenario(task: str) -> Scenario | None:
        text = task.lower()
        if "meeting" in text or "decisions" in text or "action items" in text:
            return Scenario.meeting
        if "support" in text or "ticket" in text or "customer" in text:
            return Scenario.support
        if "extract" in text or "document" in text or "fields" in text:
            return Scenario.document
        if "project" in text or "milestone" in text or "checklist" in text:
            return Scenario.project
        return None

    @staticmethod
    def _source_text(task: str) -> str:
        for marker in ("Notes:", "Text:", "Request:", "Goal:"):
            if marker in task:
                return task.split(marker, 1)[1].strip()
        return task

    @staticmethod
    def _meeting(task: str) -> dict[str, object]:
        source = ExecutionAgent._source_text(task)
        lines = [line.strip(" -*\t") for line in source.splitlines() if line.strip()]
        decisions = [line for line in lines if re.search(r"\b(decided|decision|agreed|approved)\b", line, re.I)]
        actions = [line for line in lines if re.search(r"\b(action|will|owner|assigned|follow up)\b", line, re.I)]
        summary = " ".join(lines[:3])[:700] or "No meeting notes were supplied."
        return {
            "operation": "meeting_notes",
            "summary": summary,
            "decisions": decisions[:10],
            "action_items": actions[:10],
            "owners": sorted(set(re.findall(r"\b(?:owner|assigned to)\s*:\s*([A-Z][\w -]{0,40})", source, re.I))),
        }

    @staticmethod
    def _project(task: str) -> dict[str, object]:
        source = ExecutionAgent._source_text(task)
        milestones = [
            {"priority": "High", "milestone": "Define scope and success criteria"},
            {"priority": "High", "milestone": "Complete the first working version"},
            {"priority": "Medium", "milestone": "Test with representative users and refine"},
            {"priority": "Medium", "milestone": "Prepare launch and review outcomes"},
        ]
        return {
            "operation": "project_checklist",
            "goal": source[:500] or "Define a project goal.",
            "checklist": milestones,
            "note": "Priorities are suggested planning guidance, not commitments.",
        }

    @staticmethod
    def _document(task: str) -> dict[str, object]:
        source = ExecutionAgent._source_text(task)
        patterns = {
            "email": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            "date": r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b",
            "phone": r"\b(?:\+?\d[\d ()-]{7,}\d)\b",
        }
        fields = {name: re.findall(pattern, source, re.I) for name, pattern in patterns.items()}
        fields["name"] = re.findall(r"\b(?:name|contact)\s*:\s*([^\n,;]+)", source, re.I)
        fields["organization"] = re.findall(r"\b(?:company|organization)\s*:\s*([^\n,;]+)", source, re.I)
        return {
            "operation": "document_extraction",
            "fields": {key: values or None for key, values in fields.items()},
            "missing_fields": [key for key, values in fields.items() if not values],
            "note": "Missing values are returned as null; no fields were inferred.",
        }

    @staticmethod
    def _support(task: str) -> dict[str, object]:
        source = ExecutionAgent._source_text(task)
        text = source.lower()
        category, priority = "general", "normal"
        if any(word in text for word in ("billing", "invoice", "charged", "payment")):
            category = "billing"
        elif any(word in text for word in ("login", "password", "sign in", "account")):
            category = "account access"
        elif any(word in text for word in ("bug", "error", "crash", "broken")):
            category = "technical issue"
        if any(word in text for word in ("urgent", "cannot access", "outage", "blocked")):
            priority = "high"
        return {
            "operation": "support_analysis",
            "category": category,
            "priority": priority,
            "problem_summary": source[:600],
            "recommended_next_steps": [
                "Acknowledge the reported issue and confirm relevant details.",
                "Check the appropriate account, billing, or technical records.",
                "Share a clear update and next action with the requester.",
            ],
            "note": "Classification is an automated suggestion based only on supplied text.",
        }

    @staticmethod
    def _summary(task: str) -> str:
        text = ExecutionAgent._source_text(task)
        return text[:600] + ("…" if len(text) > 600 else "")
