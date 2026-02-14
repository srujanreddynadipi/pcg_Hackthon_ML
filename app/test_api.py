"""
API Test Suite - Tests all edge cases and scenarios
"""

import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000/predict"

# Test cases (13 edge cases from hackathon demo)
test_cases = [
    {
        "name": "VPN Issue - Normal Case",
        "data": {
            "user": "john.doe@company.com",
            "title": "VPN connection not working",
            "description": "Cannot connect to VPN from home. Getting authentication error when trying to connect.",
            "historical_tickets": [
                {
                    "ticket_id": "TICKET-001",
                    "title": "VPN not connecting",
                    "description": "VPN connection failed",
                    "status": "Resolved"
                }
            ]
        },
        "expected": {
            "category": "Network",
            "resolver": "Network Team"
        }
    },
    {
        "name": "Database Connection - Critical Priority",
        "data": {
            "user": "admin@company.com",
            "title": "Production database down - URGENT",
            "description": "Critical: Production MySQL database is not responding. All users affected. Need immediate assistance.",
            "historical_tickets": []
        },
        "expected": {
            "category": "Database",
            "resolver": "DBA Team",
            "priority": "Critical"
        }
    },
    {
        "name": "Hardware Issue - Laptop Problem",
        "data": {
            "user": "jane.smith@company.com",
            "title": "Laptop screen flickering",
            "description": "My laptop screen keeps flickering and sometimes goes black. Using external monitor as workaround.",
            "historical_tickets": []
        },
        "expected": {
            "category": "Hardware",
            "resolver": "Service Desk"
        }
    },
    {
        "name": "Security - Patch Request",
        "data": {
            "user": "security@company.com",
            "title": "Critical security patch needed",
            "description": "Security vulnerability detected in Windows servers. Need to apply patch immediately to prevent breach.",
            "historical_tickets": []
        },
        "expected": {
            "category": "Security",
            "resolver": "Security Ops",
            "priority": "Critical"
        }
    },
    {
        "name": "Access - Password Reset",
        "data": {
            "user": "newuser@company.com",
            "title": "Need password reset",
            "description": "Forgot my password and account is locked. Cannot access email or any systems.",
            "historical_tickets": []
        },
        "expected": {
            "category": "Access",
            "resolver": "Service Desk"
        }
    },
    {
        "name": "Empty Title - Edge Case",
        "data": {
            "user": "test@company.com",
            "title": "",
            "description": "VPN is not connecting to network",
            "historical_tickets": []
        },
        "expected": {
            "category": "Network"
        }
    },
    {
        "name": "Typo - Misspelled Keywords",
        "data": {
            "user": "typo@company.com",
            "title": "VPM nt conneting",
            "description": "Canot conect to VPM from hme. Autentication eror.",
            "historical_tickets": []
        },
        "expected": {
            "category": "Network"
        }
    },
    {
        "name": "Multiple Issues - Combined Ticket",
        "data": {
            "user": "multi@company.com",
            "title": "Email and VPN not working",
            "description": "Cannot access email (Outlook not connecting) and also VPN is showing connection timeout error.",
            "historical_tickets": []
        },
        "expected": {
            "category": ["Email", "Network"]  # Could be either
        }
    },
    {
        "name": "Service Request - New User Setup",
        "data": {
            "user": "hr@company.com",
            "title": "New employee onboarding - access setup",
            "description": "Please create accounts and provide access for new employee John Doe starting next week.",
            "historical_tickets": []
        },
        "expected": {
            "category": "Service Request",
            "resolver": "Service Desk"
        }
    },
    {
        "name": "Cloud - AWS Issue",
        "data": {
            "user": "devops@company.com",
            "title": "AWS S3 bucket access denied",
            "description": "Getting 403 Forbidden error when trying to access S3 bucket. Need permissions updated.",
            "historical_tickets": []
        },
        "expected": {
            "category": "Cloud",
            "resolver": "Cloud Ops"
        }
    },
    {
        "name": "DevOps - CI/CD Pipeline Failed",
        "data": {
            "user": "developer@company.com",
            "title": "Jenkins build failing",
            "description": "Jenkins pipeline is failing at deployment stage. Build was working yesterday but now errors out.",
            "historical_tickets": []
        },
        "expected": {
            "category": "DevOps",
            "resolver": "DevOps Team"
        }
    },
    {
        "name": "Monitoring - Alert Issue",
        "data": {
            "user": "ops@company.com",
            "title": "Grafana dashboard not showing metrics",
            "description": "Monitoring dashboard is not displaying any metrics. Alerts are not triggering.",
            "historical_tickets": []
        },
        "expected": {
            "category": "Monitoring",
            "resolver": "Cloud Ops"
        }
    },
    {
        "name": "Software - Application Bug",
        "data": {
            "user": "user@company.com",
            "title": "CRM application crashes on startup",
            "description": "Salesforce CRM crashes immediately when I try to open it. Getting error code 0x80070005.",
            "historical_tickets": []
        },
        "expected": {
            "category": "Software",
            "resolver": "App Support"
        }
    }
]

