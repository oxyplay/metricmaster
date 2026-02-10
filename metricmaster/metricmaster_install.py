import asyncio
import base64
import json
from pathlib import Path

from flexus_client_kit import ckit_client, ckit_bot_install
from flexus_client_kit import ckit_cloudtool
from flexus_simple_bots import prompts_common
from metricmaster import metricmaster_prompts
from flexus_client_kit.integrations import fi_google_analytics
from metricmaster.tools import fi_google_tag_manager

BOT_DESCRIPTION = """
## MetricMaster - Google Analytics 4 & Tag Manager Specialist

A comprehensive analytics bot that helps you set up and manage Google Analytics 4 and Google Tag Manager for your websites.

**Key Features:**

- **OAuth Integration**: Seamless Google OAuth for GA4 and GTM access
- **Account Setup**: Guide through GA4 property and GTM container creation
- **GTM Container Deployment**: Generate code snippets and offer GitHub PR creation
- **GA4 Integration**: Automatically link GA4 measurement IDs to GTM
- **Event Tracking**: Set up comprehensive event tracking (pageviews, clicks, forms, e-commerce, custom events)
- **Analytics Reports**: Generate traffic, conversion, funnel, and custom reports
- **Scheduled Reports**: Automated daily/weekly/monthly analytics reports

**Perfect for:**

- Setting up analytics from scratch
- Migrating from Universal Analytics to GA4
- Implementing comprehensive event tracking
- Generating regular analytics insights
- E-commerce tracking and conversion optimization

**Industries:**

- E-commerce (purchase tracking, cart abandonment)
- SaaS (trial signups, feature usage)
- Lead Generation (form submissions, contact requests)
- Content/Media (video engagement, content consumption)

MetricMaster guides you through every step of the analytics setup process with clear explanations and best practices.
"""

METRICMASTER_SETUP_SCHEMA = (
    fi_google_analytics.GOOGLE_ANALYTICS_SETUP_SCHEMA +
    fi_google_tag_manager.GOOGLE_TAG_MANAGER_SETUP_SCHEMA +
    [
        {
            "bs_name": "GITHUB_REPO_URL",
            "bs_type": "string_long",
            "bs_default": "",
            "bs_group": "GitHub Integration",
            "bs_description": "GitHub repository URL for automated PR creation (optional, e.g., 'https://github.com/user/repo')",
        },
        {
            "bs_name": "SCHEDULED_REPORTS",
            "bs_type": "list_dict",
            "bs_default": [],
            "bs_group": "Scheduled Reports",
            "bs_description": "Configure automated analytics reports",
            "bs_elements": [
                {
                    "bs_name": "report_name",
                    "bs_type": "string_short",
                    "bs_default": "",
                    "bs_description": "Report name (e.g., 'Weekly Traffic Report')",
                },
                {
                    "bs_name": "frequency",
                    "bs_type": "string_short",
                    "bs_default": "weekly",
                    "bs_description": "Frequency: daily, weekly, monthly",
                },
                {
                    "bs_name": "property_id",
                    "bs_type": "string_short",
                    "bs_default": "",
                    "bs_description": "GA4 property ID",
                },
                {
                    "bs_name": "metrics",
                    "bs_type": "string_multiline",
                    "bs_default": "totalUsers,sessions,screenPageViews",
                    "bs_description": "Comma-separated metrics",
                },
                {
                    "bs_name": "dimensions",
                    "bs_type": "string_multiline",
                    "bs_default": "date",
                    "bs_description": "Comma-separated dimensions",
                },
            ],
        },
    ]
)

METRICMASTER_DEFAULT_LARK = """
print("MetricMaster processing %d messages" % len(messages))
"""


