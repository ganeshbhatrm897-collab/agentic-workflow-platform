from typing import Any


class SummarizationAgent:
    def summarize(
        self,
        task: str,
        research: dict[str, Any],
        result: dict[str, Any],
        llm_service: Any | None = None,
    ) -> dict[str, Any]:
        operation = result.get("operation", "text_summary")
        detail = result.get("summary") or result.get("problem_summary") or result.get("goal") or ""
        fallback = (
            f"Workflow result — {operation.replace('_', ' ').title()}\n\n"
            f"{detail}\n\n"
            "Evidence: generated from the text supplied in this request. "
            "Research was simulated locally; no live external sources were consulted. "
            "Assumptions and recommendations are suggestions, not verified facts."
        )
        if llm_service is not None and llm_service.configured:
            prompt = (
                "Write a concise report using only the supplied task and structured result. "
                "Do not add facts, do not imply live research, and label suggestions as suggestions.\n"
                f"Task: {task[:4000]}\nStructured result: {str(result)[:8000]}"
            )
            try:
                candidate = llm_service.complete(prompt)
                generated = candidate.strip() if isinstance(candidate, str) else ""
                if generated and len(generated) <= 8_000:
                    return {"summary": generated, "llm_used": True}
            except RuntimeError:
                pass
            return {"summary": fallback, "llm_used": False, "fallback": True}
        return {"summary": fallback, "llm_used": False}
