import logging
import time
from typing import Dict, Any, Optional, List

import gql.transport.exceptions
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.errors

from flexus_client_kit import ckit_cloudtool
from flexus_client_kit import ckit_client
from flexus_client_kit import ckit_external_auth

logger = logging.getLogger("google_tag_manager")

GOOGLE_TAG_MANAGER_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="google_tag_manager",
    description="Manage Google Tag Manager containers, tags, triggers, and variables. Call with op='help' for usage",
    parameters={
        "type": "object",
        "properties": {
            "op": {"type": "string", "description": "Start with 'help' for usage"},
            "args": {"type": "object"},
        },
        "required": []
    },
)

HELP = """
Help:

google_tag_manager(op="status")
    Show connection status and available operations.

# Account & Container Operations
google_tag_manager(op="listAccounts")
    List all GTM accounts you have access to.

google_tag_manager(op="listContainers", args={"accountId": "123456"})
    List all containers in an account.

google_tag_manager(op="getContainer", args={"accountId": "123456", "containerId": "789"})
    Get container details including container snippet code.

google_tag_manager(op="createContainer", args={
    "accountId": "123456",
    "containerName": "My Website",
    "usageContext": ["web"]  # Options: web, android, ios, amp
})
    Create a new GTM container.

# Tag Operations
google_tag_manager(op="listTags", args={"accountId": "123456", "containerId": "789", "workspaceId": "10"})
    List all tags in a workspace (workspaceId defaults to default workspace).

google_tag_manager(op="createTag", args={
    "accountId": "123456",
    "containerId": "789",
    "workspaceId": "10",
    "tagName": "GA4 Config",
    "tagType": "gaawe",  # Google Analytics: GA4 Event
    "parameters": [
        {"key": "measurementId", "type": "template", "value": "G-XXXXXXXXXX"}
    ],
    "firingTriggerId": ["2147479553"]  # All Pages trigger
})
    Create a new tag.

# Trigger Operations
google_tag_manager(op="listTriggers", args={"accountId": "123456", "containerId": "789", "workspaceId": "10"})
    List all triggers in a workspace.

google_tag_manager(op="createTrigger", args={
    "accountId": "123456",
    "containerId": "789",
    "workspaceId": "10",
    "triggerName": "Form Submit",
    "triggerType": "formSubmission",
    "filters": []
})
    Create a new trigger.

# Variable Operations
google_tag_manager(op="listVariables", args={"accountId": "123456", "containerId": "789", "workspaceId": "10"})
    List all variables in a workspace.

google_tag_manager(op="createVariable", args={
    "accountId": "123456",
    "containerId": "789",
    "workspaceId": "10",
    "variableName": "GA4 Measurement ID",
    "variableType": "c",  # Constant
    "value": "G-XXXXXXXXXX"
})
    Create a new variable.

# Version & Publishing
google_tag_manager(op="createVersion", args={
    "accountId": "123456",
    "containerId": "789",
    "workspaceId": "10",
    "versionName": "Initial Setup",
    "versionNotes": "Setup GA4 tracking"
})
    Create a container version (draft).

google_tag_manager(op="publishVersion", args={
    "accountId": "123456",
    "containerId": "789",
    "versionId": "5"
})
    Publish a container version to production.

# GA4 Integration
google_tag_manager(op="linkGA4", args={
    "accountId": "123456",
    "containerId": "789",
    "workspaceId": "10",
    "measurementId": "G-XXXXXXXXXX"
})
    Create GA4 configuration tag and link it to GTM.

# Common Usage Examples:

# 1. Get container code snippet
google_tag_manager(op="getContainer", args={
    "accountId": "123456",
    "containerId": "789"
})

# 2. Setup GA4 tracking
google_tag_manager(op="linkGA4", args={
    "accountId": "123456",
    "containerId": "789",
    "measurementId": "G-XXXXXXXXXX"
})

# 3. Create custom event tag
google_tag_manager(op="createTag", args={
    "accountId": "123456",
    "containerId": "789",
    "tagName": "Button Click Event",
    "tagType": "gaawe",
    "parameters": [
        {"key": "eventName", "type": "template", "value": "button_click"}
    ],
    "firingTriggerId": ["5"]
})
"""