async def install(
    client: ckit_client.FlexusClient,
    ws_id: str,
    bot_name: str,
    bot_version: str,
    tools: list[ckit_cloudtool.CloudTool],
):
    bot_internal_tools = json.dumps([t.openai_style_tool() for t in tools])

    pic_big_path = Path(__file__).with_name("metricmaster-1024x1536.webp")
    pic_small_path = Path(__file__).with_name("metricmaster-256x256.webp")

    if pic_big_path.exists():
        pic_big = base64.b64encode(pic_big_path.read_bytes()).decode("ascii")
    else:
        pic_big = ""
        logger.warning("Big image not found at %s", pic_big_path)

    if pic_small_path.exists():
        pic_small = base64.b64encode(pic_small_path.read_bytes()).decode("ascii")
    else:
        pic_small = ""
        logger.warning("Small image not found at %s", pic_small_path)

    await ckit_bot_install.marketplace_upsert_dev_bot(
        client,
        ws_id=ws_id,
        marketable_name=bot_name,
        marketable_version=bot_version,
        marketable_accent_color="#4285F4",
        marketable_title1="MetricMaster",
        marketable_title2="Google Analytics 4 & Tag Manager specialist for website analytics setup and reporting",
        marketable_author="Flexus",
        marketable_occupation="Analytics Specialist",
        marketable_description=BOT_DESCRIPTION,
        marketable_typical_group="Analytics / Marketing",
        marketable_github_repo="https://github.com/yourusername/metricmaster.git",
        marketable_run_this="python -m metricmaster.metricmaster_bot",
        marketable_setup_default=METRICMASTER_SETUP_SCHEMA,
        marketable_featured_actions=[
            {
                "feat_question": "Help me set up Google Analytics 4 and Tag Manager",
                "feat_expert": "default",
                "feat_depends_on_setup": [],
            },
            {
                "feat_question": "Show me my website traffic for the last 30 days",
                "feat_expert": "default",
                "feat_depends_on_setup": ["GA_DEFAULT_PROPERTY"],
            },
            {
                "feat_question": "Set up event tracking for form submissions",
                "feat_expert": "default",
                "feat_depends_on_setup": ["GTM_DEFAULT_CONTAINER"],
            },
        ],
        marketable_intro_message="Hello! I'm MetricMaster, your Google Analytics 4 and Tag Manager specialist. I can help you set up analytics, configure event tracking, and generate insights from your data. Let's get started!",
        marketable_preferred_model_default="grok-4-1-fast-reasoning",
        marketable_daily_budget_default=200_000,
        marketable_default_inbox_default=10_000,
        marketable_experts=[
            ("default", ckit_bot_install.FMarketplaceExpertInput(
                fexp_system_prompt=metricmaster_prompts.main_prompt,
                fexp_python_kernel=METRICMASTER_DEFAULT_LARK,
                fexp_block_tools="",
                fexp_allow_tools="",
                fexp_app_capture_tools=bot_internal_tools,
                fexp_description="Main expert for interactive analytics setup, configuration, and reporting",
            )),
            ("scheduled", ckit_bot_install.FMarketplaceExpertInput(
                fexp_system_prompt=metricmaster_prompts.scheduled_prompt,
                fexp_python_kernel=METRICMASTER_DEFAULT_LARK,
                fexp_block_tools="",
                fexp_allow_tools="",
                fexp_app_capture_tools=bot_internal_tools,
                fexp_description="Scheduled expert for automated report generation",
            )),
        ],
        marketable_tags=["Analytics", "Google Analytics", "Tag Manager", "Reports"],
        marketable_picture_big_b64=pic_big,
        marketable_picture_small_b64=pic_small,
        marketable_schedule=[
            prompts_common.SCHED_TASK_SORT_10M | {"sched_when": "EVERY:10m"},
            prompts_common.SCHED_TODO_5M | {
                "sched_when": "EVERY:5m",
                "sched_first_question": "Work on the assigned analytics task",
                "sched_fexp_name": "scheduled",
            },
            {
                "sched_type": "SCHED_ANY",
                "sched_when": "WEEKDAYS:MO:FR/09:00",
                "sched_first_question": "Check if there are any scheduled reports configured. If yes, generate them and save to policy documents.",
                "sched_fexp_name": "scheduled",
            },
        ],
        marketable_forms=ckit_bot_install.load_form_bundles(__file__),
    )


if __name__ == "__main__":
    import logging
    logger = logging.getLogger("metricmaster_install")

    from metricmaster import metricmaster_bot
    args = ckit_bot_install.bot_install_argparse()
    client = ckit_client.FlexusClient("metricmaster_install")
    asyncio.run(install(client, ws_id=args.ws, bot_name=metricmaster_bot.BOT_NAME, bot_version=metricmaster_bot.BOT_VERSION, tools=metricmaster_bot.TOOLS))
