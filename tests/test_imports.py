import pytest


def test_main_imports():
    from metricmaster import metricmaster_bot, metricmaster_prompts, metricmaster_install
    assert metricmaster_bot.BOT_NAME == "metricmaster"
    assert metricmaster_bot.BOT_VERSION == "0.1.0"
    assert len(metricmaster_bot.TOOLS) == 6


def test_tool_imports():
    from metricmaster.tools import fi_google_tag_manager, fi_google_analytics_enhanced
    assert fi_google_tag_manager.GOOGLE_TAG_MANAGER_TOOL is not None
    assert fi_google_analytics_enhanced.GOOGLE_ANALYTICS_ENHANCED_TOOL is not None


def test_prompts():
    from metricmaster import metricmaster_prompts
    assert len(metricmaster_prompts.main_prompt) > 100
    assert len(metricmaster_prompts.scheduled_prompt) > 50
    assert "MetricMaster" in metricmaster_prompts.main_prompt
    assert "Google Analytics" in metricmaster_prompts.main_prompt
    assert "Tag Manager" in metricmaster_prompts.main_prompt


def test_setup_schema():
    from metricmaster import metricmaster_install
    schema = metricmaster_install.METRICMASTER_SETUP_SCHEMA
    assert len(schema) > 0
    assert any(item["bs_name"] == "GA_DEFAULT_PROPERTY" for item in schema)
    assert any(item["bs_name"] == "GTM_DEFAULT_ACCOUNT" for item in schema)
    assert any(item["bs_name"] == "SCHEDULED_REPORTS" for item in schema)


def test_tool_definitions():
    from metricmaster import metricmaster_bot
    tool_names = [t.name for t in metricmaster_bot.TOOLS]
    assert "google_analytics" in tool_names
    assert "google_analytics_enhanced" in tool_names
    assert "google_tag_manager" in tool_names
    assert "flexus_policy_document" in tool_names
    assert "mongo_store" in tool_names
    assert "ask_questions" in tool_names
