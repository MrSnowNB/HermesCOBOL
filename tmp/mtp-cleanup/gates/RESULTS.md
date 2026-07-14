# Gate Results — ALL PASS
Run: 2026-07-14T16:10:54.444410+00:00
Passed: 9 / 9

| Gate | Pass | Notes |
|------|------|-------|
| G0_backups | PASS | `{"count": 5, "files": ["hermes-config.yaml.bak", "HermesCOBOL.env.bak", "lemonade-config.json.bak", "recipe_options.json` |
| G2_no_nonmtp_loaded | PASS | `{"http": 200, "error": null, "model_loaded": "Qwen3.6-35B-A3B-MTP-GGUF", "all_loaded": ["nomic-embed-text-v2-moe-GGUF", ` |
| G7_loaded_llms_allowlist | PASS | `{"llm_loaded": ["Qwen3.6-35B-A3B-MTP-GGUF", "Hermes-3-Llama-3.1-8B-GGUF"], "bad_llms": [], "require_mtp_present": true}` |
| G6_catalog_no_nonmtp | PASS | `{"http": 200, "error": null, "non_mtp_ids": [], "mtp_present": true, "qwen35_related": ["Qwen3.5-35B-A3B-GGUF", "Qwen3.6` |
| G3_registry_scrubbed | PASS | `{"user_models_has_nonmtp_key": false, "recipe_options_has_nonmtp_key": false, "user_models_path": "C:\\Users\\AMD\\.cach` |
| G4_hermes_config_pinned | PASS | `{"path": "C:\\Users\\AMD\\.hermes\\config.yaml", "has_mtp": true, "has_non_mtp_default": false, "has_custom_provider": t` |
| G5_hermescolbol_env | PASS | `{"chat_model_lines": ["OPENAI_MODEL=user.Qwen3.6-35B-A3B-MTP-GGUF", "LEMONADE_CHAT_MODEL=user.Qwen3.6-35B-A3B-MTP-GGUF"]` |
| G8_mtp_completion | PASS | `{"http": 200, "error": null, "content_preview": "", "reasoning_preview": "Here's a thinking process:\n\n1.  **Analyze Us` |
| G9_nonmtp_negative | PASS | `{"bare_http": null, "user_http": 404, "bare_error": "timed out", "user_error": "HTTP Error 404: Not Found", "bare_error_` |
