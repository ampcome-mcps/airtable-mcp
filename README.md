# Airtable MCP Server

A comprehensive Model Context Protocol (MCP) server that provides seamless integration with the Airtable API. This server enables AI assistants to interact with your Airtable bases, tables, records, and more through a secure OAuth connection managed by Nango.

## 🚀 Features

### Complete Airtable API Coverage
- **📊 Records**: Create, read, update, delete records (single & bulk operations)
- **🗄️ Bases**: Manage bases, schemas, and collaborators
- **📋 Tables**: Create and modify table structures
- **🏷️ Fields**: Add and update field types and properties
- **👀 Views**: List and manage different table views
- **💬 Comments**: Full comment management on records
- **🔗 Webhooks**: Set up and manage real-time notifications
- **👥 Collaborators**: Manage base and workspace permissions
- **🏢 Enterprise**: Enterprise account and user management
- **🔗 Shares**: Manage public sharing settings

### Developer-Friendly Features
- **🔒 Secure OAuth**: Authentication via Nango integration
- **📝 Structured Output**: Type-safe responses using Pydantic models
- **🛡️ Error Handling**: Comprehensive error handling with detailed messages
- **🔄 Auto Token Refresh**: Automatic OAuth token refresh
- **📡 STDIO Transport**: Standard input/output communication

## 📋 Prerequisites

- Python 3.8+
- Airtable account with API access
- Nango account and integration setup

## 🛠️ Installation

### 1. Install Dependencies

```bash
pip install fastmcp requests pydantic
```

### 2. Set Up Nango Integration

1. Create a [Nango account](https://www.nango.dev/)
2. Set up an Airtable integration in your Nango dashboard
3. Configure OAuth credentials for Airtable
4. Create a connection for your Airtable account

### 3. Configure Environment Variables

Create a `.env` file or export the following variables:

```bash
# Required Nango Configuration
export NANGO_CONNECTION_ID="your_connection_id"
export NANGO_INTEGRATION_ID="your_integration_id"
export NANGO_BASE_URL="https://api.nango.dev"
export NANGO_SECRET_KEY="your_nango_secret_key"
```

### 4. Run the Server

```bash
python main.py
```

## 🔧 Configuration

### Finding Your Nango Credentials

1. **NANGO_CONNECTION_ID**: Found in your Nango dashboard under "Connections"
2. **NANGO_INTEGRATION_ID**: Your integration key from the Nango dashboard
3. **NANGO_BASE_URL**: Usually `https://api.nango.dev` (or your self-hosted URL)
4. **NANGO_SECRET_KEY**: Your Nango secret key from the dashboard

## 🎯 Usage Examples

### Basic Record Operations

```python
# List all records in a table
records = list_records(
    base_id="appXXXXXXXXXXXXXX",
    table_id_or_name="tblYYYYYYYYYYYYYY"
)

# Create a new record
new_record = create_records(
    base_id="appXXXXXXXXXXXXXX",
    table_id_or_name="tblYYYYYYYYYYYYYY",
    records=[{
        "fields": {
            "Name": "John Doe",
            "Email": "john@example.com"
        }
    }]
)

# Update a record
updated_record = update_record(
    base_id="appXXXXXXXXXXXXXX",
    table_id_or_name="tblYYYYYYYYYYYYYY",
    record_id="recZZZZZZZZZZZZZZ",
    fields={
        "Status": "Complete"
    }
)
```

### Advanced Filtering and Sorting

```python
# Get filtered and sorted records
filtered_records = list_records(
    base_id="appXXXXXXXXXXXXXX",
    table_id_or_name="Tasks",
    filter_by_formula="AND({Status} = 'In Progress', {Priority} = 'High')",
    sort=[
        {"field": "Due Date", "direction": "asc"},
        {"field": "Priority", "direction": "desc"}
    ],
    max_records=50
)
```

### Webhook Management

```python
# Create a webhook
webhook = create_webhook(
    base_id="appXXXXXXXXXXXXXX",
    notification_url="https://your-app.com/webhook",
    specification={
        "options": {
            "filters": {
                "dataTypes": ["tableData"],
                "changeTypes": ["add", "update", "remove"]
            }
        }
    }
)

# List webhook payloads
payloads = list_webhook_payloads(
    base_id="appXXXXXXXXXXXXXX",
    webhook_id="webhook_id_here"
)
```

## 🔍 Available Tools

### Records Management
- `list_records()` - List records with filtering, sorting, and pagination
- `get_record()` - Get a single record by ID
- `create_records()` - Create single or multiple records
- `update_record()` - Update a single record
- `update_multiple_records()` - Bulk update records
- `delete_record()` - Delete a single record
- `delete_multiple_records()` - Bulk delete records

### Base & Schema Management
- `list_bases()` - List all accessible bases
- `get_base_schema()` - Get complete base schema
- `create_base()` - Create a new base
- `create_table()` - Create a new table
- `update_table()` - Update table metadata
- `create_field()` - Add new fields
- `update_field()` - Modify field properties

### Views & Comments
- `list_views()` - List all views in a base
- `get_view_metadata()` - Get view configuration
- `list_comments()` - Get record comments
- `create_comment()` - Add comments to records
- `update_comment()` - Edit existing comments
- `delete_comment()` - Remove comments

### Collaboration & Sharing
- `get_base_collaborators()` - List base collaborators
- `add_base_collaborator()` - Add new collaborators
- `update_collaborator_base_permission()` - Change permissions
- `list_shares()` - List public shares
- `delete_share()` - Remove public shares

### Webhooks & Automation
- `list_webhooks()` - List all webhooks
- `create_webhook()` - Set up new webhooks
- `delete_webhook()` - Remove webhooks
- `list_webhook_payloads()` - Get webhook events
- `enable_disable_webhook_notifications()` - Toggle notifications

### Authentication & Diagnostics
- `test_nango_connection()` - Test Nango OAuth connection
- `get_auth_status()` - Check authentication status
- `get_user_info()` - Get current user information

## 🔒 Security

- **OAuth 2.0**: Secure authentication via Nango
- **Token Refresh**: Automatic token refresh for long-running sessions
- **Environment Variables**: Sensitive credentials stored in environment variables
- **Error Handling**: Detailed error messages without exposing sensitive data

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Test your Nango connection
   python -c "from main import test_nango_connection; print(test_nango_connection())"
   ```

2. **Missing Environment Variables**
   ```bash
   # Check if all variables are set
   echo $NANGO_CONNECTION_ID
   echo $NANGO_INTEGRATION_ID
   echo $NANGO_BASE_URL
   echo $NANGO_SECRET_KEY
   ```

3. **Connection Issues**
   - Verify your Nango integration is properly configured
   - Check that your Airtable OAuth app has the correct permissions
   - Ensure your connection ID is active in Nango

### Debug Mode

Enable detailed logging by setting:
```bash
export DEBUG=1
```

## 📚 API Reference

All tools return structured responses with proper error handling. Responses follow this general pattern:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

Error responses:
```json
{
  "success": false,
  "error": "Detailed error message",
  "status_code": 400
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check the [Airtable API Documentation](https://airtable.com/developers/web/api)
- **Nango Setup**: Visit [Nango Documentation](https://docs.nango.dev/)

## 🔗 Related Links

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/modelcontextprotocol/python-sdk)
- [Airtable API Reference](https://airtable.com/developers/web/api/introduction)
- [Nango Integration Guide](https://docs.nango.dev/integrations/airtable)

---

Made with ❤️ for the MCP community