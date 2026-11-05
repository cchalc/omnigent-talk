import pytest

from omnigent_talk import router
from omnigent_talk.gateway import Reply


class FakeGateway:
    """Answers the classifier with `label`; records every call."""

    def __init__(self, label: str | Exception = "general") -> None:
        self.label = label
        self.calls: list[tuple[str, dict[str, str] | None]] = []

    def chat(self, service, messages, *, tags=None, max_tokens=1024):
        self.calls.append((service, tags))
        if service.endswith(router.CLASSIFIER):
            if isinstance(self.label, Exception):
                raise self.label
            return Reply(200, service, self.label, None)
        return Reply(200, service, "answer", None)


@pytest.mark.parametrize(
    ("answer", "label"),
    [("SQL.", "sql"), ("  code\n", "code"), ("General", "general"), ("dunno", None)],
)
def test_parse_label(answer, label):
    assert router.parse_label(answer) == label


@pytest.mark.parametrize(
    ("label", "service"),
    [("sql", "qwen_code"), ("code", "qwen_code"), ("general", "gemini_general")],
)
def test_ask_sends_the_prompt_to_its_route_and_tags_the_decision(label, service):
    gw = FakeGateway(label)
    r = router.ask(gw, "anything")
    assert (r.route, r.classifier, r.service) == (label, router.CLASSIFIER, service)
    assert r.model == router.SERVICE_MODELS[service]
    (classify_service, classify_tags), (answer_service, answer_tags) = gw.calls
    assert classify_service == router.CLASSIFIER
    assert classify_tags == {"demo": "router", "stage": "classify"}
    assert answer_service == service
    assert answer_tags == {
        "demo": "router",
        "stage": "answer",
        "route": label,
        "classifier": router.CLASSIFIER,
    }


@pytest.mark.parametrize("label", ["no idea", RuntimeError("gateway down")])
def test_unusable_classifier_falls_back_to_keywords(label):
    r = router.ask(FakeGateway(label), "Write a SQL query that counts orders per day")
    assert (r.route, r.classifier, r.service) == ("sql", "keywords", "qwen_code")


@pytest.mark.parametrize(
    ("prompt", "route"),
    [
        ("Write a Python function to parse dates", "code"),
        ("SELECT * FROM t is slow, why?", "sql"),
        ("Write a regular expression for ISO dates", "code"),
        ("Tips for a conference talk", "general"),
    ],
)
def test_keyword_route(prompt, route):
    assert router.keyword_route(prompt) == route


def test_services_are_qualified_by_the_caller():
    gw = FakeGateway("code")
    router.ask(gw, "x", qualify=lambda s: f"cat.sch.{s}")
    assert [service for service, _ in gw.calls] == ["cat.sch.gemini_fast", "cat.sch.qwen_code"]
