from typing import Any


class ValidationAgent:
    def validate(self, output: Any) -> dict[str, object]:
        if not isinstance(output, dict) or not output:
            return {"valid": False, "feedback": "Expected a non-empty structured result."}
        operation = output.get("operation")
        required = {
            "meeting_notes": ("summary", "decisions", "action_items"),
            "project_checklist": ("goal", "checklist"),
            "document_extraction": ("fields", "missing_fields"),
            "support_analysis": ("category", "priority", "problem_summary"),
            "text_summary": ("summary",),
        }.get(operation, ())
        missing = [key for key in required if key not in output or output[key] is None]
        if missing:
            return {"valid": False, "feedback": f"Required result fields are missing: {', '.join(missing)}."}
        if any(value is None or value == "" for value in output.values()):
            return {"valid": False, "feedback": "Result contains an empty required value."}
        return {"valid": True, "feedback": "Structured output passed required-field checks."}
