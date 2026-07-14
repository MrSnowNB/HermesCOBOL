# Diagnosis — Update Access Denied + Non-MTP Reload on Start

**Date:** 2026-07-14  
**Status:** Diagnosed; non-MTP unloaded again; SOP + ensure script provided  

---

## Problem A — `hermes update` Access Denied (os error 5)

### What it is (and is not)

```
error: failed to remove file
  C:\work\hermes-agent\.venv\...\Scripts\hermes.exe
  Access is denied. (os error 5)
```

This is **not** primarily a Windows Defender “block the app” failure. It is a **file lock**: Windows will not replace an `.exe` while a process still has it open.

### Proof (live at diagnosis)

| PID | Process | Path |
|-----|---------|------|
| 57672 | `hermes.exe` | `C:\work\hermes-agent\.venv\Scripts\hermes.exe` |
| 9264 | `python.exe` | same venv — child of hermes |
| 42252 | `python.exe` | uv python also hosting hermes |

You ran `/exit` in the TUI, then `hermes update`, but **another hermes process was still alive** (or you started `hermes` again before install finished). The interrupted install then re-triggers on next `hermes` launch and fails again for the same reason — install tries to replace `hermes.exe` **while that same process is running**.

### Correct update procedure (Windows)

```powershell
# 1) Fully stop Hermes (all instances — TUI, gateway, background)
Get-Process hermes -ErrorAction SilentlyContinue | Stop-Process -Force
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -like '*hermes-agent*' -or $_.ExecutablePath -like '*hermes.exe*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# 2) Confirm lock is gone
Get-Process hermes -ErrorAction SilentlyContinue   # must be empty

# 3) Update
cd C:\work\hermes-agent
hermes update
# If restore-stash prompt appears: prefer N unless you know you need local patches
# Stashing re-applied old customizations can cause odd behavior.

# 4) Only then start Hermes
hermes
```

If Defender/App Control also blocks `llama-server.exe` (you’ve seen that for other models), that is a **separate** issue; the os error 5 on `hermes.exe` during update is the lock.

### Recover from interrupted install (after all hermes stopped)

```powershell
cd C:\work\hermes-agent
# Ensure no hermes process
Get-Process hermes -ErrorAction SilentlyContinue | Stop-Process -Force
.\.venv\Scripts\python.exe -m ensurepip --upgrade
& "$env:LOCALAPPDATA\hermes\bin\uv.exe" pip install -e ".[all]"
# or:
.\.venv\Scripts\python.exe -m pip install -e ".[all]"
```

---

## Problem B — Non-MTP reloads on start

### Important split

| Layer | State after our earlier cleanup | What happens on Lemonade restart |
|-------|----------------------------------|----------------------------------|
| Hermes `config.yaml` | Pinned **MTP** | Stays MTP (your banner shows MTP — correct) |
| `user_models.json` | No non-MTP user entry | Stays clean |
| **Lemonade built-in catalog** | **Always ships non-MTP** | Non-MTP **reappears as loadable** forever |

### Root cause: built-in catalog, not “old Hermes setting”

File (Lemonade install, not your user config):

`C:\Users\AMD\AppData\Local\lemonade_server\bin\resources\server_models.json`

```json
"Qwen3.6-35B-A3B-GGUF": {
  "checkpoint": "unsloth/Qwen3.6-35B-A3B-GGUF:...",
  "labels": ["vision", "tool-calling", "hot"],
  "suggested": true
},
"Qwen3.6-35B-A3B-MTP-GGUF": {
  "checkpoint": "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:...",
  "labels": ["vision", "tool-calling", "mtp"],
  "suggested": true
}
```

So:

1. **`DELETE` only removes a registration / loaded instance** — it does **not** remove the built-in catalog entry. After Lemonade restart (or re-pull of models list), **both names are available again**.
2. Something (Lemonade UI last selection, “hot” models, multi-model restore, accidental load) requests `Qwen3.6-35B-A3B-GGUF` and it **loads into a free LLM slot**.
3. `max_loaded_models_per_type: 2` / `max_loaded_models: 5` allows **MTP + Hermes-3 + non-MTP** to coexist — dual 35B is possible.

### Proof (today)

- Hermes TUI banner: **`Qwen3.6-35B-A3B-MTP-GGUF`** (config pin works)
- Lemonade health before re-unload: **`model_loaded=Qwen3.6-35B-A3B-GGUF`** with both 35B variants resident on `:8002` and `:8004`
- After `unload` + `load MTP`: only MTP + Hermes-3 + nomic

Hermes is **not** the source of the non-MTP reload if the banner shows MTP. **Lemonade** is.

---

## What we did just now

```text
POST /api/v0/unload  Qwen3.6-35B-A3B-GGUF  → success
POST /api/v1/delete  Qwen3.6-35B-A3B-GGUF  → success (catalog entry still exists as builtin)
POST /api/v1/load    Qwen3.6-35B-A3B-MTP-GGUF → success
model_loaded = Qwen3.6-35B-A3B-MTP-GGUF
loaded LLMs  = MTP + Hermes-3 only
```

---

## Durable mitigation

### Do

1. In **Lemonade Model Manager**, never leave non-MTP as the selected/active model; prefer MTP.
2. Run `ensure_mtp_loaded.ps1` after Lemonade starts (or logon) — unloads non-MTP, loads MTP.
3. Keep Hermes `config.yaml` pin (already done).
4. Always stop all `hermes.exe` before `hermes update`.

### Do not

1. Expect `DELETE` to permanently remove built-in non-MTP from Lemonade.
2. Edit `server_models.json` permanently — Lemonade updates will overwrite it.
3. Answer “Y” to stash restore on update unless you know the stashed patches.

### Optional Lemonade UI habit

Unload `Qwen3.6-35B-A3B-GGUF` whenever it appears after a Lemonade restart. Keep **Hermes-3** loaded for Honcho derivers.

---

## Quick verify

```powershell
# Loaded models — must not list Qwen3.6-35B-A3B-GGUF without MTP
(Invoke-RestMethod http://127.0.0.1:8000/api/v1/health).all_models_loaded.model_name

# Hermes pin
Select-String C:\Users\AMD\.hermes\config.yaml -Pattern 'default:'

# Gate suite
python C:\work\HermesCOBOL\tmp\mtp-cleanup\run_gates.py
```
