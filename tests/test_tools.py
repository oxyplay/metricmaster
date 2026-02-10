import pytest


def test_gtm_tool_structure():
    from metricmaster.tools import fi_google_tag_manager
    tool = fi_google_tag_manager.GOOGLE_TAG_MANAGER_TOOL
    assert tool.name == "google_tag_manager"
    assert tool.strict == False
    assert "help" in tool.description.lower()
    assert "properties" in tool.parameters
    assert tool.parameters["type"] == "object"


def test_gtm_help_content():
    from metricmaster.tools import fi_google_tag_manager
    help_text = fi_google_tag_manager.HELP
    assert "google_tag_manager" in help_text
    assert "listAccounts" in help_text
    assert "createContainer" in help_text
    assert "linkGA4" in help_text
    assert "publishVersion" in help_text


def test_ga_enhanced_tool_structure():
    from metricmaster.tools import fi_google_analytics_enhanced
    tool = fi_google_analytics_enhanced.GOOGLE_ANALYTICS_ENHANCED_TOOL
    assert tool.name == "google_analytics_enhanced"
    assert tool.strict == False
    assert "help" in tool.description.lower()


def test_ga_enhanced_help_content():
    from metricmaster.tools import fi_google_analytics_enhanced
    help_text = fi_google_analytics_enhanced.HELP
    assert "google_analytics_enhanced" in help_text
    assert "listEvents" in help_text
    assert "getConversions" in help_text
    assert "getEcommerceReport" in help_text
    assert "getFunnelReport" in help_text


def test_gtm_setup_schema():
    from metricmaster.tools import fi_google_tag_manager
    schema = fi_google_tag_manager.GOOGLE_TAG_MANAGER_SETUP_SCHEMA
    assert len(schema) == 2
    assert schema[0]["bs_name"] == "GTM_DEFAULT_ACCOUNT"
    assert schema[1]["bs_name"] == "GTM_DEFAULT_CONTAINER"
    assert all(item["bs_type"] == "string_short" for item in schema)


def test_tool_scopes():
    from metricmaster.tools import fi_google_tag_manager
    from flexus_client_kit.integrations import fi_google_analytics
    gtm_scopes = fi_google_tag_manager.REQUIRED_SCOPES
    ga_scopes = fi_google_analytics.REQUIRED_SCOPES
    assert "tagmanager" in " ".join(gtm_scopes)
    assert "analytics" in " ".join(ga_scopes)
