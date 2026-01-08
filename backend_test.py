#!/usr/bin/env python3
"""
Backend API Testing Suite for HiringReferrals Platform
Tests comprehensive business logic and database enhancements
"""

import requests
import json
import sys
import time
from datetime import datetime, timezone, timedelta
import uuid

# Configuration
BASE_URL = "https://talentlink-72.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Test credentials
TEST_ADMIN = {"email": "admin@hire.com", "password": "adminpassword"}
TEST_RECRUITER = {"email": "recruiter@refer.com", "password": "password"}

class BackendTester:
    def __init__(self):
        self.admin_token = None
        self.recruiter_token = None
        self.admin_user = None
        self.recruiter_user = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if error:
            print(f"   Error: {error}")
        if details:
            print(f"   Details: {details}")
    
    def make_request(self, method, endpoint, data=None, token=None, params=None):
        """Make HTTP request with error handling"""
        url = f"{BASE_URL}{endpoint}"
        headers = HEADERS.copy()
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            
            return response
        except requests.exceptions.RequestException as e:
            return None
    
    def test_authentication(self):
        """Test user authentication"""
        print("\n=== Testing Authentication ===")
        
        # Test admin login
        response = self.make_request("POST", "/auth/login", TEST_ADMIN)
        if response and response.status_code == 200:
            data = response.json()
            self.admin_token = data.get("access_token")
            self.admin_user = data.get("user")
            self.log_result("Admin Login", True, f"User ID: {self.admin_user.get('id')}")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Admin Login", False, error=error)
            return False
        
        # Test recruiter login
        response = self.make_request("POST", "/auth/login", TEST_RECRUITER)
        if response and response.status_code == 200:
            data = response.json()
            self.recruiter_token = data.get("access_token")
            self.recruiter_user = data.get("user")
            self.log_result("Recruiter Login", True, f"User ID: {self.recruiter_user.get('id')}")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Recruiter Login", False, error=error)
            return False
        
        return True
    
    def test_commission_calculation(self):
        """Test commission calculation system"""
        print("\n=== Testing Commission Calculation System ===")
        
        if not self.admin_token:
            self.log_result("Commission Tests", False, error="No admin token available")
            return
        
        # Test commission calculation with high package
        test_data = {
            "user_id": self.recruiter_user["id"],
            "annual_package": 1500000,  # 15L package - should be senior level (12%)
            "currency": "INR"
        }
        
        response = self.make_request("POST", "/commission/calculate", test_data, self.admin_token)
        if response and response.status_code == 200:
            data = response.json()
            details = data.get("calculation_details", {})
            
            # Verify senior level rate (12%)
            expected_rate = 0.12
            actual_rate = details.get("base_commission_rate", 0)
            
            if abs(actual_rate - expected_rate) < 0.001:  # Allow small floating point differences
                self.log_result("Commission Calculation - Senior Level", True, 
                              f"Rate: {actual_rate*100}%, Gross: ₹{details.get('gross_commission', 0)}")
            else:
                self.log_result("Commission Calculation - Senior Level", False, 
                              error=f"Expected rate {expected_rate*100}%, got {actual_rate*100}%")
            
            # Verify TDS deduction (should be 10% since commission > ₹30,000)
            gross = details.get("gross_commission", 0)
            tds = details.get("tds_amount", 0)
            expected_tds = gross * 0.10 if gross > 30000 else 0
            
            if abs(tds - expected_tds) < 1:  # Allow ₹1 difference for rounding
                self.log_result("TDS Calculation", True, f"TDS: ₹{tds} on gross ₹{gross}")
            else:
                self.log_result("TDS Calculation", False, 
                              error=f"Expected TDS ₹{expected_tds}, got ₹{tds}")
            
            # Verify platform fee (5%)
            platform_fee = details.get("platform_fee", 0)
            expected_fee = gross * 0.05
            
            if abs(platform_fee - expected_fee) < 1:
                self.log_result("Platform Fee Calculation", True, f"Fee: ₹{platform_fee}")
            else:
                self.log_result("Platform Fee Calculation", False, 
                              error=f"Expected fee ₹{expected_fee}, got ₹{platform_fee}")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Commission Calculation API", False, error=error)
        
        # Test commission summary
        response = self.make_request("GET", "/commission/summary", token=self.recruiter_token)
        if response and response.status_code == 200:
            data = response.json()
            self.log_result("Commission Summary", True, 
                          f"Tier: {data.get('current_tier')}, Multiplier: {data.get('tier_multiplier')}")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Commission Summary", False, error=error)
        
        # Test commission rates (public endpoint)
        response = self.make_request("GET", "/commission/rates")
        if response and response.status_code == 200:
            self.log_result("Commission Rates API", True, "Public rates retrieved")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Commission Rates API", False, error=error)
    
    def test_candidate_matching(self):
        """Test candidate matching system"""
        print("\n=== Testing Candidate Matching System ===")
        
        if not self.admin_token:
            self.log_result("Matching Tests", False, error="No admin token available")
            return
        
        # First, create a test job
        job_data = {
            "title": "Senior Python Developer",
            "description": "Looking for experienced Python developer",
            "requirements": ["python", "django", "postgresql", "aws"],
            "location": "Bangalore",
            "salary_range": "12-18 LPA",
            "experience_level": "senior",
            "employment_type": "full-time"
        }
        
        response = self.make_request("POST", "/jobs", job_data, self.admin_token)
        if response and response.status_code == 200:
            job = response.json()
            job_id = job.get("id")
            self.log_result("Test Job Creation", True, f"Job ID: {job_id}")
            
            # Test candidate matching for this job
            response = self.make_request("GET", f"/matching/job/{job_id}/candidates", token=self.admin_token)
            if response and response.status_code == 200:
                candidates = response.json()
                self.log_result("Candidate Matching", True, f"Found {len(candidates)} matching candidates")
            else:
                error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                self.log_result("Candidate Matching", False, error=error)
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Test Job Creation", False, error=error)
        
        # Test match score calculation
        match_data = {
            "candidate": {
                "skills": ["python", "django", "react", "postgresql"],
                "experience_years": 5,
                "education": ["B.Tech Computer Science"],
                "location": "Bangalore",
                "expected_salary": 1400000
            },
            "job": {
                "requirements": ["python", "django", "postgresql"],
                "experience_min": 3,
                "experience_max": 7,
                "location": "Bangalore",
                "salary_min": 1200000,
                "salary_max": 1800000
            }
        }
        
        response = self.make_request("POST", "/matching/score", match_data, self.admin_token)
        if response and response.status_code == 200:
            data = response.json()
            score = data.get("overall_score", 0)
            self.log_result("Match Score Calculation", True, f"Score: {score}%")
        else:
            # This endpoint might not be implemented, so let's not fail the test
            self.log_result("Match Score Calculation", False, error="Endpoint not implemented or accessible")
    
    def test_application_pipeline(self):
        """Test application processing pipeline"""
        print("\n=== Testing Application Pipeline ===")
        
        if not self.admin_token:
            self.log_result("Pipeline Tests", False, error="No admin token available")
            return
        
        # Get existing applications for testing
        response = self.make_request("GET", "/applications", token=self.admin_token)
        if response and response.status_code == 200:
            applications = response.json()
            if applications:
                app_id = applications[0].get("id")
                
                # Test auto-screening
                response = self.make_request("POST", f"/applications/{app_id}/screen", token=self.admin_token)
                if response and response.status_code == 200:
                    data = response.json()
                    self.log_result("Auto-screening", True, 
                                  f"Score: {data.get('screening_score')}%, Recommendation: {data.get('recommendation')}")
                else:
                    error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                    self.log_result("Auto-screening", False, error=error)
                
                # Test status update
                status_data = {"status": "shortlisted", "notes": "Test status update"}
                response = self.make_request("PUT", f"/applications/{app_id}/status", status_data, self.admin_token)
                if response and response.status_code == 200:
                    self.log_result("Status Update", True, "Status updated to shortlisted")
                else:
                    error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                    self.log_result("Status Update", False, error=error)
                
                # Test status history
                response = self.make_request("GET", f"/applications/{app_id}/history", token=self.admin_token)
                if response and response.status_code == 200:
                    history = response.json()
                    self.log_result("Status History", True, f"Found {len(history)} history entries")
                else:
                    error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                    self.log_result("Status History", False, error=error)
                
                # Test interview scheduling
                interview_data = {
                    "interview_type": "technical",
                    "scheduled_at": (datetime.now() + timedelta(days=2)).isoformat(),
                    "duration_minutes": 60,
                    "meeting_link": "https://meet.google.com/test-link",
                    "notes": "Technical interview for Python role"
                }
                
                response = self.make_request("POST", f"/applications/{app_id}/interview", interview_data, self.admin_token)
                if response and response.status_code == 200:
                    interview = response.json()
                    interview_id = interview.get("interview_id")
                    self.log_result("Interview Scheduling", True, f"Interview ID: {interview_id}")
                    
                    # Test interview feedback
                    feedback_data = {
                        "rating": 8,
                        "technical_score": 85,
                        "communication_score": 90,
                        "cultural_fit_score": 80,
                        "comments": "Strong technical skills, good communication",
                        "recommendation": "proceed"
                    }
                    
                    response = self.make_request("POST", f"/interviews/{interview_id}/feedback", feedback_data, self.admin_token)
                    if response and response.status_code == 200:
                        self.log_result("Interview Feedback", True, "Feedback submitted successfully")
                    else:
                        error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                        self.log_result("Interview Feedback", False, error=error)
                else:
                    error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                    self.log_result("Interview Scheduling", False, error=error)
            else:
                self.log_result("Application Pipeline Tests", False, error="No applications found for testing")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Get Applications", False, error=error)
        
        # Test pipeline statistics
        response = self.make_request("GET", "/pipeline/stats", token=self.admin_token)
        if response and response.status_code == 200:
            stats = response.json()
            self.log_result("Pipeline Statistics", True, 
                          f"Total applications: {stats.get('total_applications', 0)}")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Pipeline Statistics", False, error=error)
    
    def test_bgv_system(self):
        """Test BGV (Background Verification) system"""
        print("\n=== Testing BGV System ===")
        
        if not self.admin_token:
            self.log_result("BGV Tests", False, error="No admin token available")
            return
        
        # Create BGV request
        bgv_data = {
            "candidate_id": self.recruiter_user["id"],  # Using recruiter as test candidate
            "application_id": str(uuid.uuid4()),  # Mock application ID
            "verification_types": ["identity", "address", "employment", "education"],
            "priority": "normal",
            "special_instructions": "Test BGV request for platform validation"
        }
        
        response = self.make_request("POST", "/bgv/requests", bgv_data, self.admin_token)
        if response and response.status_code == 200:
            bgv = response.json()
            bgv_id = bgv.get("bgv_id")
            self.log_result("BGV Request Creation", True, f"BGV ID: {bgv_id}")
            
            # Test BGV assignment
            assign_data = {
                "check_type": "identity",
                "specialist_id": self.admin_user["id"]  # Using admin as specialist
            }
            
            response = self.make_request("POST", f"/bgv/requests/{bgv_id}/assign", assign_data, self.admin_token)
            if response and response.status_code == 200:
                self.log_result("BGV Specialist Assignment", True, "Identity check assigned")
            else:
                error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                self.log_result("BGV Specialist Assignment", False, error=error)
            
            # Test BGV check update
            check_data = {
                "check_type": "identity",
                "status": "verified",
                "verification_data": {
                    "document_type": "aadhaar",
                    "document_number": "XXXX-XXXX-1234",
                    "verified": True
                },
                "remarks": "Identity verification completed successfully"
            }
            
            response = self.make_request("PUT", f"/bgv/requests/{bgv_id}/check", check_data, self.admin_token)
            if response and response.status_code == 200:
                self.log_result("BGV Check Update", True, "Identity check marked as verified")
            else:
                error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                self.log_result("BGV Check Update", False, error=error)
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("BGV Request Creation", False, error=error)
        
        # Test BGV requests listing
        response = self.make_request("GET", "/bgv/requests", token=self.admin_token)
        if response and response.status_code == 200:
            requests_list = response.json()
            self.log_result("BGV Requests Listing", True, f"Found {len(requests_list)} BGV requests")
            
            if requests_list:
                # Test individual BGV details
                bgv_id = requests_list[0].get("id")
                response = self.make_request("GET", f"/bgv/requests/{bgv_id}", token=self.admin_token)
                if response and response.status_code == 200:
                    self.log_result("BGV Details Retrieval", True, "BGV details retrieved successfully")
                else:
                    error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                    self.log_result("BGV Details Retrieval", False, error=error)
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("BGV Requests Listing", False, error=error)
    
    def test_audit_and_notifications(self):
        """Test audit logging and notifications"""
        print("\n=== Testing Audit & Notifications ===")
        
        if not self.admin_token:
            self.log_result("Audit Tests", False, error="No admin token available")
            return
        
        # Test user audit log
        user_id = self.recruiter_user["id"]
        response = self.make_request("GET", f"/audit/user/{user_id}", token=self.admin_token)
        if response and response.status_code == 200:
            audit_logs = response.json()
            self.log_result("User Audit Log", True, f"Found {len(audit_logs)} audit entries")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("User Audit Log", False, error=error)
        
        # Test security events (admin only)
        response = self.make_request("GET", "/audit/security", token=self.admin_token)
        if response and response.status_code == 200:
            security_events = response.json()
            self.log_result("Security Events", True, f"Found {len(security_events)} security events")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Security Events", False, error=error)
        
        # Test notifications
        response = self.make_request("GET", "/notifications", token=self.recruiter_token)
        if response and response.status_code == 200:
            notifications = response.json()
            self.log_result("User Notifications", True, f"Found {len(notifications)} notifications")
            
            if notifications and len(notifications) > 0:
                # Test marking notification as read
                notif_id = notifications[0].get("id")
                if notif_id:
                    response = self.make_request("PUT", f"/notifications/{notif_id}/read", token=self.recruiter_token)
                    if response and response.status_code == 200:
                        self.log_result("Mark Notification Read", True, "Notification marked as read")
                    else:
                        error = response.json().get("detail", "Unknown error") if response else "Connection failed"
                        self.log_result("Mark Notification Read", False, error=error)
                else:
                    self.log_result("Mark Notification Read", False, error="No notification ID found")
            else:
                self.log_result("Mark Notification Read", False, error="No notifications available to test")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("User Notifications", False, error=error)
    
    def test_user_profile(self):
        """Test user profile endpoints"""
        print("\n=== Testing User Profile ===")
        
        if not self.recruiter_token:
            self.log_result("Profile Tests", False, error="No recruiter token available")
            return
        
        # Test get profile
        response = self.make_request("GET", "/profile", token=self.recruiter_token)
        if response and response.status_code == 200:
            profile = response.json()
            self.log_result("Get Profile", True, f"Profile for {profile.get('full_name')}")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Get Profile", False, error=error)
        
        # Test update profile
        update_data = {
            "full_name": "Updated Recruiter Name",
            "phone": "+91-9876543210",
            "location": "Mumbai, India"
        }
        
        response = self.make_request("PUT", "/profile", update_data, self.recruiter_token)
        if response and response.status_code == 200:
            self.log_result("Update Profile", True, "Profile updated successfully")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Update Profile", False, error=error)
    
    def test_gamification_endpoints(self):
        """Test gamification system endpoints"""
        print("\n=== Testing Gamification System ===")
        
        if not self.recruiter_token:
            self.log_result("Gamification Tests", False, error="No recruiter token available")
            return
        
        user_id = self.recruiter_user["id"]
        
        # Test get achievements
        response = self.make_request("GET", "/gamification/achievements", token=self.recruiter_token)
        if response and response.status_code == 200:
            achievements = response.json()
            self.log_result("Get All Achievements", True, f"Found {len(achievements)} achievements")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Get All Achievements", False, error=error)
        
        # Test user points
        response = self.make_request("GET", f"/gamification/user/{user_id}/points", token=self.recruiter_token)
        if response and response.status_code == 200:
            points = response.json()
            self.log_result("Get User Points", True, f"Points: {points.get('total_points', 0)}")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Get User Points", False, error=error)
        
        # Test user stats
        response = self.make_request("GET", f"/gamification/user/{user_id}/stats", token=self.recruiter_token)
        if response and response.status_code == 200:
            stats = response.json()
            self.log_result("Get User Stats", True, f"Level: {stats.get('level', 1)}")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Get User Stats", False, error=error)
        
        # Test streak update
        response = self.make_request("POST", f"/gamification/user/{user_id}/streak/update", token=self.recruiter_token)
        if response and response.status_code == 200:
            streak = response.json()
            self.log_result("Update Streak", True, f"Current streak: {streak.get('current_streak', 0)}")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Update Streak", False, error=error)
        
        # Test leaderboard
        response = self.make_request("GET", "/gamification/leaderboard", token=self.recruiter_token)
        if response and response.status_code == 200:
            leaderboard = response.json()
            self.log_result("Get Leaderboard", True, f"Found {len(leaderboard)} users on leaderboard")
        else:
            error = response.json().get("detail", "Unknown error") if response else "Connection failed"
            self.log_result("Get Leaderboard", False, error=error)
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Testing Suite")
        print(f"Testing against: {BASE_URL}")
        
        # Authentication is required for all other tests
        if not self.test_authentication():
            print("❌ Authentication failed - stopping tests")
            return False
        
        # Run all test suites
        self.test_commission_calculation()
        self.test_candidate_matching()
        self.test_application_pipeline()
        self.test_bgv_system()
        self.test_audit_and_notifications()
        self.test_user_profile()
        self.test_gamification_endpoints()
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['error']}")
        
        print(f"\n📝 Detailed results saved to test_results.json")
        
        # Save detailed results
        with open("/app/test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)


if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Backend testing completed!")
    else:
        print("\n💥 Backend testing failed!")
        sys.exit(1)