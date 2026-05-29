from pathlib import Path

from muscles.core.core import Configurator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_secret_constructor_reads_custom_secret_file(tmp_path):
    _write(
        tmp_path / "configuration.yaml",
        "db:\n  uri: !secret DB_URI\n",
    )
    _write(
        tmp_path / "secrets" / "custom-secret.yaml",
        "DB_URI: sqlite:///custom.db\n",
    )

    config = Configurator(
        file="configuration.yaml",
        basedir=str(tmp_path),
        name="secret-custom",
        secret_file="secrets/custom-secret.yaml",
    )

    assert config.db.uri.value() == "sqlite:///custom.db"


def test_secret_constructor_uses_default_fallback_path(tmp_path):
    _write(
        tmp_path / "configuration.yaml",
        "db:\n  uri: !secret DB_URI\n",
    )
    _write(
        tmp_path / "config" / "secret.yaml",
        "DB_URI: sqlite:///fallback.db\n",
    )

    config = Configurator(
        file="configuration.yaml",
        basedir=str(tmp_path),
        name="secret-fallback",
    )

    assert config.db.uri.value() == "sqlite:///fallback.db"
