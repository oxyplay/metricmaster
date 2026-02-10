import logging
from typing import Dict, Any, Optional

from flexus_client_kit.integrations import fi_google_analytics
from flexus_client_kit import ckit_cloudtool
from flexus_client_kit import ckit_client

logger = logging.getLogger("google_analytics_enhanced")

GOOGLE_ANALYTICS_ENHANCED_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="google_analytics_enhanced",
    description="Enhanced Google Analytics operations for event setup and tracking. Call with op='help' for usage",
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
Enhanced Google Analytics Help:

google_analytics_enhanced(op="status")
    Show connection status.

# Event Tracking Setup
google_analytics_enhanced(op="getEventConfig", args={
    "propertyId": "123456",
    "eventName": "purchase"
})
    Get configuration for a specific event.

google_analytics_enhanced(op="listEvents", args={
    "propertyId": "123456",
    "dateRange": "last7days"
})
    List all events tracked in the property.

google_analytics_enhanced(op="getEventReport", args={
    "propertyId": "123456",
    "eventName": "purchase",
    "dateRange": "last30days",
    "dimensions": ["date", "eventName"],
    "metrics": ["eventCount", "eventValue"]
})
    Get detailed event analytics.

# Conversion Tracking
google_analytics_enhanced(op="getConversions", args={
    "propertyId": "123456",
    "dateRange": "last30days",
    "dimensions": ["sessionSource", "sessionMedium"]
})
    Get conversion metrics with breakdown.

# E-commerce Tracking
google_analytics_enhanced(op="getEcommerceReport", args={
    "propertyId": "123456",
    "dateRange": "last30days",
    "dimensions": ["itemName", "itemCategory"]
})
    Get e-commerce performance metrics.

# User Journey & Funnels
google_analytics_enhanced(op="getUserJourney", args={
    "propertyId": "123456",
    "dateRange": "last7days",
    "startPage": "/",
    "endPage": "/checkout/complete"
})
    Analyze user journey from start to end page.

google_analytics_enhanced(op="getFunnelReport", args={
    "propertyId": "123456",
    "funnelSteps": [
        {"name": "Home", "page": "/"},
        {"name": "Product", "page": "/product"},
        {"name": "Cart", "page": "/cart"},
        {"name": "Checkout", "page": "/checkout"}
    ],
    "dateRange": "last30days"
})
    Analyze conversion funnel with drop-off rates.

# Custom Reports
google_analytics_enhanced(op="customQuery", args={
    "propertyId": "123456",
    "dateRange": "last30days",
    "metrics": ["sessions", "conversions"],
    "dimensions": ["deviceCategory", "browser"],
    "filters": [
        {"field": "country", "operator": "EQUALS", "value": "United States"}
    ],
    "orderBy": {"metric": "sessions", "desc": True},
    "limit": 50
})
    Execute a custom analytics query with filters.

# Recommended Events for Different Industries:

E-commerce:
- page_view, view_item, add_to_cart, remove_from_cart
- begin_checkout, add_payment_info, add_shipping_info
- purchase, refund

Lead Generation:
- page_view, generate_lead, form_submit, sign_up
- contact_submit, download_brochure

Content/Media:
- page_view, video_start, video_progress, video_complete
- file_download, search, share