def test_api():
    """Run all test cases"""
    print("🧪 ITSM AI API Test Suite")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    errors = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test['name']}")
        print("-" * 60)
        
        try:
            # Make API request
            response = requests.post(API_URL, json=test['data'], timeout=30)
            
            if response.status_code != 200:
                print(f"❌ FAILED: HTTP {response.status_code}")
                print(f"   Error: {response.text}")
                failed += 1
                errors.append({
                    "test": test['name'],
                    "error": f"HTTP {response.status_code}: {response.text}"
                })
                print()
                continue
            
            result = response.json()
            
            # Extract predictions
            predicted_category = result['predictions']['category']['predicted']
            predicted_resolver = result['predictions']['resolver_group']['assigned_to']
            predicted_priority = result['predictions']['priority']['predicted']
            confidence = result['predictions']['category']['confidence']
            processing_time = result['processing_time_ms']
            
            # Validate predictions
            success = True
            
            # Check category
            expected_cat = test['expected']['category']
            if isinstance(expected_cat, list):
                if predicted_category not in expected_cat:
                    success = False
                    print(f"❌ Category: Expected one of {expected_cat}, got {predicted_category}")
            else:
                if predicted_category != expected_cat:
                    success = False
                    print(f"❌ Category: Expected {expected_cat}, got {predicted_category}")
            
            # Check resolver (if specified)
            if 'resolver' in test['expected']:
                if predicted_resolver != test['expected']['resolver']:
                    success = False
                    print(f"❌ Resolver: Expected {test['expected']['resolver']}, got {predicted_resolver}")
            
            # Check priority (if specified)
            if 'priority' in test['expected']:
                if predicted_priority != test['expected']['priority']:
                    success = False
                    print(f"❌ Priority: Expected {test['expected']['priority']}, got {predicted_priority}")
            
            if success:
                print(f"✅ PASSED")
                print(f"   Category: {predicted_category} ({confidence:.2%} confidence)")
                print(f"   Priority: {predicted_priority}")
                print(f"   Resolver: {predicted_resolver}")
                print(f"   Processing: {processing_time:.1f}ms")
                passed += 1
            else:
                failed += 1
                errors.append({
                    "test": test['name'],
                    "error": "Prediction mismatch (see details above)"
                })
            
            # Show RAG insights if available
            if result['rag_insights']['proactive_insights']['count'] > 0:
                insights = result['rag_insights']['proactive_insights']['insights']
                print(f"   💡 Insights: {len(insights)} proactive recommendations")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED: Connection error")
            print(f"   Error: {e}")
            failed += 1
            errors.append({
                "test": test['name'],
                "error": f"Connection error: {str(e)}"
            })
        except Exception as e:
            print(f"❌ FAILED: Unexpected error")
            print(f"   Error: {e}")
            failed += 1
            errors.append({
                "test": test['name'],
                "error": f"Unexpected error: {str(e)}"
            })
        
        print()
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(test_cases)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {passed/len(test_cases)*100:.1f}%")
    
    if errors:
        print("\n❌ Failed Tests:")
        for error in errors:
            print(f"  - {error['test']}: {error['error']}")
    else:
        print("\n🎉 All tests passed!")
    
    print()
    print(f"Timestamp: {datetime.now().isoformat()}")

if __name__ == "__main__":
    print("⏳ Starting API tests...")
    print("Make sure the API is running on http://localhost:8000")
    print()
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy and ready")
            print()
            test_api()
        else:
            print("❌ API returned non-200 status")
            print("Please start the API first: python app/main.py")
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API")
        print("Please start the API first: python app/main.py")
