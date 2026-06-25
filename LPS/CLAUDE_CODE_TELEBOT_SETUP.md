# Claude Code Telebot Setup Complete! 🤖

**Created:** 2026-01-09
**Location:** `/Users/LPS/META_Projects/META/ARCHIVE/experimental/all things CLAUDE/claude-code-telegram/`

## ✅ What You Have
A multi-API Telegram bot with:
- **Multiple AI providers**: Claude, OpenAI, Ollama (Local LLM)
- **Dynamic switching**: Auto switches based on cost, time, errors
- **Local LLM support**: Privacy-focused Ollama integration
- **Cost tracking**: Monitors usage per provider
- **Fallback system**: Automatic failover when primary APIs fail

## 🚀 Quick Start

### 1. Get Telegram Bot Token
- Message [@BotFather](https://t.me/BotFather) on Telegram
- `/newbot` → Create your bot
- Copy the API token

### 2. Configure Environment
```bash
cd /Users/LPS/META_Projects/META/ARCHIVE/experimental/all\ things\ CLAUDE/claude-code-telegram

# Copy and edit config
cp .env.multiapi .env
nano .env
```

### 3. Essential Settings
```bash
# Required
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_BOT_USERNAME=your_bot_username
APPROVED_DIRECTORY=/path/to/your/projects
ALLOWED_USERS=your_user_id

# Multi-API setup
PRIMARY_API_PROVIDER=claude
OLLAMA_MODEL=llama3:8b
OLLAMA_API_URL=http://localhost:11434

# Optional cost control
COST_SWITCH_THRESHOLD=5.0
LOCAL_HOURS_START=18  # 6 PM
LOCAL_HOURS_END=9      # 9 AM
ENABLE_WEEKEND_LOCAL=true
```

### 4. Install Dependencies
```bash
# Option A: Poetry (recommended)
poetry install

# Option B: pip
pip install httpx python-dotenv structlog --break-system-packages --user
```

### 5. Start Ollama (for local LLM)
```bash
# Check if running
ollama list

# Pull model (if needed)
ollama pull llama3:8b

# Start service
ollama serve
```

### 6. Test Setup
```bash
python simple_test.py
```

### 7. Start the Bot
```bash
# Development
python -m src.main

# With poetry
poetry run python -m src.main
```

## 🔑 Key Features

### Dynamic Provider Switching
- **Cost-based**: Switches to local LLM when $5.00 threshold reached
- **Time-based**: Uses Ollama after 6 PM until 9 AM next day
- **Weekends**: Always uses local LLM on Saturday/Sunday
- **Auto-fallback**: Switches to backup provider on errors

### Supported Providers
1. **Claude API** (Primary, high quality)
2. **OpenAI API** (Fallback option)
3. **Ollama/Local LLM** (Free, private)

### Configuration Examples

**Cost-Conscious Setup:**
```bash
PRIMARY_API_PROVIDER=claude
COST_SWITCH_THRESHOLD=5.0
FALLBACK_API_PROVIDER=ollama
OLLAMA_MODEL=llama3:8b
```

**Evenings & Weekends Only:**
```bash
PRIMARY_API_PROVIDER=claude
LOCAL_HOURS_START=18
LOCAL_HOURS_END=9
ENABLE_WEEKEND_LOCAL=true
```

**Pure Local Setup:**
```bash
PRIMARY_API_PROVIDER=ollama
OLLAMA_MODEL=llama3:8b
```

## 📊 Monitoring & Control

### Check Current Provider
The bot will show which provider it's using in responses.

### Cost Tracking
Usage is tracked automatically and can be extended to show costs in the interface.

### Manual Override
Edit `.env` and restart the bot to change providers or settings.

## 📁 Important Files
- `src/claude/multi_api_manager.py` - Core multi-API logic
- `src/config/multi_settings.py` - Configuration management
- `simple_test.py` - Test script
- `MULTI_API_SETUP.md` - Detailed setup guide
- `MULTI_API_SUMMARY.md` - Technical overview

## 🔧 Troubleshooting

### Common Issues
1. **Ollama Connection Failed**
   ```bash
   # Check Ollama is running
   ollama list

   # Test API
   curl http://localhost:11434/api/tags
   ```

2. **API Key Errors**
   - Verify tokens are correct
   - Check API permissions
   - Ensure URLs are accurate

3. **Import Errors**
   ```bash
   # Install missing dependencies
   poetry install
   # Or
   pip install httpx python-dotenv structlog --break-system-packages --user
   ```

### Debug Mode
```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

## 🎯 Next Steps
1. Get Telegram bot token from @BotFather
2. Configure `.env` with your API keys
3. Test with `simple_test.py`
4. Start the bot with `python -m src.main`
5. Add to Telegram and start chatting!

## 💡 Pro Tips
- The bot uses your local directory for security
- All conversations are private to your approved users
- Local LLM mode works without internet
- Cost tracking helps optimize API usage

---

**Note**: This implementation gives you a production-ready Telegram bot with multiple AI providers, automatic cost optimization, and local LLM support for privacy and cost savings.