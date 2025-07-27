#!/usr/bin/env python3
"""
Backend API Testing for Social Media Engagement Tracking System
Tests all backend endpoints with proper authentication and realistic data
"""

import requests
import json
import io
import pandas as pd
from datetime import datetime, timedelta
import base64
import sys
import os

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
print(f"Testing backend at: {BASE_URL}")

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth = (ADMIN_USERNAME, ADMIN_PASSWORD)
        self.test_results = []
        self.created_user_ids = []
        self.created_post_ids = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        })
        
    def create_test_csv_content(self, usernames):
        """Create CSV content for testing"""
        df = pd.DataFrame({'username': usernames})
        return df.to_csv(index=False).encode('utf-8')
        
    def create_test_excel_content(self, usernames):
        """Create Excel content for testing"""
        df = pd.DataFrame({'username': usernames})
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer.getvalue()

    def test_authentication(self):
        """Test 1: Authentication endpoint"""
        print("\n=== Testing Authentication ===")
        
        try:
            # Test valid credentials
            response = self.session.post(f"{BASE_URL}/login", auth=self.auth)
            if response.status_code == 200:
                data = response.json()
                if data.get('username') == ADMIN_USERNAME:
                    self.log_test("Authentication - Valid Credentials", True, "Login successful with admin credentials")
                else:
                    self.log_test("Authentication - Valid Credentials", False, "Login response missing username")
            else:
                self.log_test("Authentication - Valid Credentials", False, f"Login failed with status {response.status_code}")
                
            # Test invalid credentials
            response = self.session.post(f"{BASE_URL}/login", auth=("wrong", "wrong"))
            if response.status_code == 401:
                self.log_test("Authentication - Invalid Credentials", True, "Correctly rejected invalid credentials")
            else:
                self.log_test("Authentication - Invalid Credentials", False, f"Should reject invalid credentials, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Authentication", False, f"Exception during authentication test: {str(e)}")

    def test_user_management(self):
        """Test 2: User Management APIs"""
        print("\n=== Testing User Management ===")
        
        try:
            # Test CSV upload for Instagram users
            instagram_users = ['mehmet_ak', 'ayse_yilmaz', 'fatma_demir', 'ali_kaya', 'zeynep_ozkan']
            csv_content = self.create_test_csv_content(instagram_users)
            
            files = {'file': ('instagram_users.csv', csv_content, 'text/csv')}
            data = {'platform': 'instagram'}
            
            response = self.session.post(f"{BASE_URL}/users/upload", files=files, data=data, auth=self.auth)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('count') == len(instagram_users):
                    self.log_test("User Upload - Instagram CSV", True, f"Successfully uploaded {len(instagram_users)} Instagram users")
                else:
                    self.log_test("User Upload - Instagram CSV", False, f"Upload response invalid: {result}")
            else:
                self.log_test("User Upload - Instagram CSV", False, f"Upload failed with status {response.status_code}: {response.text}")
                
            # Test Excel upload for X users
            x_users = ['ahmet_twitter', 'elif_x', 'murat_sosyal', 'selin_medya', 'burak_dijital']
            excel_content = self.create_test_excel_content(x_users)
            
            files = {'file': ('x_users.xlsx', excel_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {'platform': 'x'}
            
            response = self.session.post(f"{BASE_URL}/users/upload", files=files, data=data, auth=self.auth)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('count') == len(x_users):
                    self.log_test("User Upload - X Excel", True, f"Successfully uploaded {len(x_users)} X users")
                else:
                    self.log_test("User Upload - X Excel", False, f"Upload response invalid: {result}")
            else:
                self.log_test("User Upload - X Excel", False, f"Upload failed with status {response.status_code}: {response.text}")
                
            # Test manual user addition
            manual_user = {'username': 'manuel_kullanici', 'platform': 'instagram'}
            response = self.session.post(f"{BASE_URL}/users/add", json=manual_user, auth=self.auth)
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get('username') == 'manuel_kullanici':
                    self.created_user_ids.append(user_data.get('id'))
                    self.log_test("User Add - Manual", True, "Successfully added manual user")
                else:
                    self.log_test("User Add - Manual", False, f"Manual user response invalid: {user_data}")
            else:
                self.log_test("User Add - Manual", False, f"Manual user add failed with status {response.status_code}")
                
            # Test get users (all)
            response = self.session.get(f"{BASE_URL}/users", auth=self.auth)
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list) and len(users) > 0:
                    self.log_test("User Get - All", True, f"Retrieved {len(users)} users")
                else:
                    self.log_test("User Get - All", False, "No users returned or invalid format")
            else:
                self.log_test("User Get - All", False, f"Get users failed with status {response.status_code}")
                
            # Test get users with platform filter
            response = self.session.get(f"{BASE_URL}/users?platform=instagram", auth=self.auth)
            if response.status_code == 200:
                instagram_users_result = response.json()
                if isinstance(instagram_users_result, list):
                    self.log_test("User Get - Platform Filter", True, f"Retrieved {len(instagram_users_result)} Instagram users")
                else:
                    self.log_test("User Get - Platform Filter", False, "Invalid format for filtered users")
            else:
                self.log_test("User Get - Platform Filter", False, f"Get filtered users failed with status {response.status_code}")
                
            # Test delete user (if we have a user ID)
            if self.created_user_ids:
                user_id = self.created_user_ids[0]
                response = self.session.delete(f"{BASE_URL}/users/{user_id}", auth=self.auth)
                if response.status_code == 200:
                    self.log_test("User Delete", True, "Successfully deleted user")
                else:
                    self.log_test("User Delete", False, f"Delete user failed with status {response.status_code}")
            else:
                self.log_test("User Delete", False, "No user ID available for deletion test")
                
        except Exception as e:
            self.log_test("User Management", False, f"Exception during user management test: {str(e)}")

    def test_post_management(self):
        """Test 3: Post Management APIs"""
        print("\n=== Testing Post Management ===")
        
        try:
            # Test create Instagram post
            instagram_post = {
                'title': 'Yeni Instagram Gönderisi - Parti Etkinliği',
                'platform': 'instagram',
                'post_id': 'ig_post_12345',
                'post_date': datetime.utcnow().isoformat()
            }
            
            response = self.session.post(f"{BASE_URL}/posts", json=instagram_post, auth=self.auth)
            if response.status_code == 200:
                post_data = response.json()
                if post_data.get('title') == instagram_post['title']:
                    self.created_post_ids.append(post_data.get('id'))
                    self.log_test("Post Create - Instagram", True, "Successfully created Instagram post")
                else:
                    self.log_test("Post Create - Instagram", False, f"Post response invalid: {post_data}")
            else:
                self.log_test("Post Create - Instagram", False, f"Create Instagram post failed with status {response.status_code}")
                
            # Test create X post
            x_post = {
                'title': 'X Platformu Gönderisi - Siyasi Açıklama',
                'platform': 'x',
                'post_id': 'x_post_67890',
                'post_date': (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
            
            response = self.session.post(f"{BASE_URL}/posts", json=x_post, auth=self.auth)
            if response.status_code == 200:
                post_data = response.json()
                if post_data.get('title') == x_post['title']:
                    self.created_post_ids.append(post_data.get('id'))
                    self.log_test("Post Create - X", True, "Successfully created X post")
                else:
                    self.log_test("Post Create - X", False, f"Post response invalid: {post_data}")
            else:
                self.log_test("Post Create - X", False, f"Create X post failed with status {response.status_code}")
                
            # Test get posts
            response = self.session.get(f"{BASE_URL}/posts", auth=self.auth)
            if response.status_code == 200:
                posts = response.json()
                if isinstance(posts, list) and len(posts) > 0:
                    self.log_test("Post Get", True, f"Retrieved {len(posts)} posts")
                else:
                    self.log_test("Post Get", False, "No posts returned or invalid format")
            else:
                self.log_test("Post Get", False, f"Get posts failed with status {response.status_code}")
                
        except Exception as e:
            self.log_test("Post Management", False, f"Exception during post management test: {str(e)}")

    def test_engagement_analysis(self):
        """Test 4: Engagement Analysis APIs"""
        print("\n=== Testing Engagement Analysis ===")
        
        try:
            if not self.created_post_ids:
                self.log_test("Engagement Analysis", False, "No posts available for engagement testing")
                return
                
            post_id = self.created_post_ids[0]
            
            # Test upload engagement data
            engaged_users = ['mehmet_ak', 'ayse_yilmaz', 'fatma_demir']  # Users who liked the post
            csv_content = self.create_test_csv_content(engaged_users)
            
            files = {'file': ('engagement_data.csv', csv_content, 'text/csv')}
            data = {'post_id': post_id}
            
            response = self.session.post(f"{BASE_URL}/engagements/upload", files=files, data=data, auth=self.auth)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('count') == len(engaged_users):
                    self.log_test("Engagement Upload", True, f"Successfully uploaded {len(engaged_users)} engagements")
                else:
                    self.log_test("Engagement Upload", False, f"Engagement upload response invalid: {result}")
            else:
                self.log_test("Engagement Upload", False, f"Engagement upload failed with status {response.status_code}: {response.text}")
                
            # Test engagement analysis
            response = self.session.get(f"{BASE_URL}/engagements/analysis/{post_id}", auth=self.auth)
            if response.status_code == 200:
                analysis = response.json()
                required_fields = ['post_id', 'post_title', 'platform', 'total_management', 'total_engaged', 'engagement_percentage', 'engaged_users', 'not_engaged_users']
                if all(field in analysis for field in required_fields):
                    self.log_test("Engagement Analysis", True, f"Analysis complete: {analysis['engagement_percentage']}% engagement rate")
                else:
                    self.log_test("Engagement Analysis", False, f"Analysis response missing fields: {analysis}")
            else:
                self.log_test("Engagement Analysis", False, f"Engagement analysis failed with status {response.status_code}")
                
        except Exception as e:
            self.log_test("Engagement Analysis", False, f"Exception during engagement analysis test: {str(e)}")

    def test_weekly_reports(self):
        """Test 5: Weekly Reports API"""
        print("\n=== Testing Weekly Reports ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/reports/weekly", auth=self.auth)
            if response.status_code == 200:
                report = response.json()
                required_fields = ['period', 'users', 'summary']
                if all(field in report for field in required_fields):
                    users_count = len(report.get('users', []))
                    self.log_test("Weekly Reports", True, f"Generated weekly report for {users_count} users")
                else:
                    self.log_test("Weekly Reports", False, f"Weekly report response missing fields: {report}")
            else:
                self.log_test("Weekly Reports", False, f"Weekly reports failed with status {response.status_code}")
                
        except Exception as e:
            self.log_test("Weekly Reports", False, f"Exception during weekly reports test: {str(e)}")

    def test_pdf_export(self):
        """Test 6: PDF Export API"""
        print("\n=== Testing PDF Export ===")
        
        try:
            if not self.created_post_ids:
                self.log_test("PDF Export", False, "No posts available for PDF export testing")
                return
                
            post_id = self.created_post_ids[0]
            
            response = self.session.get(f"{BASE_URL}/export/pdf/{post_id}", auth=self.auth)
            if response.status_code == 200:
                result = response.json()
                if 'pdf_data' in result and result['pdf_data']:
                    # Try to decode the hex data to verify it's valid
                    try:
                        pdf_bytes = bytes.fromhex(result['pdf_data'])
                        if pdf_bytes.startswith(b'%PDF'):
                            self.log_test("PDF Export", True, f"Successfully generated PDF ({len(pdf_bytes)} bytes)")
                        else:
                            self.log_test("PDF Export", False, "PDF data doesn't start with PDF header")
                    except ValueError:
                        self.log_test("PDF Export", False, "PDF data is not valid hex")
                else:
                    self.log_test("PDF Export", False, f"PDF export response missing pdf_data: {result}")
            else:
                self.log_test("PDF Export", False, f"PDF export failed with status {response.status_code}")
                
        except Exception as e:
            self.log_test("PDF Export", False, f"Exception during PDF export test: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for Social Media Engagement Tracking System")
        print("=" * 80)
        
        # Run tests in priority order
        self.test_authentication()
        self.test_user_management()
        self.test_post_management()
        self.test_engagement_analysis()
        self.test_weekly_reports()
        self.test_pdf_export()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test['success']:
                    print(f"  - {test['test']}: {test['message']}")
                    if test['details']:
                        print(f"    Details: {test['details']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)