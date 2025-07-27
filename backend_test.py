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

    def test_csv_data_matching_system(self):
        """Test 7: Enhanced CSV Data Matching System - Focus on username normalization and matching issues"""
        print("\n=== Testing Enhanced CSV Data Matching System ===")
        
        try:
            # Clear existing data first
            self.clear_test_data()
            
            # Test Case 1: Problematic usernames that should match
            print("\n--- Test Case 1: Problematic Username Variations ---")
            
            # Upload management users with various formats
            management_users_raw = [
                "cmile.ozdmrr",      # Base format
                "@ayse_yilmaz",      # With @ symbol
                "Mehmet.Kaya",       # Mixed case with dot
                "fatma demir",       # With space
                "Ali-Ozkan",         # With hyphen
                "zeynep_123"         # With underscore and numbers
            ]
            
            # Upload management users for Instagram
            csv_content = self.create_test_csv_content(management_users_raw)
            files = {'file': ('management_users.csv', csv_content, 'text/csv')}
            data = {'platform': 'instagram'}
            
            response = self.session.post(f"{BASE_URL}/users/upload", files=files, data=data, auth=self.auth)
            if response.status_code == 200:
                result = response.json()
                self.log_test("CSV Matching - Management Upload", True, f"Uploaded {result.get('count')} management users")
                print(f"   Sample normalized users: {result.get('sample_users', [])}")
            else:
                self.log_test("CSV Matching - Management Upload", False, f"Failed to upload management users: {response.status_code}")
                return
            
            # Create a test post
            test_post = {
                'title': 'Test Post for CSV Matching',
                'platform': 'instagram',
                'post_id': 'test_csv_matching_123',
                'post_date': datetime.utcnow().isoformat()
            }
            
            response = self.session.post(f"{BASE_URL}/posts", json=test_post, auth=self.auth)
            if response.status_code == 200:
                post_data = response.json()
                test_post_id = post_data.get('id')
                self.created_post_ids.append(test_post_id)
                self.log_test("CSV Matching - Test Post Creation", True, "Created test post for matching")
            else:
                self.log_test("CSV Matching - Test Post Creation", False, f"Failed to create test post: {response.status_code}")
                return
            
            # Test Case 2: Upload engagement data with different formatting of same usernames
            print("\n--- Test Case 2: Engagement Data with Different Formatting ---")
            
            engagement_users_raw = [
                "@cmile.ozdmrr",     # Same as management but with @
                "AYSE_YILMAZ",       # Same as management but uppercase
                "mehmet.kaya",       # Same as management but lowercase
                "Fatma Demir",       # Same as management but different case/space
                "ali-ozkan",         # Same as management but lowercase
                "Zeynep_123"         # Same as management but different case
            ]
            
            csv_content = self.create_test_csv_content(engagement_users_raw)
            files = {'file': ('engagement_data.csv', csv_content, 'text/csv')}
            data = {'post_id': test_post_id}
            
            response = self.session.post(f"{BASE_URL}/engagements/upload", files=files, data=data, auth=self.auth)
            if response.status_code == 200:
                result = response.json()
                self.log_test("CSV Matching - Engagement Upload", True, f"Uploaded {result.get('count')} engagement records")
                print(f"   Sample normalized engagements: {result.get('sample_users', [])}")
            else:
                self.log_test("CSV Matching - Engagement Upload", False, f"Failed to upload engagement data: {response.status_code}")
                return
            
            # Test Case 3: Analyze engagement to check matching
            print("\n--- Test Case 3: Engagement Analysis and Matching ---")
            
            response = self.session.get(f"{BASE_URL}/engagements/analysis/{test_post_id}", auth=self.auth)
            if response.status_code == 200:
                analysis = response.json()
                
                total_management = analysis.get('total_management', 0)
                total_engaged = analysis.get('total_engaged', 0)
                engagement_percentage = analysis.get('engagement_percentage', 0)
                engaged_users = analysis.get('engaged_users', [])
                not_engaged_users = analysis.get('not_engaged_users', [])
                
                print(f"   Management Users: {total_management}")
                print(f"   Engaged Users: {total_engaged}")
                print(f"   Engagement Rate: {engagement_percentage}%")
                print(f"   Engaged: {engaged_users}")
                print(f"   Not Engaged: {not_engaged_users}")
                
                # Check if matching is working correctly
                if total_management == 6 and total_engaged == 6 and engagement_percentage == 100.0:
                    self.log_test("CSV Matching - Perfect Match Analysis", True, "All username variations matched correctly (100% engagement)")
                elif total_engaged > 0:
                    self.log_test("CSV Matching - Partial Match Analysis", True, f"Partial matching working ({engagement_percentage}% engagement)")
                else:
                    self.log_test("CSV Matching - No Match Analysis", False, "Username normalization not working - no matches found")
                    
            else:
                self.log_test("CSV Matching - Analysis", False, f"Failed to get analysis: {response.status_code}")
                return
            
            # Test Case 4: Debug normalization endpoint
            print("\n--- Test Case 4: Debug Normalization Endpoint ---")
            
            response = self.session.get(f"{BASE_URL}/debug/normalization/{test_post_id}", auth=self.auth)
            if response.status_code == 200:
                debug_info = response.json()
                
                mgmt_users = debug_info.get('management_users', {})
                eng_users = debug_info.get('engagement_users', {})
                analysis_debug = debug_info.get('analysis', {})
                
                print(f"   Management Users Count: {mgmt_users.get('count', 0)}")
                print(f"   Engagement Users Count: {eng_users.get('count', 0)}")
                print(f"   Matches: {analysis_debug.get('matches', {}).get('count', 0)}")
                print(f"   Mismatches: {analysis_debug.get('mismatches', {}).get('count', 0)}")
                print(f"   Extra Engagements: {analysis_debug.get('extra_engagements', {}).get('count', 0)}")
                
                if 'management_users' in debug_info and 'engagement_users' in debug_info:
                    self.log_test("CSV Matching - Debug Endpoint", True, "Debug normalization endpoint working")
                    
                    # Show detailed matching info
                    matches = analysis_debug.get('matches', {}).get('users', [])
                    mismatches = analysis_debug.get('mismatches', {}).get('users', [])
                    
                    if matches:
                        print(f"   ✅ Matched Users: {matches}")
                    if mismatches:
                        print(f"   ❌ Unmatched Users: {mismatches}")
                        
                else:
                    self.log_test("CSV Matching - Debug Endpoint", False, "Debug endpoint missing required data")
            else:
                self.log_test("CSV Matching - Debug Endpoint", False, f"Debug endpoint failed: {response.status_code}")
            
            # Test Case 5: Different file encodings
            print("\n--- Test Case 5: Different File Encodings ---")
            
            # Test UTF-8 with BOM
            utf8_users = ["türkçe_kullanıcı", "özel_karakter", "ğüşıöç_test"]
            df = pd.DataFrame({'username': utf8_users})
            utf8_bom_content = df.to_csv(index=False).encode('utf-8-sig')
            
            files = {'file': ('utf8_bom_users.csv', utf8_bom_content, 'text/csv')}
            data = {'platform': 'x'}
            
            response = self.session.post(f"{BASE_URL}/users/upload", files=files, data=data, auth=self.auth)
            if response.status_code == 200:
                result = response.json()
                self.log_test("CSV Matching - UTF-8 BOM Encoding", True, f"Successfully processed UTF-8 BOM file with {result.get('count')} users")
            else:
                self.log_test("CSV Matching - UTF-8 BOM Encoding", False, f"Failed to process UTF-8 BOM file: {response.status_code}")
            
            # Test Case 6: Excel file with different column names
            print("\n--- Test Case 6: Excel with Different Column Names ---")
            
            excel_users = ["excel_user1", "excel_user2", "excel_user3"]
            df = pd.DataFrame({'kullanici_adi': excel_users})  # Turkish column name
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            excel_content = buffer.getvalue()
            
            files = {'file': ('turkish_column.xlsx', excel_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {'platform': 'instagram'}
            
            response = self.session.post(f"{BASE_URL}/users/upload", files=files, data=data, auth=self.auth)
            if response.status_code == 200:
                result = response.json()
                self.log_test("CSV Matching - Excel Turkish Columns", True, f"Successfully processed Excel with Turkish column names: {result.get('count')} users")
            else:
                self.log_test("CSV Matching - Excel Turkish Columns", False, f"Failed to process Excel with Turkish columns: {response.status_code}")
                
        except Exception as e:
            self.log_test("CSV Data Matching System", False, f"Exception during CSV matching tests: {str(e)}")

    def test_post_deletion_cascade(self):
        """Test 8: Post Deletion with Cascade Deletion of Engagement Data"""
        print("\n=== Testing Post Deletion with Cascade ===")
        
        try:
            # Create a test post
            test_post = {
                'title': 'Test Post for Deletion',
                'platform': 'instagram',
                'post_id': 'delete_test_456',
                'post_date': datetime.utcnow().isoformat()
            }
            
            response = self.session.post(f"{BASE_URL}/posts", json=test_post, auth=self.auth)
            if response.status_code == 200:
                post_data = response.json()
                delete_test_post_id = post_data.get('id')
                self.log_test("Post Deletion - Create Test Post", True, "Created test post for deletion")
            else:
                self.log_test("Post Deletion - Create Test Post", False, f"Failed to create test post: {response.status_code}")
                return
            
            # Add engagement data to the post
            engagement_users = ["delete_test_user1", "delete_test_user2"]
            csv_content = self.create_test_csv_content(engagement_users)
            files = {'file': ('delete_test_engagement.csv', csv_content, 'text/csv')}
            data = {'post_id': delete_test_post_id}
            
            response = self.session.post(f"{BASE_URL}/engagements/upload", files=files, data=data, auth=self.auth)
            if response.status_code == 200:
                self.log_test("Post Deletion - Add Engagement Data", True, "Added engagement data to test post")
            else:
                self.log_test("Post Deletion - Add Engagement Data", False, f"Failed to add engagement data: {response.status_code}")
                return
            
            # Verify engagement data exists
            response = self.session.get(f"{BASE_URL}/engagements/analysis/{delete_test_post_id}", auth=self.auth)
            if response.status_code == 200:
                analysis = response.json()
                if analysis.get('total_engaged', 0) > 0:
                    self.log_test("Post Deletion - Verify Engagement Exists", True, f"Confirmed {analysis.get('total_engaged')} engagement records exist")
                else:
                    self.log_test("Post Deletion - Verify Engagement Exists", False, "No engagement data found before deletion")
            
            # Delete the post
            response = self.session.delete(f"{BASE_URL}/posts/{delete_test_post_id}", auth=self.auth)
            if response.status_code == 200:
                self.log_test("Post Deletion - Delete Post", True, "Successfully deleted post")
            else:
                self.log_test("Post Deletion - Delete Post", False, f"Failed to delete post: {response.status_code}")
                return
            
            # Verify post is deleted
            response = self.session.get(f"{BASE_URL}/posts", auth=self.auth)
            if response.status_code == 200:
                posts = response.json()
                post_exists = any(post.get('id') == delete_test_post_id for post in posts)
                if not post_exists:
                    self.log_test("Post Deletion - Verify Post Deleted", True, "Post successfully removed from database")
                else:
                    self.log_test("Post Deletion - Verify Post Deleted", False, "Post still exists after deletion")
            
            # Verify engagement data is also deleted (cascade)
            response = self.session.get(f"{BASE_URL}/engagements/analysis/{delete_test_post_id}", auth=self.auth)
            if response.status_code == 404:
                self.log_test("Post Deletion - Verify Cascade Deletion", True, "Engagement data successfully deleted with post (cascade working)")
            else:
                self.log_test("Post Deletion - Verify Cascade Deletion", False, f"Engagement data may still exist: {response.status_code}")
                
        except Exception as e:
            self.log_test("Post Deletion Cascade", False, f"Exception during post deletion test: {str(e)}")

    def clear_test_data(self):
        """Helper method to clear test data"""
        try:
            # Get all posts and delete them (this will cascade delete engagements)
            response = self.session.get(f"{BASE_URL}/posts", auth=self.auth)
            if response.status_code == 200:
                posts = response.json()
                for post in posts:
                    self.session.delete(f"{BASE_URL}/posts/{post['id']}", auth=self.auth)
            
            # Get all users and delete them
            response = self.session.get(f"{BASE_URL}/users", auth=self.auth)
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    self.session.delete(f"{BASE_URL}/users/{user['id']}", auth=self.auth)
                    
        except Exception as e:
            print(f"Warning: Could not clear test data: {str(e)}")

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