#!/usr/bin/env python3
"""
Debug script for AI API issues.
Helps troubleshoot OpenAI/DeepSeek API connectivity and response issues.
"""

import os
import sys
import json
import requests
import time
from typing import Optional


def test_openai_api(api_key: str) -> bool:
    """Test OpenAI API connectivity"""
    print("🔄 Testing OpenAI API...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Say 'Hello, API test successful!'"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        duration = time.time() - start_time
        
        print(f"⏱️ Response time: {duration:.2f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ OpenAI API working! Response: {content}")
            return True
        else:
            print(f"❌ OpenAI API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ OpenAI API timeout (30s)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 OpenAI API network error: {e}")
        return False
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False


def test_deepseek_api(api_key: str) -> bool:
    """Test DeepSeek API connectivity"""
    print("🔄 Testing DeepSeek API...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "Say 'Hello, API test successful!'"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        duration = time.time() - start_time
        
        print(f"⏱️ Response time: {duration:.2f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ DeepSeek API working! Response: {content}")
            return True
        else:
            print(f"❌ DeepSeek API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ DeepSeek API timeout (30s)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 DeepSeek API network error: {e}")
        return False
    except Exception as e:
        print(f"❌ DeepSeek API error: {e}")
        return False


def test_network_connectivity() -> bool:
    """Test basic network connectivity"""
    print("🔄 Testing network connectivity...")
    
    test_urls = [
        "https://api.openai.com",
        "https://api.deepseek.com",
        "https://httpbin.org/get"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {e}")
            return False
    
    return True


def main():
    """Main debug function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug AI API connectivity')
    parser.add_argument('--openai-key', help='OpenAI API key')
    parser.add_argument('--deepseek-key', help='DeepSeek API key')
    parser.add_argument('--test-network', action='store_true', help='Test network connectivity')
    
    args = parser.parse_args()
    
    print("🔍 AI API Debug Tool")
    print("=" * 50)
    
    # Test network connectivity
    if args.test_network:
        if test_network_connectivity():
            print("✅ Network connectivity OK")
        else:
            print("❌ Network connectivity issues")
            return
    
    # Test OpenAI API
    if args.openai_key:
        if test_openai_api(args.openai_key):
            print("✅ OpenAI API is working")
        else:
            print("❌ OpenAI API has issues")
    else:
        print("⏭️ Skipping OpenAI API test (no key provided)")
    
    # Test DeepSeek API
    if args.deepseek_key:
        if test_deepseek_api(args.deepseek_key):
            print("✅ DeepSeek API is working")
        else:
            print("❌ DeepSeek API has issues")
    else:
        print("⏭️ Skipping DeepSeek API test (no key provided)")
    
    print("\n💡 Recommendations:")
    print("- If APIs are failing, check your API keys")
    print("- If timeouts occur, check your network connection")
    print("- Use SKIP_AI=true to bypass AI calls in the pipeline")
    print("- Check API quotas and billing status")


if __name__ == "__main__":
    main()
