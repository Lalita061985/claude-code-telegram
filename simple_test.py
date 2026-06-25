#!/usr/bin/env python3
"""Simple test for multi-API functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Test Ollama directly
async def test_ollama():
    """Test Ollama API directly."""
    print("🚀 Testing Ollama API")
    print("=" * 30)

    try:
        import httpx
    except ImportError:
        print("❌ httpx not installed. Installing...")
        os.system("pip install httpx --break-system-packages --user")
        import httpx

    # Test Ollama connection
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Check Ollama status
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json()
                print("✅ Ollama is running")
                print(f"   Available models: {[m['name'] for m in models.get('models', [])]}")
            else:
                print(f"❌ Ollama status error: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            return

        # Test chat completion
        try:
            print("\n🧪 Testing chat completion...")
            chat_response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llama3:8b",
                    "messages": [
                        {"role": "user", "content": "Hello! Can you tell me a very short joke?"}
                    ],
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 100,
                    },
                    "stream": False,  # Disable streaming for simpler response
                },
            )

            if chat_response.status_code == 200:
                data = chat_response.json()
                print("✅ Chat completion successful!")
                print(f"   Response: {data['message']['content'][:100]}...")
                print(f"   Model: {data.get('model', 'unknown')}")
                print(f"   Done: {data.get('done', 'unknown')}")
            else:
                print(f"❌ Chat completion failed: {chat_response.status_code}")
                print(f"   Error: {chat_response.text}")

        except Exception as e:
            print(f"❌ Chat completion error: {e}")

    print("\n🎉 Ollama test completed!")


async def test_multi_api_config():
    """Test configuration loading."""
    print("\n🔧 Testing Configuration")
    print("=" * 30)

    # Test loading .env file
    try:
        from dotenv import load_dotenv
        load_dotenv('.env.test')

        print("✅ .env.test loaded")
        print(f"   TELEGRAM_BOT_TOKEN: {os.getenv('TELEGRAM_BOT_TOKEN', 'Not set')}")
        print(f"   PRIMARY_API_PROVIDER: {os.getenv('PRIMARY_API_PROVIDER', 'Not set')}")
        print(f"   OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL', 'Not set')}")
        print(f"   ENABLE_DYNAMIC_SWITCHING: {os.getenv('ENABLE_DYNAMIC_SWITCHING', 'Not set')}")

    except ImportError:
        print("❌ python-dotenv not installed")
        return
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return

    print("\n🎉 Configuration test completed!")


async def main():
    """Run all tests."""
    print("🎯 Starting Multi-API System Tests")
    print("=" * 50)

    # Test configuration
    await test_multi_api_config()

    # Test Ollama
    await test_ollama()

    print("\n🚀 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())