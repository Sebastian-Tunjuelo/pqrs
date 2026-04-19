import pytest
import importlib


def test_exit_sin_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    import telegram_bot.config as cfg
    # Reload so the module re-reads env vars (token is now absent)
    importlib.reload(cfg)
    # After reload, patch the module-level var to ensure it's None
    monkeypatch.setattr(cfg, "TELEGRAM_BOT_TOKEN", None)
    with pytest.raises(SystemExit) as exc:
        cfg.validate()
    assert exc.value.code == 1