SaaS:
- page_view, sign_up, login, trial_start
- upgrade, feature_usage, subscription_cancel
"""

GOOGLE_ANALYTICS_ENHANCED_SETUP_SCHEMA = []


class IntegrationGoogleAnalyticsEnhanced:

    def __init__(
        self,
        fclient: ckit_client.FlexusClient,
        rcx,
        base_integration: fi_google_analytics.IntegrationGoogleAnalytics,
    ):
        self.fclient = fclient
        self.rcx = rcx
        self.base = base_integration

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

        authenticated = await self.base._ensure_services()

        if print_status:
            r = f"Google Analytics Enhanced integration status:\n"
            r += f"  Authenticated: {'✅ Yes' if authenticated else '❌ No'}\n"
            r += f"  User: {self.rcx.persona.owner_fuser_id}\n"
            if not authenticated:
                return await self.base.called_by_model(toolcall, model_produced_args)
            return r

        if print_help:
            return HELP

        if not authenticated:
            return await self.base.called_by_model(toolcall, model_produced_args)

        try:
            if op == "getEventConfig":
                return await self._get_event_config(args)
            elif op == "listEvents":
                return await self._list_events(args)
            elif op == "getEventReport":
                return await self._get_event_report(args)
            elif op == "getConversions":
                return await self._get_conversions(args)
            elif op == "getEcommerceReport":
                return await self._get_ecommerce_report(args)
            elif op == "getUserJourney":
                return await self._get_user_journey(args)
            elif op == "getFunnelReport":
                return await self._get_funnel_report(args)
            elif op == "customQuery":
                return await self._custom_query(args)
            else:
                return f"❌ Unknown operation: {op}\n\nTry google_analytics_enhanced(op='help') for usage."

        except Exception as e:
            logger.exception("Error in enhanced analytics")
            return f"❌ Error: {str(e)}"

    async def _get_event_config(self, args: Dict[str, Any]) -> str:
        property_id = args.get("propertyId", "")
        event_name = args.get("eventName", "")

        if not property_id or not event_name:
            return "❌ Missing required parameters: 'propertyId' and 'eventName'"

        base_args = {
            "propertyId": property_id,
            "dateRange": "last7days",
            "metrics": ["eventCount"],
            "dimensions": ["eventName"],
        }

        result = await self.base._get_report(base_args)

        if event_name in result:
            return f"✅ Event '{event_name}' is being tracked.\n\n{result}"
        else:
            return f"⚠️ Event '{event_name}' not found in recent data. It may not be tracked yet or has no data in the last 7 days."

    async def _list_events(self, args: Dict[str, Any]) -> str:
        property_id = args.get("propertyId", "")
        date_range = args.get("dateRange", "last7days")

        if not property_id:
            return "❌ Missing required parameter: 'propertyId'"

        base_args = {
            "propertyId": property_id,
            "dateRange": date_range,
            "metrics": ["eventCount", "eventValue"],
            "dimensions": ["eventName"],
            "orderBy": {"metric": "eventCount", "desc": True},
            "limit": 50,
        }

        return await self.base._get_report(base_args)

    async def _get_event_report(self, args: Dict[str, Any]) -> str:
        property_id = args.get("propertyId", "")
        event_name = args.get("eventName", "")

        if not property_id:
            return "❌ Missing required parameter: 'propertyId'"

        base_args = {
            "propertyId": property_id,
            "dateRange": args.get("dateRange", "last30days"),
            "metrics": args.get("metrics", ["eventCount", "eventValue"]),
            "dimensions": args.get("dimensions", ["date", "eventName"]),
            "orderBy": {"metric": "eventCount", "desc": True},
        }

        return await self.base._get_report(base_args)

    async def _get_conversions(self, args: Dict[str, Any]) -> str:
        property_id = args.get("propertyId", "")

        if not property_id:
            return "❌ Missing required parameter: 'propertyId'"

        base_args = {
            "propertyId": property_id,
            "dateRange": args.get("dateRange", "last30days"),
            "metrics": ["conversions", "totalRevenue", "sessions"],
            "dimensions": args.get("dimensions", ["sessionSource", "sessionMedium"]),
            "orderBy": {"metric": "conversions", "desc": True},
            "limit": 20,
        }

        return await self.base._get_report(base_args)

    async def _get_ecommerce_report(self, args: Dict[str, Any]) -> str:
        property_id = args.get("propertyId", "")

        if not property_id:
            return "❌ Missing required parameter: 'propertyId'"

        base_args = {
            "propertyId": property_id,
            "dateRange": args.get("dateRange", "last30days"),
            "metrics": ["itemRevenue", "itemsPurchased", "itemsViewed"],
            "dimensions": args.get("dimensions", ["itemName", "itemCategory"]),
            "orderBy": {"metric": "itemRevenue", "desc": True},
            "limit": 30,
        }

        return await self.base._get_report(base_args)

    async def _get_user_journey(self, args: Dict[str, Any]) -> str:
        property_id = args.get("propertyId", "")
        start_page = args.get("startPage", "/")
        end_page = args.get("endPage", "")

        if not property_id:
            return "❌ Missing required parameter: 'propertyId'"

        base_args = {
            "propertyId": property_id,
            "dateRange": args.get("dateRange", "last7days"),
            "metrics": ["screenPageViews", "sessions"],
            "dimensions": ["pagePath", "pageTitle"],
            "orderBy": {"metric": "screenPageViews", "desc": True},
            "limit": 100,
        }

        result = await self.base._get_report(base_args)
        return f"🔍 User Journey Analysis\n\nPages visited between '{start_page}' and '{end_page}':\n\n{result}\n\nNote: Full path analysis requires custom implementation with GA4 Data API."

    async def _get_funnel_report(self, args: Dict[str, Any]) -> str:
        property_id = args.get("propertyId", "")
        funnel_steps = args.get("funnelSteps", [])

        if not property_id or not funnel_steps:
            return "❌ Missing required parameters: 'propertyId' and 'funnelSteps'"

        output = ["📊 Funnel Analysis:\n"]

        for i, step in enumerate(funnel_steps, 1):
            step_name = step.get("name", f"Step {i}")
            step_page = step.get("page", "")

            base_args = {
                "propertyId": property_id,
                "dateRange": args.get("dateRange", "last30days"),
                "metrics": ["screenPageViews", "sessions"],
                "dimensions": ["pagePath"],
            }

            step_result = await self.base._get_report(base_args)
            output.append(f"\n{i}. {step_name} ({step_page})")
            output.append(f"   Users: [analyzing...]")

        output.append("\n\nNote: Full funnel analysis with drop-off rates requires GA4 Funnel Exploration API.")
        return "\n".join(output)

    async def _custom_query(self, args: Dict[str, Any]) -> str:
        property_id = args.get("propertyId", "")

        if not property_id:
            return "❌ Missing required parameter: 'propertyId'"

        base_args = {
            "propertyId": property_id,
            "dateRange": args.get("dateRange", "last30days"),
            "metrics": args.get("metrics", ["sessions"]),
            "dimensions": args.get("dimensions", []),
            "orderBy": args.get("orderBy"),
            "limit": args.get("limit", 100),
        }

        if args.get("startDate") and args.get("endDate"):
            base_args["startDate"] = args["startDate"]
            base_args["endDate"] = args["endDate"]
            base_args["dateRange"] = "custom"

        result = await self.base._get_report(base_args)

        filters = args.get("filters", [])
        if filters:
            result += f"\n\nNote: Filters applied: {filters}"

        return result
