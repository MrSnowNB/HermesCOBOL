#!/usr/bin/env python3
"""Gated validation for MTP-only Qwen cleanup. Writes gates/RESULTS.json + probe artifacts."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ART = Path(__file__).resolve().parent
GATES = ART / "gates"
LEMONADE = "http://127.0.0.1:8000"
MTP = "Qwen3.6-35B-A3B-MTP-GGUF"
NON_MTP = "Qwen3.6-35B-A3B-GGUF"
NON_MTP_USER = "user.Qwen3.6-35B-A3B-GGUF"
ALLOWED_LOADED_LLMS = {MTP, "Hermes-3-Llama-3.1-8B-GGUF"}
# embeddings allowed
ALLOWED_LOADED = ALLOWED_LOADED_LLMS | {"nomic-embed-text-v2-moe-GGUF"}

HERMES_CFG = Path.home() / ".hermes" / "config.yaml"
USER_MODELS = Path.home() / ".cache" / "lemonade" / "user_models.json"
RECIPE_OPTS = Path.home() / ".cache" / "lemonade" / "recipe_options.json"
HERMESCOBOL_ENV = Path(r"C:\work\HermesCOBOL\.env")


def http_json(method: str, url: str, body: dict | None = None, timeout: float = 60.0):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {"_raw": raw}
            return resp.status, payload, None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"_raw": raw}
        return e.code, payload, str(e)
    except Exception as e:
        return None, {}, str(e)


def is_non_mtp_35b_id(name: str) -> bool:
    """True if name is the stale non-MTP 35B id (not MTP, not other Qwen variants)."""
    if not name:
        return False
    n = name.strip()
    # strip user. prefix for comparison
    bare = n[5:] if n.startswith("user.") else n
    if "MTP" in bare.upper():
        return False
    # exact non-MTP product id
    return bare == NON_MTP or bare == f"{NON_MTP}" or re.fullmatch(
        r"Qwen3\.6-35B-A3B-GGUF", bare
    ) is not None


def gate(name: str, passed: bool, detail: dict) -> dict:
    return {
        "gate": name,
        "pass": passed,
        "detail": detail,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    GATES.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    # G0 backups
    backups = list((ART / "backups").glob("*"))
    results.append(
        gate(
            "G0_backups",
            len(backups) >= 4,
            {"count": len(backups), "files": [b.name for b in backups]},
        )
    )

    # G2 health — no non-MTP loaded
    code, health, err = http_json("GET", f"{LEMONADE}/api/v1/health")
    (GATES / "06-live-health.json").write_text(
        json.dumps(health, indent=2), encoding="utf-8"
    )
    loaded = []
    if isinstance(health, dict):
        for m in health.get("all_models_loaded") or []:
            loaded.append(m.get("model_name") or "")
    non_mtp_loaded = [n for n in loaded if is_non_mtp_35b_id(n)]
    unexpected_llm = [
        n
        for n in loaded
        if n not in ALLOWED_LOADED and not n.endswith("-GGUF") is False
    ]
    # only flag unexpected *llm* that look like the bad non-mtp
    results.append(
        gate(
            "G2_no_nonmtp_loaded",
            code == 200 and len(non_mtp_loaded) == 0,
            {
                "http": code,
                "error": err,
                "model_loaded": health.get("model_loaded") if isinstance(health, dict) else None,
                "all_loaded": loaded,
                "non_mtp_loaded": non_mtp_loaded,
            },
        )
    )

    # G7 allowed loaded set for LLMs of interest
    llm_loaded = [
        m.get("model_name")
        for m in (health.get("all_models_loaded") or [])
        if isinstance(m, dict) and m.get("type") == "llm"
    ]
    bad_llms = [n for n in llm_loaded if n not in ALLOWED_LOADED_LLMS]
    results.append(
        gate(
            "G7_loaded_llms_allowlist",
            len(bad_llms) == 0 and MTP in llm_loaded,
            {"llm_loaded": llm_loaded, "bad_llms": bad_llms, "require_mtp_present": MTP in llm_loaded},
        )
    )

    # G6 catalog
    code_m, models, err_m = http_json("GET", f"{LEMONADE}/api/v1/models")
    (GATES / "06-live-models.json").write_text(
        json.dumps(models, indent=2)[:200000], encoding="utf-8"
    )
    ids = []
    if isinstance(models, dict):
        ids = [d.get("id") for d in (models.get("data") or []) if isinstance(d, dict)]
    non_mtp_catalog = [i for i in ids if is_non_mtp_35b_id(i or "")]
    mtp_in_catalog = any(
        (i or "") == MTP or (i or "").endswith(MTP) or MTP in (i or "") for i in ids
    )
    results.append(
        gate(
            "G6_catalog_no_nonmtp",
            code_m == 200 and len(non_mtp_catalog) == 0 and mtp_in_catalog,
            {
                "http": code_m,
                "error": err_m,
                "non_mtp_ids": non_mtp_catalog,
                "mtp_present": mtp_in_catalog,
                "qwen35_related": [i for i in ids if i and "35B-A3B" in i],
            },
        )
    )

    # G3 config files
    um = USER_MODELS.read_text(encoding="utf-8") if USER_MODELS.exists() else ""
    ro = RECIPE_OPTS.read_text(encoding="utf-8") if RECIPE_OPTS.exists() else ""
    um_bad = bool(re.search(r"Qwen3\.6-35B-A3B-GGUF", um)) and "MTP" not in "".join(
        re.findall(r"Qwen3\.6-35B-A3B[^\"]*", um)
    )
    # stricter: key presence
    um_has_non = '"Qwen3.6-35B-A3B-GGUF"' in um or "'Qwen3.6-35B-A3B-GGUF'" in um
    ro_has_non = "user.Qwen3.6-35B-A3B-GGUF" in ro
    results.append(
        gate(
            "G3_registry_scrubbed",
            (not um_has_non) and (not ro_has_non),
            {
                "user_models_has_nonmtp_key": um_has_non,
                "recipe_options_has_nonmtp_key": ro_has_non,
                "user_models_path": str(USER_MODELS),
                "recipe_options_path": str(RECIPE_OPTS),
            },
        )
    )

    # G4 hermes config
    hcfg = HERMES_CFG.read_text(encoding="utf-8") if HERMES_CFG.exists() else ""
    has_mtp_default = MTP in hcfg
    has_non_as_default = bool(
        re.search(r"default:\s*[\"']?user\.?Qwen3\.6-35B-A3B-GGUF[\"']?", hcfg)
    ) or bool(
        re.search(r"default:\s*[\"']?Qwen3\.6-35B-A3B-GGUF[\"']?", hcfg)
    )
    # if default is non-mtp without MTP substring
    pins_ok = has_mtp_default and not has_non_as_default and "provider: \"custom\"" in hcfg.replace("'", '"') or (
        "provider: \"custom\"" in hcfg or "provider: 'custom'" in hcfg or 'provider: "custom"' in hcfg
    )
    # simplify pins_ok
    pins_ok = (
        has_mtp_default
        and not has_non_as_default
        and ("provider: \"custom\"" in hcfg or "provider: 'custom'" in hcfg)
        and "127.0.0.1:8000" in hcfg
        and "title_generation" in hcfg
        and "compression" in hcfg
    )
    results.append(
        gate(
            "G4_hermes_config_pinned",
            pins_ok,
            {
                "path": str(HERMES_CFG),
                "has_mtp": has_mtp_default,
                "has_non_mtp_default": has_non_as_default,
                "has_custom_provider": "custom" in hcfg,
                "has_aux_pins": "title_generation" in hcfg and "compression" in hcfg,
            },
        )
    )

    # G5 HermesCOBOL env
    env_txt = HERMESCOBOL_ENV.read_text(encoding="utf-8") if HERMESCOBOL_ENV.exists() else ""
    env_lines = [
        ln
        for ln in env_txt.splitlines()
        if re.search(r"^(OPENAI_MODEL|LEMONADE_CHAT_MODEL)=", ln)
    ]
    env_ok = all("MTP" in ln for ln in env_lines) and len(env_lines) >= 1
    env_bad = any(is_non_mtp_35b_id(ln.split("=", 1)[-1].strip()) for ln in env_lines)
    results.append(
        gate(
            "G5_hermescolbol_env",
            env_ok and not env_bad,
            {"chat_model_lines": env_lines, "env_bad": env_bad},
        )
    )

    # G8 MTP completion probe (thinking models may put tokens in reasoning_content)
    status_ok, body_ok, err_ok = http_json(
        "POST",
        f"{LEMONADE}/api/v1/chat/completions",
        {
            "model": MTP,
            "messages": [
                {
                    "role": "user",
                    "content": "Do not think long. Reply with the single token: MTP_OK",
                }
            ],
            "max_tokens": 64,
            "temperature": 0,
        },
        timeout=180.0,
    )
    (GATES / "08-mtp-completion.json").write_text(
        json.dumps(
            {"http": status_ok, "error": err_ok, "response": body_ok},
            indent=2,
            default=str,
        )[:50000],
        encoding="utf-8",
    )
    content = ""
    reasoning = ""
    resp_model = ""
    try:
        msg = body_ok["choices"][0]["message"]
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or ""
        resp_model = body_ok.get("model") or ""
    except Exception:
        content = str(body_ok)[:500]
    # Success: HTTP 200, any assistant text, and response tied to MTP/Qwen3.6-35B-A3B (not non-MTP bare id)
    text_any = bool((content or "").strip() or (reasoning or "").strip())
    model_ok = ("MTP" in (resp_model or "") or "Qwen3.6-35B-A3B" in (resp_model or "")) and (
        NON_MTP not in (resp_model or "") or "MTP" in (resp_model or "")
    )
    # If lemonade returns underlying gguf name (e.g. ...UD-Q4_K_XL.gguf), still accept when request was MTP
    if status_ok == 200 and text_any and not is_non_mtp_35b_id(resp_model):
        model_ok = True
    results.append(
        gate(
            "G8_mtp_completion",
            status_ok == 200 and text_any and model_ok,
            {
                "http": status_ok,
                "error": err_ok,
                "content_preview": (content or "")[:200],
                "reasoning_preview": (reasoning or "")[:200],
                "response_model": resp_model,
                "model_requested": MTP,
            },
        )
    )

    # G9 negative: non-MTP must not succeed as a usable chat model
    status_bad, body_bad, err_bad = http_json(
        "POST",
        f"{LEMONADE}/api/v1/chat/completions",
        {
            "model": NON_MTP,
            "messages": [{"role": "user", "content": "Reply with NONMTP_OK"}],
            "max_tokens": 8,
            "temperature": 0,
        },
        timeout=20.0,
    )
    status_bad2, body_bad2, err_bad2 = http_json(
        "POST",
        f"{LEMONADE}/api/v1/chat/completions",
        {
            "model": NON_MTP_USER,
            "messages": [{"role": "user", "content": "Reply with NONMTP_OK"}],
            "max_tokens": 8,
            "temperature": 0,
        },
        timeout=20.0,
    )
    (GATES / "09-nonmtp-negative.json").write_text(
        json.dumps(
            {
                "bare": {"http": status_bad, "error": err_bad, "response": body_bad},
                "user_prefix": {
                    "http": status_bad2,
                    "error": err_bad2,
                    "response": body_bad2,
                },
            },
            indent=2,
            default=str,
        )[:50000],
        encoding="utf-8",
    )

    def failed_ok(status, body, err):
        # Pass if not a successful completion that returns assistant text from non-MTP
        if status is None:
            # timeout / connection: treat as fail-closed for non-MTP availability
            return True
        if status != 200:
            return True
        try:
            c = (body.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            r = (body.get("choices") or [{}])[0].get("message", {}).get("reasoning_content") or ""
            if (c or r).strip():
                return False  # non-MTP produced output — FAIL
        except Exception:
            pass
        return True

    results.append(
        gate(
            "G9_nonmtp_negative",
            failed_ok(status_bad, body_bad, err_bad)
            and failed_ok(status_bad2, body_bad2, err_bad2),
            {
                "bare_http": status_bad,
                "user_http": status_bad2,
                "bare_error": err_bad,
                "user_error": err_bad2,
                "bare_error_snippet": str(body_bad)[:300],
                "user_error_snippet": str(body_bad2)[:300],
            },
        )
    )

    # Summary
    all_pass = all(r["pass"] for r in results)
    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "all_pass": all_pass,
        "passed": sum(1 for r in results if r["pass"]),
        "failed": sum(1 for r in results if not r["pass"]),
        "gates": results,
    }
    (GATES / "RESULTS.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Human table
    lines = [
        f"# Gate Results — {'ALL PASS' if all_pass else 'FAILURES PRESENT'}",
        f"Run: {summary['run_at']}",
        f"Passed: {summary['passed']} / {len(results)}",
        "",
        "| Gate | Pass | Notes |",
        "|------|------|-------|",
    ]
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        note = json.dumps(r["detail"], default=str)[:120].replace("|", "/")
        lines.append(f"| {r['gate']} | {mark} | `{note}` |")
    (GATES / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"all_pass": all_pass, "passed": summary["passed"], "failed": summary["failed"]}, indent=2))
    for r in results:
        print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['gate']}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
