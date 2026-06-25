# Multi-API Setup Guide for Claude Code Telegram Bot

This guide shows you how to set up the enhanced claude-code-telegram bot with multiple API providers and dynamic switching capabilities.

## 🌟 Features

- **Multiple API Support**: Claude, OpenAI, Ollama (Local LLM)
- **Dynamic Switching**: Automatic provider switching based on cost, time, or conditions
- **Cost Tracking**: Monitor usage and costs per provider
- **Fallback Support**: Automatic fallback if primary provider fails
- **Flexible Configuration**: Easy switching between APIs at runtime

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Or if Poetry fails, use pip with system packages
pip install httpx python-dotenv structlog --break-system-packages --user
```

### 2. Set Up Ollama (Local LLM)

```bash
# Check if Ollama is installed
which ollama

# Pull a model
ollama pull llama3:8b

# Start Ollama service (if not running)
ollama serve
```

### 3. Configure Environment

Copy the enhanced configuration:

```bash
# Copy multi-API configuration
cp .env.multiapi .env

# Edit the configuration
nano .env
```

### 4. Basic Configuration

```bash
# Required settings
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=your_bot_username
APPROVED_DIRECTORY=/path/to/your/projects

# API Provider Configuration
PRIMARY_API_PROVIDER=ollama  # or claude, openai, local
OLLAMA_MODEL=llama3:8b
OLLAMA_API_URL=http://localhost:11434
```

## 🔧 Configuration Options

### API Provider Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `PRIMARY_API_PROVIDER` | Main API to use | `claude` |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OLLAMA_MODEL` | Local model name | `llama3:8b` |
| `OLLAMA_API_URL` | Ollama endpoint | `http://localhost:11434` |

### Dynamic Switching Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `ENABLE_DYNAMIC_SWITCHING` | Enable automatic switching | `true` |
| `COST_SWITCH_THRESHOLD` | Switch to local when cost reaches | `$5.00` |
| `LOCAL_HOURS_START` | Start local hours (24h) | - |
| `LOCAL_HOURS_END` | End local hours (24h) | - |
| `ENABLE_WEEKEND_LOCAL` | Use local on weekends | `true` |

### Fallback Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `FALLBACK_API_PROVIDER` | Backup provider | `local` |
| `ENABLE_AUTO_FALLBACK` | Auto-fallback on error | `true` |

## 📱 Usage Examples

### Example 1: Cost-Aware Configuration

```bash
# .env file
PRIMARY_API_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-api...
ANTHROPIC_MODEL=claude-3-sonnet-20240229
COST_SWITCH_THRESHOLD=5.0
FALLBACK_API_PROVIDER=ollama
OLLAMA_MODEL=llama3:8b
```

**Behavior**: Uses Claude API until $5.00 is spent, then switches to Ollama.

### Example 2: Time-Based Configuration

```bash
# .env file
PRIMARY_API_PROVIDER=claude
LOCAL_HOURS_START=18  # 6 PM
LOCAL_HOURS_END=9      # 9 AM (next day)
ENABLE_WEEKEND_LOCAL=true
```

**Behavior**: Uses Ollama after 6 PM until 9 AM next day, and all day on weekends.

### Example 3: Simple Local Setup

```bash
# .env file
PRIMARY_API_PROVIDER=ollama
OLLAMA_MODEL=llama3:8b
OLLAMA_MAX_TOKENS=2000
```

**Behavior**: Always uses Ollama (free local model).

## 🔄 Dynamic Switching Scenarios

### Cost-Based Switching
- User starts with Claude API (expensive)
- After $5.00 usage, automatically switches to Ollama (free)
- Usage resets monthly

### Time-Based Switching
- Work hours (9 AM - 6 PM): Claude API for best performance
- Evenings/weekends: Ollama to save costs

### Error-Based Fallback
- Primary API fails → automatically try fallback
- Logs the switch for debugging

## 🧪 Testing

### Test Individual APIs

```bash
# Test Ollama directly
python3 simple_test.py

# Test multi-API configuration
python3 test_multi_api.py
```

### Test Chat Completion

```bash
# Start the bot
python -m src.main

# Or with poetry
poetry run python -m src.main
```

## 🔐 Security Considerations

1. **API Keys**: Store keys securely, never commit to git
2. **User Whitelisting**: Always specify `ALLOWED_USERS`
3. **Directory Restrictions**: Use `APPROVED_DIRECTORY` to limit access
4. **Rate Limiting**: Configure rate limits to prevent abuse

## 📊 Monitoring

### Cost Tracking

```python
# In your code
from src.config.multi_settings import create_settings

settings = create_settings()
multi_api_manager = MultiAPIManager(settings)

# Get user cost summary
cost_summary = await multi_api_manager.get_user_cost_summary(user_id)
print(f"Total cost: ${cost_summary['total']['cost_usd']}")
```

### Provider Information

```python
# Get current provider info
provider_info = multi_api_manager.get_provider_info(user_id)
print(f"Using: {provider_info['current_provider']}")
print(f"Available: {provider_info['available_providers']}")
```

## 🚨 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   ```bash
   # Check Ollama is running
   ollama list

   # Check port is accessible
   curl http://localhost:11434/api/tags
   ```

2. **API Key Errors**
   - Verify keys are correct
   - Check API permissions
   - Ensure URLs are correct

3. **Import Errors**
   ```bash
   # Install missing dependencies
   poetry install
   # Or
   pip install httpx python-dotenv structlog --break-system-packages --user
   ```

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG
DEBUG=true
```

## 🎯 Next Steps

1. **Set up Telegram Bot**: Create bot with @BotFather
2. **Configure Environment**: Edit `.env` with your settings
3. **Test APIs**: Verify each provider works
4. **Start Bot**: Run the main application
5. **Monitor Usage**: Track costs and performance

## 🔄 Migration from Original

If you're migrating from the original claude-code-telegram:

1. Backup your `.env` file
2. Copy the new configuration options you want
3. The bot will automatically use the new multi-API system
4. Test thoroughly with your providers

## 📚 Advanced Configuration

### Custom Provider Logic

Extend the `MultiAPIManager` class to add custom switching logic:

```python
class CustomMultiAPIManager(MultiAPIManager):
    async def get_current_provider(self, user_id: int) -> APIProvider:
        # Add your custom logic here
        # Check user preferences, time of day, etc.
        return super().get_current_provider(user_id)
```

### Multiple Fallback Levels

Configure multiple fallback providers:

```bash
# In settings.py or configuration
FALLBACK_CHAIN = ["ollama", "openai", "claude"]
```

## 🎉 Conclusion

You now have a flexible, multi-API Claude Code Telegram bot that can:

- Switch between Claude, OpenAI, and Local LLMs
- Automatically optimize for cost vs. performance
- Handle failures gracefully with fallback providers
- Adapt to different usage patterns and preferences

Start with a simple configuration and gradually add more complexity as needed!