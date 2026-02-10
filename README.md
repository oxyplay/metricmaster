# MetricMaster BOT

MetricMaster is a comprehensive Flexus bot that helps users set up and manage Google Analytics 4 (GA4) and Google Tag Manager (GTM) for their websites.

## Features

### 1. OAuth Authentication
- Seamless Google OAuth2 integration for GA4 and GTM
- Automatic token refresh
- Secure credential management

### 2. Account Setup
- List existing GA4 properties and GTM accounts
- Guide users through creating new properties/containers
- Check current configuration status

### 3. GTM Container Deployment
- Generate GTM container code snippets
- Provide clear installation instructions for website integration
- Option to create GitHub PRs for automated code deployment

### 4. GA4 Integration
- Automatically link GA4 measurement IDs to GTM containers
- Create GA4 configuration tags
- Set up proper tag firing triggers

### 5. Event Tracking Setup
- Comprehensive event tracking configuration:
  - Page views
  - Button clicks
  - Form submissions
  - E-commerce events (purchase, add_to_cart, etc.)
  - Custom events
- Industry-specific event recommendations:
  - E-commerce: purchase, cart, checkout events
  - Lead Generation: form_submit, sign_up, contact events
  - Content/Media: video tracking, downloads, searches
  - SaaS: trial_start, feature_usage, subscriptions

### 6. Analytics Reports
- Traffic reports (users, sessions, pageviews)
- Conversion tracking and analysis
- E-commerce performance reports
- Funnel analysis with drop-off rates
- Custom queries with filters and dimensions

### 7. Scheduled Reports
- Automated daily/weekly/monthly reports
- Configurable metrics and dimensions
- Save reports to policy documents or MongoDB
- Email delivery (when integrated)

## Installation

```bash
# Install the package
pip install -e /workspace

# Install the bot in your Flexus workspace
python -m metricmaster.metricmaster_install --ws=$FLEXUS_WORKSPACE
```

## Bot Structure

```
metricmaster/
├── __init__.py
├── metricmaster_bot.py          # Main bot logic and event loop
├── metricmaster_prompts.py      # System prompts for experts
├── metricmaster_install.py      # Marketplace registration
├── metricmaster-1024x1536.webp  # Big marketplace image
├── metricmaster-256x256.webp    # Avatar image
├── tools/
│   ├── __init__.py
│   ├── fi_google_tag_manager.py      # GTM API integration
│   └── fi_google_analytics_enhanced.py  # Enhanced GA4 features
└── forms/                        # Custom HTML forms (optional)
```

## Configuration

The bot uses the following setup schema:

### Google Analytics
- `GA_DEFAULT_PROPERTY`: Default GA4 property ID (optional)

### Google Tag Manager
- `GTM_DEFAULT_ACCOUNT`: Default GTM account ID (optional)
- `GTM_DEFAULT_CONTAINER`: Default GTM container ID (optional)

### GitHub Integration
- `GITHUB_REPO_URL`: Repository URL for automated PR creation (optional)

### Scheduled Reports
- `SCHEDULED_REPORTS`: List of configured automated reports with:
  - `report_name`: Name of the report
  - `frequency`: daily, weekly, or monthly
  - `property_id`: GA4 property ID
  - `metrics`: Comma-separated metrics (e.g., "totalUsers,sessions")
  - `dimensions`: Comma-separated dimensions (e.g., "date,country")

## Tools

### google_analytics
- List properties
- Get property details
- Generate standard reports
- Track user activity

### google_analytics_enhanced
- Advanced event tracking
- Conversion reports
- E-commerce analytics
- Funnel analysis
- Custom queries with filters

### google_tag_manager
- List accounts and containers
- Create/manage containers
- Create/manage tags, triggers, and variables
- Link GA4 to GTM
- Create and publish versions

### Supporting Tools
- `flexus_policy_document`: Save configurations and reports
- `mongo_store`: Store generated files and exports
- `ask_questions`: Interactive user input collection

## Usage Examples

### Initial Setup
```
User: Help me set up Google Analytics 4 and Tag Manager
Bot: I'll check your current setup and guide you through the process...
     [Checks authentication, lists accounts, guides through creation]
```

### Generate Report
```
User: Show me traffic for the last 30 days
Bot: [Generates report with users, sessions, pageviews by date]
```

### Event Tracking
```
User: Set up tracking for form submissions
Bot: I'll create a form submission trigger and GA4 event tag...
     [Creates trigger, creates tag, publishes version]
```

### Scheduled Reports
```
User: Set up a weekly traffic report
Bot: [Configures scheduled report in setup, saves to policy documents]
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

### Running the Bot
```bash
# Set required environment variables
export FLEXUS_API_BASEURL="..."
export FLEXUS_API_KEY="..."
export FLEXUS_WORKSPACE="..."

# Run the bot
python -m metricmaster.metricmaster_bot
```

## Architecture

### Main Loop
The bot uses an event-driven architecture with handlers for:
- Tool calls (GA4, GTM operations)
- Message updates
- Thread updates
- Kanban task updates

### OAuth Flow
1. Bot checks for existing token
2. If not authenticated, generates OAuth URL
3. User authorizes in browser
4. Token is stored and auto-refreshed
5. API calls use refreshed tokens

### Scheduled Operations
- Task sorting: Every 10 minutes
- Task processing: Every 5 minutes
- Report generation: Daily at 9 AM (weekdays)

## API Keys Required

The following Google API scopes are required:
- `https://www.googleapis.com/auth/analytics.readonly`
- `https://www.googleapis.com/auth/tagmanager.edit.containers`
- `https://www.googleapis.com/auth/tagmanager.readonly`

OAuth is handled automatically through the Flexus platform.

## Best Practices

1. **Always check authentication first**: Call status on both tools before operations
2. **Explain before creating**: Show users what will be created before confirmation
3. **Document configurations**: Save important setup details to policy documents
4. **Test before publishing**: Create GTM versions before publishing to production
5. **Provide clear instructions**: Include code snippets with exact placement details

## Troubleshooting

### Authentication Issues
- Ensure OAuth flow is completed
- Check that required scopes are granted
- Verify token expiration and refresh

### GTM Changes Not Appearing
- Remember to create a version after making changes
- Publish the version to production
- Clear browser cache if testing

### Missing Data in Reports
- Check that GTM container is installed on website
- Verify GA4 configuration tag is firing
- Allow 24-48 hours for data to appear in reports

## License

This bot is part of the Flexus ecosystem.

## Support

For issues or questions, please report at:
https://github.com/anthropics/claude-code/issues
