#!/usr/bin/env python3
"""
Focused CSV Data Matching System Test
Tests the improved normalize_username() function and matching capabilities
"""

import requests
import json
import io
import pandas as pd
from datetime import datetime
import sys

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url() + "/api"
ADMIN_AUTH = ("admin", "admin123")

def create_test_csv_content(usernames):
    """Create CSV content for testing"""
    df = pd.DataFrame({'username': usernames})
    return df.to_csv(index=False).encode('utf-8')

def test_csv_matching_comprehensive():
    """Comprehensive test of CSV data matching with problematic usernames"""
    print("🔍 COMPREHENSIVE CSV DATA MATCHING TEST")
    print("=" * 60)
    
    session = requests.Session()
    
    # Clear existing data
    print("\n1. Clearing existing test data...")
    try:
        # Delete all posts (cascade deletes engagements)
        response = session.get(f"{BASE_URL}/posts", auth=ADMIN_AUTH)
        if response.status_code == 200:
            posts = response.json()
            for post in posts:
                session.delete(f"{BASE_URL}/posts/{post['id']}", auth=ADMIN_AUTH)
        
        # Delete all users
        response = session.get(f"{BASE_URL}/users", auth=ADMIN_AUTH)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                session.delete(f"{BASE_URL}/users/{user['id']}", auth=ADMIN_AUTH)
        print("✅ Test data cleared")
    except Exception as e:
        print(f"⚠️  Warning: Could not clear all test data: {e}")
    
    # Test Case: Reproduce the user's issue with problematic usernames
    print("\n2. Testing problematic username variations that should match...")
    
    # Management users with various problematic formats
    management_users_raw = [
        "cmile.ozdmrr",      # Base format (from user's example)
        "@ayse.yilmaz",      # With @ symbol and dot
        "Mehmet_Kaya",       # Mixed case with underscore
        "fatma demir",       # With space
        "Ali-Ozkan",         # With hyphen
        "zeynep_123",        # With underscore and numbers
        "BURAK.TWITTER",     # All caps with dot
        "selin medya",       # Lowercase with space
    ]
    
    print(f"   Uploading {len(management_users_raw)} management users:")
    for i, user in enumerate(management_users_raw, 1):
        print(f"   {i}. '{user}'")
    
    # Upload management users
    csv_content = create_test_csv_content(management_users_raw)
    files = {'file': ('management_users.csv', csv_content, 'text/csv')}
    data = {'platform': 'instagram'}
    
    response = session.post(f"{BASE_URL}/users/upload", files=files, data=data, auth=ADMIN_AUTH)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Uploaded {result.get('count')} management users")
        print(f"   Normalized sample: {result.get('sample_users', [])}")
    else:
        print(f"❌ Failed to upload management users: {response.status_code}")
        return False
    
    # Create test post
    print("\n3. Creating test post...")
    test_post = {
        'title': 'Test Post - CSV Matching Issue Reproduction',
        'platform': 'instagram',
        'post_id': 'csv_test_reproduction',
        'post_date': datetime.utcnow().isoformat()
    }
    
    response = session.post(f"{BASE_URL}/posts", json=test_post, auth=ADMIN_AUTH)
    if response.status_code == 200:
        post_data = response.json()
        test_post_id = post_data.get('id')
        print(f"✅ Created test post: {test_post['title']}")
    else:
        print(f"❌ Failed to create test post: {response.status_code}")
        return False
    
    # Engagement users with different formatting (should match management users)
    print("\n4. Testing engagement data with different formatting...")
    
    engagement_users_raw = [
        "@cmile.ozdmrr",     # Same as management but with @
        "AYSE.YILMAZ",       # Same as management but uppercase
        "mehmet_kaya",       # Same as management but lowercase
        "Fatma Demir",       # Same as management but different case
        "ali-ozkan",         # Same as management but lowercase
        "Zeynep_123",        # Same as management but different case
        "burak.twitter",     # Same as management but lowercase
        "SELIN MEDYA",       # Same as management but uppercase
    ]
    
    print(f"   Uploading {len(engagement_users_raw)} engagement records:")
    for i, user in enumerate(engagement_users_raw, 1):
        print(f"   {i}. '{user}'")
    
    csv_content = create_test_csv_content(engagement_users_raw)
    files = {'file': ('engagement_data.csv', csv_content, 'text/csv')}
    data = {'post_id': test_post_id}
    
    response = session.post(f"{BASE_URL}/engagements/upload", files=files, data=data, auth=ADMIN_AUTH)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Uploaded {result.get('count')} engagement records")
        print(f"   Normalized sample: {result.get('sample_users', [])}")
    else:
        print(f"❌ Failed to upload engagement data: {response.status_code}")
        return False
    
    # Analyze engagement to check matching
    print("\n5. Analyzing engagement matching...")
    
    response = session.get(f"{BASE_URL}/engagements/analysis/{test_post_id}", auth=ADMIN_AUTH)
    if response.status_code == 200:
        analysis = response.json()
        
        total_management = analysis.get('total_management', 0)
        total_engaged = analysis.get('total_engaged', 0)
        engagement_percentage = analysis.get('engagement_percentage', 0)
        engaged_users = analysis.get('engaged_users', [])
        not_engaged_users = analysis.get('not_engaged_users', [])
        
        print(f"   📊 ANALYSIS RESULTS:")
        print(f"   Total Management Users: {total_management}")
        print(f"   Total Engaged Users: {total_engaged}")
        print(f"   Engagement Rate: {engagement_percentage}%")
        print(f"   ✅ Engaged Users: {engaged_users}")
        print(f"   ❌ Not Engaged Users: {not_engaged_users}")
        
        # Check if the issue is resolved
        if total_management == 8 and total_engaged == 8 and engagement_percentage == 100.0:
            print(f"\n🎉 SUCCESS: All username variations matched correctly!")
            print(f"   The CSV data matching issue has been RESOLVED.")
            success = True
        elif total_engaged > 0:
            print(f"\n⚠️  PARTIAL SUCCESS: {engagement_percentage}% of users matched")
            print(f"   Some username variations are still not matching correctly.")
            success = False
        else:
            print(f"\n❌ FAILURE: No users matched - the issue persists")
            success = False
            
    else:
        print(f"❌ Failed to get analysis: {response.status_code}")
        return False
    
    # Debug normalization endpoint
    print("\n6. Using debug endpoint for detailed analysis...")
    
    response = session.get(f"{BASE_URL}/debug/normalization/{test_post_id}", auth=ADMIN_AUTH)
    if response.status_code == 200:
        debug_info = response.json()
        
        mgmt_users = debug_info.get('management_users', {})
        eng_users = debug_info.get('engagement_users', {})
        analysis_debug = debug_info.get('analysis', {})
        
        print(f"   🔍 DEBUG INFORMATION:")
        print(f"   Management Users: {mgmt_users.get('all', [])}")
        print(f"   Engagement Users: {eng_users.get('all', [])}")
        
        matches = analysis_debug.get('matches', {}).get('users', [])
        mismatches = analysis_debug.get('mismatches', {}).get('users', [])
        extra_engagements = analysis_debug.get('extra_engagements', {}).get('users', [])
        
        if matches:
            print(f"   ✅ MATCHED: {matches}")
        if mismatches:
            print(f"   ❌ UNMATCHED: {mismatches}")
        if extra_engagements:
            print(f"   ⚠️  EXTRA ENGAGEMENTS: {extra_engagements}")
            
    else:
        print(f"❌ Debug endpoint failed: {response.status_code}")
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 CSV DATA MATCHING SYSTEM: WORKING CORRECTLY")
        print("   All problematic username variations are now matching properly!")
    else:
        print("❌ CSV DATA MATCHING SYSTEM: NEEDS IMPROVEMENT")
        print("   Some username variations are still not matching correctly.")
    
    return success

if __name__ == "__main__":
    success = test_csv_matching_comprehensive()
    sys.exit(0 if success else 1)