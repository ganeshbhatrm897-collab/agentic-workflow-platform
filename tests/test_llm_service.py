import pytest

from app.agents.summarization_agent import SummarizationAgent
from app.config import Settings
from app.services.llm_service import LLMService


def test_llm_service_requires_complete_backend_configuration():
    service = LLMService(Settings())
    assert service.configured is False
    with pytest.raises(RuntimeError, match="not configured"):
        service.complete("A safe prompt")


def test_unconfigured_provider_keeps_summary_deterministic():
    output = SummarizationAgent().summarize(
        "A supplied task",
        {"simulated": True},
        {"operation": "text_summary", "summary": "Supplied text."},
        LLMService(Settings()),
    )
    assert output["llm_used"] is False
    assert "Supplied text." in output["summary"]


def test_configured_provider_failure_falls_back_without_leaking_details():
    class FailingProvider:
        configured = True

        def complete(self, prompt):
            raise RuntimeError("private provider details")

    output = SummarizationAgent().summarize(
        "A supplied task",
        {"simulated": True},
        {"operation": "text_summary", "summary": "Supplied text."},
        FailingProvider(),
    )
    assert output["llm_used"] is False
    assert output["fallback"] is True
    assert "Supplied text." in output["summary"]
    assert "private provider details" not in str(output)


def test_successful_provider_summary_is_labeled():
    class SuccessfulProvider:
        configured = True

        def complete(self, prompt):
            assert "Structured result" in prompt
            return "Report based on supplied evidence."

    output = SummarizationAgent().summarize(
        "A supplied task",
        {},
        {"operation": "text_summary", "summary": "Supplied text."},
        SuccessfulProvider(),
    )
    assert output == {"summary": "Report based on supplied evidence.", "llm_used": True}


@pytest.mark.parametrize("invalid_output", ["", "x" * 8_001, None])
def test_invalid_provider_output_falls_back(invalid_output):
    class InvalidProvider:
        configured = True

        def complete(self, prompt):
            return invalid_output

    output = SummarizationAgent().summarize(
        "A supplied task",
        {},
        {"operation": "text_summary", "summary": "Supplied text."},
        InvalidProvider(),
    )
    assert output["llm_used"] is False
    assert output["fallback"] is True
    assert "Supplied text." in output["summary"]
