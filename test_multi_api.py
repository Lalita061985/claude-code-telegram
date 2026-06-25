#!/usr/bin/env python3
"""Test script for multi-API functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.multi_settings import Settings, create_settings
from src.claude.multi_api_manager import MultiAPIManager


async def test_multi_api():
    """Test multi-API functionality."""
    print("🚀 Testing Multi-API System")
    print("=" * 50)

    # Load settings
    try:
        settings = create_settings()
        print("✅ Settings loaded successfully")
        print(f"   Primary API: {settings.multi_api.primary_api_provider}")
        print(f"   Dynamic switching: {settings.multi_api.enable_dynamic_switching}")
        print(f"   Cost threshold: ${settings.multi_api.cost_switch_threshold}")
        print()
    except Exception as e:
        print(f"❌ Settings failed: {e}")
        print("   Make sure you have .env file with basic settings")
        return

    # Initialize multi-API manager
    try:
        multi_api_manager = MultiAPIManager(settings)
        print("✅ Multi-API manager initialized")
        print(f"   Available providers: {list(multi_api_manager.providers.keys())}")
        print()
    except Exception as e:
        print(f"❌ Multi-API manager failed: {e}")
        return

    # Test API responses
    test_messages = [
        {"role": "user", "content": "Hello! Can you tell me a short joke?"}
    ]

    # Test each provider
    for provider_name, provider in multi_api_manager.providers.items():
        print(f"🧪 Testing {provider_name.value.upper()} provider...")
        try:
            result = await provider.chat_completion(test_messages)
            print(f"   ✅ Response received: {len(result['content'])} characters")
            print(f"   📊 Tokens used: {result['tokens_used']}")
            print(f"   🤖 Model: {result['model']}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        print()

    # Test dynamic provider selection
    print("🔄 Testing dynamic provider selection...")
    user_id = 12345
    provider_info = multi_api_manager.get_provider_info(user_id)
    print(f"   Current provider: {provider_info['current_provider']}")
    print(f"   Available providers: {provider_info['available_providers']}")
    print(f"   User cost: ${provider_info['user_cost']:.4f}")
    print()

    # Test dynamic switching simulation
    print("⏰ Testing cost-based switching...")
    # Simulate high cost
    multi_api_manager.cost_tracker.add_usage(user_id, multi_api_manager.primary_provider, 100000, 0.00001)

    new_provider_info = multi_api_manager.get_provider_info(user_id)
    print(f"   After high cost (${new_provider_info['user_cost']:.4f}): {new_provider_info['current_provider']}")
    print()

    print("🎉 Multi-API system test completed!")


if __name__ == "__main__":
    asyncio.run(test_multi_api())