GOOGLE_TAG_MANAGER_SETUP_SCHEMA = [
    {
        "bs_name": "GTM_DEFAULT_ACCOUNT",
        "bs_type": "string_short",
        "bs_default": "",
        "bs_group": "Google Tag Manager",
        "bs_description": "Default GTM account ID (optional, e.g., '123456')",
    },
    {
        "bs_name": "GTM_DEFAULT_CONTAINER",
        "bs_type": "string_short",
        "bs_default": "",
        "bs_group": "Google Tag Manager",
        "bs_description": "Default GTM container ID (optional, e.g., '789')",
    },
]

REQUIRED_SCOPES = [
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/tagmanager.readonly",
]


class IntegrationGoogleTagManager:

    def __init__(
        self,
        fclient: ckit_client.FlexusClient,
        rcx,
    ):
        self.fclient = fclient
        self.rcx = rcx
        self.token_data = None
        self.service = None

    async def _ensure_service(self) -> bool:
        if self.service and self.token_data and time.time() < self.token_data.expires_at - 60:
            return True

        try:
            self.token_data = await ckit_external_auth.get_external_auth_token(
                self.fclient,
                "google",
                self.rcx.persona.ws_id,
                self.rcx.persona.owner_fuser_id,
            )
        except gql.transport.exceptions.TransportQueryError:
            return False

        if not self.token_data:
            return False

        creds = google.oauth2.credentials.Credentials(token=self.token_data.access_token)
        self.service = googleapiclient.discovery.build('tagmanager', 'v2', credentials=creds)

        logger.info("Google Tag Manager service initialized for user %s", self.rcx.persona.owner_fuser_id)
        return True

    async def called_by_model(
        self,
        toolcall: ckit_cloudtool.FCloudtoolCall,
        model_produced_args: Optional[Dict[str, Any]]
    ) -> str:
        if not model_produced_args:
            return HELP

        op = model_produced_args.get("op", "")
        args, args_error = ckit_cloudtool.sanitize_args(model_produced_args)
        if args_error:
            return args_error

        print_help = not op or "help" in op
        print_status = not op or "status" in op

        authenticated = await self._ensure_service()

        if print_status:
            r = f"Google Tag Manager integration status:\n"
            r += f"  Authenticated: {'✅ Yes' if authenticated else '❌ No'}\n"
            r += f"  User: {self.rcx.persona.owner_fuser_id}\n"
            r += f"  Workspace: {self.rcx.persona.ws_id}\n"
            if not authenticated:
                try:
                    auth_url = await ckit_external_auth.start_external_auth_flow(
                        self.fclient,
                        "google",
                        self.rcx.persona.ws_id,
                        self.rcx.persona.owner_fuser_id,
                        REQUIRED_SCOPES,
                    )
                    r += f"\n❌ Not authenticated. Ask user to authorize at:\n{auth_url}\n"
                except gql.transport.exceptions.TransportQueryError as e:
                    r += f"\n❌ Error initiating OAuth: {e}\n"
            return r

        if print_help:
            return HELP

        if not authenticated:
            try:
                auth_url = await ckit_external_auth.start_external_auth_flow(
                    self.fclient,
                    "google",
                    self.rcx.persona.ws_id,
                    self.rcx.persona.owner_fuser_id,
                    REQUIRED_SCOPES,
                )
                return f"❌ Not authenticated. Ask user to authorize at:\n{auth_url}\n\nThen retry this operation."
            except gql.transport.exceptions.TransportQueryError as e:
                return f"❌ Failed to initiate OAuth: {e}"

        try:
            if op == "listAccounts":
                return await self._list_accounts(args)
            elif op == "listContainers":
                return await self._list_containers(args)
            elif op == "getContainer":
                return await self._get_container(args)
            elif op == "createContainer":
                return await self._create_container(toolcall, args)
            elif op == "listTags":
                return await self._list_tags(args)
            elif op == "createTag":
                return await self._create_tag(toolcall, args)
            elif op == "listTriggers":
                return await self._list_triggers(args)
            elif op == "createTrigger":
                return await self._create_trigger(toolcall, args)
            elif op == "listVariables":
                return await self._list_variables(args)
            elif op == "createVariable":
                return await self._create_variable(toolcall, args)
            elif op == "createVersion":
                return await self._create_version(toolcall, args)
            elif op == "publishVersion":
                return await self._publish_version(toolcall, args)
            elif op == "linkGA4":
                return await self._link_ga4(toolcall, args)
            else:
                return f"❌ Unknown operation: {op}\n\nTry google_tag_manager(op='help') for usage."

        except googleapiclient.errors.HttpError as e:
            if e.resp.status in (401, 403):
                self.token_data = None
                self.service = None
                auth_url = await ckit_external_auth.start_external_auth_flow(
                    self.fclient,
                    "google",
                    self.rcx.persona.ws_id,
                    self.rcx.persona.owner_fuser_id,
                    REQUIRED_SCOPES,
                )
                return f"❌ Google Tag Manager authentication error: {e.resp.status}\n\nPlease authorize at:\n{auth_url}\n\nThen retry."
            error_msg = f"Google Tag Manager API error: {e.resp.status} - {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"

    async def _list_accounts(self, args: Dict[str, Any]) -> str:
        try:
            accounts = self.service.accounts().list().execute()

            if not accounts.get("account"):
                return "📦 No Google Tag Manager accounts found."

            output = ["📦 Google Tag Manager Accounts:\n"]

            for account in accounts.get("account", []):
                account_name = account.get("name", "Unknown")
                account_id = account.get("accountId", "")
                output.append(f"• {account_name} (ID: {account_id})")

            return "\n".join(output)

        except googleapiclient.errors.HttpError as e:
            raise

    async def _list_containers(self, args: Dict[str, Any]) -> str:
        account_id = args.get("accountId", "")
        if not account_id:
            return "❌ Missing required parameter: 'accountId'"

        try:
            containers = self.service.accounts().containers().list(
                parent=f"accounts/{account_id}"
            ).execute()

            if not containers.get("container"):
                return f"📦 No containers found in account {account_id}"

            output = [f"📦 Containers in Account {account_id}:\n"]

            for container in containers.get("container", []):
                container_name = container.get("name", "Unknown")
                container_id = container.get("containerId", "")
                public_id = container.get("publicId", "")
                usage_context = ", ".join(container.get("usageContext", []))
                output.append(f"• {container_name}")
                output.append(f"  ID: {container_id}")
                output.append(f"  Public ID: {public_id}")
                output.append(f"  Type: {usage_context}\n")

            return "\n".join(output)

        except googleapiclient.errors.HttpError as e:
            raise

    async def _get_container(self, args: Dict[str, Any]) -> str:
        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")

        if not account_id or not container_id:
            return "❌ Missing required parameters: 'accountId' and 'containerId'"

        try:
            container = self.service.accounts().containers().get(
                path=f"accounts/{account_id}/containers/{container_id}"
            ).execute()

            output = [
                "📦 Container Details:\n",
                f"Name: {container.get('name', 'Unknown')}",
                f"Container ID: {container.get('containerId', '')}",
                f"Public ID: {container.get('publicId', '')}",
                f"Usage Context: {', '.join(container.get('usageContext', []))}",
                f"Time Zone: {container.get('timeZoneId', 'Unknown')}",
                "\n🔧 Container Snippet Code:",
                "\nAdd this to your website's <head> section:",
                "```html",
                f"<!-- Google Tag Manager -->",
                f"<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':",
                f"new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],",
                f"j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=",
                f"'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);",
                f"}})(window,document,'script','dataLayer','{container.get('publicId', '')}');</script>",
                f"<!-- End Google Tag Manager -->",
                "```",
                "\nAdd this immediately after opening <body> tag:",
                "```html",
                f"<!-- Google Tag Manager (noscript) -->",
                f"<noscript><iframe src=\"https://www.googletagmanager.com/ns.html?id={container.get('publicId', '')}\"",
                f"height=\"0\" width=\"0\" style=\"display:none;visibility:hidden\"></iframe></noscript>",
                f"<!-- End Google Tag Manager (noscript) -->",
                "```",
            ]

            return "\n".join(output)

        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 404:
                return f"❌ Container not found: {account_id}/{container_id}"
            raise

    async def _create_container(self, toolcall: ckit_cloudtool.FCloudtoolCall, args: Dict[str, Any]) -> str:
        if not toolcall.confirmed_by_human:
            raise ckit_cloudtool.NeedsConfirmation(
                confirm_setup_key="gtm_write",
                confirm_command=f"create container: {args.get('containerName', '')}",
                confirm_explanation="This will create a new GTM container in your account",
            )

        account_id = args.get("accountId", "")
        container_name = args.get("containerName", "")
        usage_context = args.get("usageContext", ["web"])

        if not account_id or not container_name:
            return "❌ Missing required parameters: 'accountId' and 'containerName'"

        try:
            container = self.service.accounts().containers().create(
                parent=f"accounts/{account_id}",
                body={
                    "name": container_name,
                    "usageContext": usage_context,
                }
            ).execute()

            return f"✅ Created container: {container.get('name')} (ID: {container.get('containerId')})"

        except googleapiclient.errors.HttpError as e:
            raise

    async def _list_tags(self, args: Dict[str, Any]) -> str:
        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")
        workspace_id = args.get("workspaceId", "")

        if not account_id or not container_id:
            return "❌ Missing required parameters: 'accountId' and 'containerId'"

        if not workspace_id:
            workspaces = self.service.accounts().containers().workspaces().list(
                parent=f"accounts/{account_id}/containers/{container_id}"
            ).execute()
            workspace_id = workspaces.get("workspace", [{}])[0].get("workspaceId", "")

        try:
            tags = self.service.accounts().containers().workspaces().tags().list(
                parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
            ).execute()

            if not tags.get("tag"):
                return f"🏷️ No tags found in workspace {workspace_id}"

            output = [f"🏷️ Tags in Workspace {workspace_id}:\n"]

            for tag in tags.get("tag", []):
                tag_name = tag.get("name", "Unknown")
                tag_id = tag.get("tagId", "")
                tag_type = tag.get("type", "")
                output.append(f"• {tag_name} (ID: {tag_id}, Type: {tag_type})")

            return "\n".join(output)

        except googleapiclient.errors.HttpError as e:
            raise

    async def _create_tag(self, toolcall: ckit_cloudtool.FCloudtoolCall, args: Dict[str, Any]) -> str:
        if not toolcall.confirmed_by_human:
            raise ckit_cloudtool.NeedsConfirmation(
                confirm_setup_key="gtm_write",
                confirm_command=f"create tag: {args.get('tagName', '')}",
                confirm_explanation="This will create a new tag in GTM",
            )

        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")
        workspace_id = args.get("workspaceId", "")
        tag_name = args.get("tagName", "")
        tag_type = args.get("tagType", "")
        parameters = args.get("parameters", [])
        firing_trigger_id = args.get("firingTriggerId", [])

        if not account_id or not container_id or not tag_name or not tag_type:
            return "❌ Missing required parameters: 'accountId', 'containerId', 'tagName', 'tagType'"

        if not workspace_id:
            workspaces = self.service.accounts().containers().workspaces().list(
                parent=f"accounts/{account_id}/containers/{container_id}"
            ).execute()
            workspace_id = workspaces.get("workspace", [{}])[0].get("workspaceId", "")

        try:
            tag = self.service.accounts().containers().workspaces().tags().create(
                parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}",
                body={
                    "name": tag_name,
                    "type": tag_type,
                    "parameter": parameters,
                    "firingTriggerId": firing_trigger_id,
                }
            ).execute()

            return f"✅ Created tag: {tag.get('name')} (ID: {tag.get('tagId')})"

        except googleapiclient.errors.HttpError as e:
            raise

    async def _list_triggers(self, args: Dict[str, Any]) -> str:
        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")
        workspace_id = args.get("workspaceId", "")

        if not account_id or not container_id:
            return "❌ Missing required parameters: 'accountId' and 'containerId'"

        if not workspace_id:
            workspaces = self.service.accounts().containers().workspaces().list(
                parent=f"accounts/{account_id}/containers/{container_id}"
            ).execute()
            workspace_id = workspaces.get("workspace", [{}])[0].get("workspaceId", "")

        try:
            triggers = self.service.accounts().containers().workspaces().triggers().list(
                parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
            ).execute()

            if not triggers.get("trigger"):
                return f"⚡ No triggers found in workspace {workspace_id}"

            output = [f"⚡ Triggers in Workspace {workspace_id}:\n"]

            for trigger in triggers.get("trigger", []):
                trigger_name = trigger.get("name", "Unknown")
                trigger_id = trigger.get("triggerId", "")
                trigger_type = trigger.get("type", "")
                output.append(f"• {trigger_name} (ID: {trigger_id}, Type: {trigger_type})")

            return "\n".join(output)

        except googleapiclient.errors.HttpError as e:
            raise

    async def _create_trigger(self, toolcall: ckit_cloudtool.FCloudtoolCall, args: Dict[str, Any]) -> str:
        if not toolcall.confirmed_by_human:
            raise ckit_cloudtool.NeedsConfirmation(
                confirm_setup_key="gtm_write",
                confirm_command=f"create trigger: {args.get('triggerName', '')}",
                confirm_explanation="This will create a new trigger in GTM",
            )

        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")
        workspace_id = args.get("workspaceId", "")
        trigger_name = args.get("triggerName", "")
        trigger_type = args.get("triggerType", "")
        filters = args.get("filters", [])

        if not account_id or not container_id or not trigger_name or not trigger_type:
            return "❌ Missing required parameters: 'accountId', 'containerId', 'triggerName', 'triggerType'"

        if not workspace_id:
            workspaces = self.service.accounts().containers().workspaces().list(
                parent=f"accounts/{account_id}/containers/{container_id}"
            ).execute()
            workspace_id = workspaces.get("workspace", [{}])[0].get("workspaceId", "")

        try:
            trigger = self.service.accounts().containers().workspaces().triggers().create(
                parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}",
                body={
                    "name": trigger_name,
                    "type": trigger_type,
                    "filter": filters,
                }
            ).execute()

            return f"✅ Created trigger: {trigger.get('name')} (ID: {trigger.get('triggerId')})"

        except googleapiclient.errors.HttpError as e:
            raise

    async def _list_variables(self, args: Dict[str, Any]) -> str:
        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")
        workspace_id = args.get("workspaceId", "")

        if not account_id or not container_id:
            return "❌ Missing required parameters: 'accountId' and 'containerId'"

        if not workspace_id:
            workspaces = self.service.accounts().containers().workspaces().list(
                parent=f"accounts/{account_id}/containers/{container_id}"
            ).execute()
            workspace_id = workspaces.get("workspace", [{}])[0].get("workspaceId", "")

        try:
            variables = self.service.accounts().containers().workspaces().variables().list(
                parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
            ).execute()

            if not variables.get("variable"):
                return f"📊 No variables found in workspace {workspace_id}"

            output = [f"📊 Variables in Workspace {workspace_id}:\n"]

            for variable in variables.get("variable", []):
                variable_name = variable.get("name", "Unknown")
                variable_id = variable.get("variableId", "")
                variable_type = variable.get("type", "")
                output.append(f"• {variable_name} (ID: {variable_id}, Type: {variable_type})")

            return "\n".join(output)

        except googleapiclient.errors.HttpError as e:
            raise

    async def _create_variable(self, toolcall: ckit_cloudtool.FCloudtoolCall, args: Dict[str, Any]) -> str:
        if not toolcall.confirmed_by_human:
            raise ckit_cloudtool.NeedsConfirmation(
                confirm_setup_key="gtm_write",
                confirm_command=f"create variable: {args.get('variableName', '')}",
                confirm_explanation="This will create a new variable in GTM",
            )

        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")
        workspace_id = args.get("workspaceId", "")
        variable_name = args.get("variableName", "")
        variable_type = args.get("variableType", "")
        value = args.get("value", "")

        if not account_id or not container_id or not variable_name or not variable_type:
            return "❌ Missing required parameters: 'accountId', 'containerId', 'variableName', 'variableType'"

        if not workspace_id:
            workspaces = self.service.accounts().containers().workspaces().list(
                parent=f"accounts/{account_id}/containers/{container_id}"
            ).execute()
            workspace_id = workspaces.get("workspace", [{}])[0].get("workspaceId", "")

        try:
            variable = self.service.accounts().containers().workspaces().variables().create(
                parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}",
                body={
                    "name": variable_name,
                    "type": variable_type,
                    "parameter": [
                        {"key": "value", "type": "template", "value": value}
                    ] if value else [],
                }
            ).execute()

            return f"✅ Created variable: {variable.get('name')} (ID: {variable.get('variableId')})"

        except googleapiclient.errors.HttpError as e:
            raise

    async def _create_version(self, toolcall: ckit_cloudtool.FCloudtoolCall, args: Dict[str, Any]) -> str:
        if not toolcall.confirmed_by_human:
            raise ckit_cloudtool.NeedsConfirmation(
                confirm_setup_key="gtm_write",
                confirm_command=f"create version: {args.get('versionName', '')}",
                confirm_explanation="This will create a new container version",
            )

        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")
        workspace_id = args.get("workspaceId", "")
        version_name = args.get("versionName", "")
        version_notes = args.get("versionNotes", "")

        if not account_id or not container_id:
            return "❌ Missing required parameters: 'accountId' and 'containerId'"

        if not workspace_id:
            workspaces = self.service.accounts().containers().workspaces().list(
                parent=f"accounts/{account_id}/containers/{container_id}"
            ).execute()
            workspace_id = workspaces.get("workspace", [{}])[0].get("workspaceId", "")

        try:
            version = self.service.accounts().containers().workspaces().create_version(
                path=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}",
                body={
                    "name": version_name,
                    "notes": version_notes,
                }
            ).execute()

            container_version = version.get("containerVersion", {})
            return f"✅ Created version: {container_version.get('name')} (ID: {container_version.get('containerVersionId')})"

        except googleapiclient.errors.HttpError as e:
            raise

    async def _publish_version(self, toolcall: ckit_cloudtool.FCloudtoolCall, args: Dict[str, Any]) -> str:
        if not toolcall.confirmed_by_human:
            raise ckit_cloudtool.NeedsConfirmation(
                confirm_setup_key="gtm_publish",
                confirm_command=f"publish version {args.get('versionId', '')}",
                confirm_explanation="This will publish the container version to PRODUCTION",
            )

        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")
        version_id = args.get("versionId", "")

        if not account_id or not container_id or not version_id:
            return "❌ Missing required parameters: 'accountId', 'containerId', 'versionId'"

        try:
            published = self.service.accounts().containers().versions().publish(
                path=f"accounts/{account_id}/containers/{container_id}/versions/{version_id}"
            ).execute()

            return f"✅ Published version to production: {published.get('containerVersion', {}).get('name')}"

        except googleapiclient.errors.HttpError as e:
            raise

    async def _link_ga4(self, toolcall: ckit_cloudtool.FCloudtoolCall, args: Dict[str, Any]) -> str:
        if not toolcall.confirmed_by_human:
            raise ckit_cloudtool.NeedsConfirmation(
                confirm_setup_key="gtm_write",
                confirm_command=f"link GA4 measurement ID: {args.get('measurementId', '')}",
                confirm_explanation="This will create GA4 configuration tag in GTM",
            )

        account_id = args.get("accountId", "")
        container_id = args.get("containerId", "")
        workspace_id = args.get("workspaceId", "")
        measurement_id = args.get("measurementId", "")

        if not account_id or not container_id or not measurement_id:
            return "❌ Missing required parameters: 'accountId', 'containerId', 'measurementId'"

        if not workspace_id:
            workspaces = self.service.accounts().containers().workspaces().list(
                parent=f"accounts/{account_id}/containers/{container_id}"
            ).execute()
            workspace_id = workspaces.get("workspace", [{}])[0].get("workspaceId", "")

        triggers = self.service.accounts().containers().workspaces().triggers().list(
            parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}"
        ).execute()
        all_pages_trigger_id = None
        for trigger in triggers.get("trigger", []):
            if trigger.get("type") == "pageview":
                all_pages_trigger_id = trigger.get("triggerId")
                break

        if not all_pages_trigger_id:
            return "❌ Could not find 'All Pages' trigger. Create a pageview trigger first."

        try:
            tag = self.service.accounts().containers().workspaces().tags().create(
                parent=f"accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}",
                body={
                    "name": "GA4 Configuration",
                    "type": "gaawe",
                    "parameter": [
                        {"key": "measurementId", "type": "template", "value": measurement_id}
                    ],
                    "firingTriggerId": [all_pages_trigger_id],
                }
            ).execute()

            return f"✅ Created GA4 configuration tag: {tag.get('name')} (ID: {tag.get('tagId')})\n\nGA4 is now linked to GTM. Create a version and publish to make it live."

        except googleapiclient.errors.HttpError as e:
            raise
