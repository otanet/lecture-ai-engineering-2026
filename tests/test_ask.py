from types import SimpleNamespace
import sys

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    call_args = {}
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=7),
        text="回答",
    )
    client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: (call_args.update(kwargs) or response)
        )
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    answer = ask_module.ask("質問", temperature=0.7, model="gemini-3.5-flash")

    assert answer == "回答"
    assert call_args["model"] == "gemini-3.5-flash"
    assert call_args["config"].temperature == 0.7
    assert "[トークン] 入力: 12, 出力: 7" in capsys.readouterr().out


def test_main_passes_temperature_option(monkeypatch, capsys):
    received = {}
    monkeypatch.setattr(
        sys,
        "argv",
        ["app.ask", "--model", "gemini-3.1-flash-lite", "--temperature", "0.7", "質問"],
    )
    monkeypatch.setattr(
        ask_module,
        "ask",
        lambda question, temperature, model: received.update(
            question=question, temperature=temperature, model=model
        ) or "回答",
    )

    ask_module.main()

    assert received == {
        "question": "質問",
        "temperature": 0.7,
        "model": "gemini-3.1-flash-lite",
    }
    output = capsys.readouterr().out
    assert "[model] gemini-3.1-flash-lite" in output
    assert "[temperature] 0.7" in output
