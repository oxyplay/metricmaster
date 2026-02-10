import asyncio
import logging
import json
from typing import Dict, Any

from pymongo import AsyncMongoClient

from flexus_client_kit import ckit_client
from flexus_client_kit import ckit_cloudtool
from flexus_client_kit import ckit_bot_exec
from flexus_client_kit import ckit_shutdown
from flexus_client_kit import ckit_ask_model
from flexus_client_kit import ckit_mongo
from flexus_client_kit import ckit_kanban
from flexus_client_kit.integrations import fi_mongo_store
from flexus_client_kit.integrations import fi_pdoc
from flexus_client_kit.integrations import fi_google_analytics
from flexus_client_kit.integrations import fi_question
from metricmaster import metricmaster_install
from metricmaster.tools import fi_google_tag_manager
from metricmaster.tools import fi_google_analytics_enhanced

logger = logging.getLogger("bot_metricmaster")

BOT_NAME = "metricmaster"
BOT_VERSION = "0.1.0"

TOOLS = [
    fi_google_analytics.GOOGLE_ANALYTICS_TOOL,
    fi_google_analytics_enhanced.GOOGLE_ANALYTICS_ENHANCED_TOOL,
    fi_google_tag_manager.GOOGLE_TAG_MANAGER_TOOL,
    fi_mongo_store.MONGO_STORE_TOOL,
    fi_pdoc.POLICY_DOCUMENT_TOOL,
    fi_question.ASK_QUESTIONS_TOOL,
]


async def metricmaster_main_loop(fclient: ckit_client.FlexusClient, rcx: ckit_bot_exec.RobotContext) -> None:
    setup = ckit_bot_exec.official_setup_mixing_procedure(
        metricmaster_install.METRICMASTER_SETUP_SCHEMA,
        rcx.persona.persona_setup,
    )

    mongo_conn_str = await ckit_mongo.mongo_fetch_creds(fclient, rcx.persona.persona_id)
    mongo = AsyncMongoClient(mongo_conn_str)
    dbname = rcx.persona.persona_id + "_db"
    mydb = mongo[dbname]
    personal_mongo = mydb["personal_mongo"]
    pdoc_integration = fi_pdoc.IntegrationPdoc(rcx, rcx.persona.ws_root_group_id)

    ga_integration = fi_google_analytics.IntegrationGoogleAnalytics(fclient, rcx)
    ga_enhanced_integration = fi_google_analytics_enhanced.IntegrationGoogleAnalyticsEnhanced(
        fclient, rcx, ga_integration,
    )
    gtm_integration = fi_google_tag_manager.IntegrationGoogleTagManager(fclient, rcx)

    logger.info("MetricMaster bot initialized for persona %s", rcx.persona.persona_id)

    @rcx.on_updated_message
    async def updated_message_in_db(msg: ckit_ask_model.FThreadMessageOutput):
        pass

    @rcx.on_updated_thread
    async def updated_thread_in_db(th: ckit_ask_model.FThreadOutput):
        pass

    @rcx.on_updated_task
    async def updated_task_in_db(t: ckit_kanban.FPersonaKanbanTaskOutput):
        pass

    @rcx.on_tool_call(fi_google_analytics.GOOGLE_ANALYTICS_TOOL.name)
    async def toolcall_google_analytics(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        return await ga_integration.called_by_model(toolcall, model_produced_args)

    @rcx.on_tool_call(fi_google_analytics_enhanced.GOOGLE_ANALYTICS_ENHANCED_TOOL.name)
    async def toolcall_google_analytics_enhanced(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        return await ga_enhanced_integration.called_by_model(toolcall, model_produced_args)

    @rcx.on_tool_call(fi_google_tag_manager.GOOGLE_TAG_MANAGER_TOOL.name)
    async def toolcall_google_tag_manager(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        return await gtm_integration.called_by_model(toolcall, model_produced_args)

    @rcx.on_tool_call(fi_mongo_store.MONGO_STORE_TOOL.name)
    async def toolcall_mongo_store(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        return await fi_mongo_store.handle_mongo_store(
            rcx.workdir,
            personal_mongo,
            toolcall,
            model_produced_args,
        )

    @rcx.on_tool_call(fi_pdoc.POLICY_DOCUMENT_TOOL.name)
    async def toolcall_pdoc(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        return await pdoc_integration.called_by_model(toolcall, model_produced_args)

    @rcx.on_tool_call(fi_question.ASK_QUESTIONS_TOOL.name)
    async def toolcall_ask_questions(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        return fi_question.handle_ask_questions(toolcall, model_produced_args)

    try:
        while not ckit_shutdown.shutdown_event.is_set():
            await rcx.unpark_collected_events(sleep_if_no_work=10.0)

    finally:
        await rcx.wait_for_bg_tasks()
        logger.info("MetricMaster bot %s exit", rcx.persona.persona_id)


def main():
    scenario_fn = ckit_bot_exec.parse_bot_args()
    fclient = ckit_client.FlexusClient(ckit_client.bot_service_name(BOT_NAME, BOT_VERSION), endpoint="/v1/jailed-bot")

    asyncio.run(ckit_bot_exec.run_bots_in_this_group(
        fclient,
        marketable_name=BOT_NAME,
        marketable_version_str=BOT_VERSION,
        bot_main_loop=metricmaster_main_loop,
        inprocess_tools=TOOLS,
        scenario_fn=scenario_fn,
        install_func=metricmaster_install.install,
    ))


if __name__ == "__main__":
    main()
