from career_copilot.config import Settings


def test_settings_ignore_unknown_env_file_keys(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("OLLAMA_MODEL=test-model\nSOME_OTHER_TOOL_KEY=value\n")

    settings = Settings(_env_file=env_file)

    assert settings.ollama_model == "test-model"
