#!/usr/bin/env python3
"""
Test script for FastAPI + CrewAI Knowledge PoC

This script demonstrates how to interact with the API and test various queries.
Run this after starting the FastAPI server.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

async def test_api_health():
    """Test the health check endpoint"""
    print("🔍 Testing API health...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API is healthy!")
                print(f"   Knowledge files: {data['knowledge_files_count']}")
                print(f"   Crew initialized: {data['crew_initialized']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

async def test_list_files():
    """Test the file listing endpoint"""
    print("\n📁 Testing file listing...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/files")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['count']} knowledge files:")
                for file in data['available_files']:
                    print(f"   📄 {file}")
                return data['available_files']
            else:
                print(f"❌ File listing failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ File listing error: {e}")
            return []

async def test_query(query: str, expected_keywords: list = None):
    """Test a knowledge query"""
    print(f"\n❓ Testing query: '{query}'")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/query",
                json={"query": query}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Query successful!")
                print(f"📝 Response: {data['response'][:200]}{'...' if len(data['response']) > 200 else ''}")
                print(f"📚 Sources: {data['sources']}")
                
                # Check if expected keywords are in response
                if expected_keywords:
                    found_keywords = []
                    response_lower = data['response'].lower()
                    for keyword in expected_keywords:
                        if keyword.lower() in response_lower:
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        print(f"🎯 Found expected keywords: {found_keywords}")
                    else:
                        print(f"⚠️  Expected keywords not found: {expected_keywords}")
                
                return data
            else:
                print(f"❌ Query failed: {response.status_code}")
                if response.status_code == 422:
                    print(f"   Validation error: {response.json()}")
                return None
        except Exception as e:
            print(f"❌ Query error: {e}")
            return None

async def run_comprehensive_tests():
    """Run a comprehensive test suite"""
    print("🚀 Starting FastAPI + CrewAI Knowledge PoC Tests")
    print("=" * 60)
    
    # Test 1: Health check
    health_ok = await test_api_health()
    if not health_ok:
        print("❌ Cannot proceed - API is not healthy")
        return
    
    # Test 2: List files
    files = await test_list_files()
    if not files:
        print("⚠️  No knowledge files found. Make sure to add .md files to ./knowledge/ directory")
        return
    
    # Test 3: Sample queries based on expected knowledge
    test_cases = [
        {
            "query": "What are the key features of FastAPI?",
            "keywords": ["fast", "performance", "type hints", "documentation"]
        },
        {
            "query": "How do I create a CrewAI agent?",
            "keywords": ["Agent", "role", "goal", "backstory"]
        },
        {
            "query": "What are the best practices for Docker deployment?",
            "keywords": ["multi-stage", "alpine", "security", "layer"]
        },
        {
            "query": "How should I handle environment variables in production?",
            "keywords": ["environment variables", "secrets", "API keys"]
        },
        {
            "query": "What monitoring metrics should I track for AI applications?",
            "keywords": ["response times", "error rates", "token usage"]
        }
    ]
    
    successful_queries = 0
    total_queries = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*20} Test Query {i}/{total_queries} {'='*20}")
        result = await test_query(test_case["query"], test_case["keywords"])
        if result:
            successful_queries += 1
        
        # Small delay between queries
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🎯 Test Summary:")
    print(f"   Successful queries: {successful_queries}/{total_queries}")
    print(f"   Success rate: {(successful_queries/total_queries)*100:.1f}%")
    
    if successful_queries == total_queries:
        print("🎉 All tests passed! Your CrewAI Knowledge PoC is working correctly.")
    elif successful_queries > 0:
        print("⚠️  Some tests passed. Check the failed queries and knowledge files.")
    else:
        print("❌ All tests failed. Check your setup and knowledge files.")

async def interactive_mode():
    """Interactive mode for testing custom queries"""
    print("\n🤖 Interactive Query Mode")
    print("Type your questions and get answers from the knowledge base.")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            query = input("❓ Your question: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                print("Please enter a question.")
                continue
            
            result = await test_query(query)
            if result:
                print(f"\n🤖 Answer: {result['response']}")
                print(f"📚 Sources: {', '.join(result['sources'])}")
            
            print("\n" + "-" * 50)
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function to run tests"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(run_comprehensive_tests())

if __name__ == "__main__":
    main()