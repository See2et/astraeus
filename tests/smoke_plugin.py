#!/usr/bin/env python3
"""Real CLI lifecycle test, isolated CODEX_HOME, no authentication/model calls."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="astraeus-smoke-") as tmp:
        tmp = Path(tmp)
        source = tmp / "checkout"
        source.mkdir()
        shutil.copytree(ROOT / "plugins", source / "plugins")
        shutil.copytree(ROOT / ".agents", source / ".agents")
        other = tmp / "other-source"
        shutil.copytree(source, other)
        other_plugin = other / "plugins/astraeus"
        other_plugin.rename(other / "plugins/sentinel")
        manifest = other / "plugins/sentinel/.codex-plugin/plugin.json"
        data = json.loads(manifest.read_text())
        data["name"] = "sentinel"
        manifest.write_text(json.dumps(data))
        catalog = other / ".agents/plugins/marketplace.json"
        data = json.loads(catalog.read_text())
        data["name"] = "sentinel-market"
        data["plugins"][0].update(name="sentinel", source=dict(source="local", path="./plugins/sentinel"))
        catalog.write_text(json.dumps(data))
        home = tmp / "codex-home"
        home.mkdir()
        (home / "config.toml").write_text('model = "gpt-6-astra"\n')
        (home / "history.jsonl").write_text('{"sentinel":"preserve"}\n')
        (home / "auth.json").write_text('{}\n')
        env = os.environ | {"CODEX_HOME": str(home)}
        def run(*cmd):
            p = subprocess.run(cmd, env=env, cwd=tmp, text=True, capture_output=True)
            if p.returncode:
                raise AssertionError(f"{cmd}: {p.stdout}\n{p.stderr}")
            return p.stdout
        script = source / "plugins/astraeus/scripts/astraeus.py"
        import sys
        def manage(action):
            return json.loads(run(sys.executable, str(script), "plugin", action, "--repo", str(source), "--apply"))
        run("codex", "plugin", "marketplace", "add", str(other))
        installed_other = json.loads(run("codex", "plugin", "add", "sentinel@sentinel-market", "--json"))
        sentinel_cache = Path(installed_other["installedPath"])
        def snapshot(path):
            return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}
        sentinel_before = snapshot(sentinel_cache)
        auth_before = (home / "auth.json").read_bytes()
        history_before = (home / "history.jsonl").read_bytes()
        installed = manage("install")
        installed_path = Path(json.loads(installed["outputs"][-1])["installedPath"])
        assert (installed_path / "skills/orchestrate/SKILL.md").is_file()
        assert (installed_path / "skills/adjudicate/SKILL.md").is_file()
        assert (installed_path / "schemas/adjudication.json").is_file()
        skill = source / "plugins/astraeus/skills/orchestrate/SKILL.md"
        skill.write_text(skill.read_text() + "\nSmoke refresh marker.\n")
        refreshed = manage("refresh")
        refreshed_path = Path(json.loads(refreshed["outputs"][-1])["installedPath"])
        assert refreshed_path != installed_path
        assert "Smoke refresh marker." in (refreshed_path / "skills/orchestrate/SKILL.md").read_text()
        manage("reset")
        # Full source identity check: a second checkout must not replace the registered source.
        mismatch = tmp / "wrong-checkout"
        shutil.copytree(source, mismatch)
        p = subprocess.run([sys.executable, str(script), "plugin", "refresh", "--repo", str(mismatch), "--apply"],
                           env=env, cwd=tmp, capture_output=True, text=True)
        assert p.returncode == 2 and "not this local checkout" in p.stderr
        agents = home / "AGENTS.md"
        agents.write_text("Keep sentinel instructions.\n")
        run(sys.executable, str(script), "activation", "enable", "--apply")
        assert "astraeus:begin" in agents.read_text()
        run(sys.executable, str(script), "activation", "disable", "--apply")
        assert "astraeus:begin" not in agents.read_text()
        assert agents.read_text() == "Keep sentinel instructions.\n"
        manage("remove")
        assert not refreshed_path.exists()
        assert sentinel_cache.exists() and snapshot(sentinel_cache) == sentinel_before
        assert (home / "auth.json").read_bytes() == auth_before
        assert (home / "history.jsonl").read_bytes() == history_before
        import tomllib
        config = tomllib.loads((home / "config.toml").read_text())
        assert config["model"] == "gpt-6-astra"
        assert config["plugins"]["sentinel@sentinel-market"]["enabled"] is True
        run("codex", "plugin", "marketplace", "remove", "astraeus")
        print(json.dumps(dict(status="passed", cli=run("codex", "--version").strip(),
                              checks=["install", "refresh contents", "reset", "source mismatch refusal",
                                      "activation enable/disable", "remove", "other plugin unchanged",
                                      "auth/history unchanged", "unrelated config preserved"]), indent=2))


if __name__ == "__main__":
    main()
