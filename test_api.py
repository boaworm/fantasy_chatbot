"""
Test script for Fantasy Chatbot API.
Run this to verify your setup is working correctly.
"""

import requests
import sys
from pathlib import Path

API_BASE = "http://localhost:8000/api"


def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        data = response.json()

        if response.status_code == 200:
            print(f"✓ Health check passed: {data['status']}")
            print(f"  - LLM Healthy: {data['llm_healthy']}")
            print(f"  - Topics Count: {data['topics_count']}")
            return True
        else:
            print(f"✗ Health check failed: {data}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {str(e)}")
        return False


def test_topics():
    """Test the topics endpoint."""
    print("\nTesting topics endpoint...")
    try:
        response = requests.get(f"{API_BASE}/topics")
        data = response.json()

        if response.status_code == 200:
            print(f"✓ Topics retrieved successfully")
            print(f"  - Topics: {', '.join(data['topics'])}")
            return True
        else:
            print(f"✗ Failed to retrieve topics: {data}")
            return False
    except Exception as e:
        print(f"✗ Failed to retrieve topics: {str(e)}")
        return False


def test_chat():
    """Test the chat endpoint."""
    print("\nTesting chat endpoint...")
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={"message": "Tell me about the One Ring"},
            timeout=10
        )
        data = response.json()

        if response.status_code == 200:
            print(f"✓ Chat response received")
            print(f"  - On Topic: {data['is_on_topic']}")
            print(f"  - Reason: {data['reason']}")
            print(f"  - Response: {data['response'][:100]}...")
            return True
        else:
            print(f"✗ Chat request failed: {data}")
            return False
    except Exception as e:
        print(f"✗ Chat request failed: {str(e)}")
        return False


def test_off_topic():
    """Test off-topic rejection."""
    print("\nTesting off-topic rejection...")
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={"message": "What's for dinner?"},
            timeout=10
        )
        data = response.json()

        if response.status_code == 200:
            if not data['is_on_topic']:
                print(f"✓ Off-topic correctly rejected")
                print(f"  - Reason: {data['reason']}")
                print(f"  - Response: {data['response']}")
                return True
            else:
                print(f"✗ Off-topic was not rejected")
                return False
        else:
            print(f"✗ Request failed: {data}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Fantasy Chatbot API Test Suite")
    print("=" * 60)

    results = []

    # Run tests
    results.append(test_health())
    results.append(test_topics())
    results.append(test_chat())
    results.append(test_off_topic())

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! Your setup is working correctly.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()