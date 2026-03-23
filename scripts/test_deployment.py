#!/usr/bin/env python3
"""
Deployment Testing Script
Tests database connectivity and application functionality after deployment
"""

import os
import sys
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DeploymentTester:
    """Test deployment functionality"""
    
    def __init__(self):
        self.app_url = os.environ.get('PRODUCTION_APP_URL', 'http://localhost:5000')
        self.test_results = []
        self.start_time = datetime.now()
    
    def log_test(self, test_name: str, success: bool, message: str, response_time: float = 0):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if response_time > 0:
            print(f"   ⏱️  Response time: {response_time:.2f}s")
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.app_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test(
                        "Health Check",
                        True,
                        f"Application is healthy - Database: {data.get('database', 'unknown')}",
                        response_time
                    )
                else:
                    self.log_test(
                        "Health Check",
                        False,
                        f"Application unhealthy: {data.get('status', 'unknown')}",
                        response_time
                    )
            else:
                self.log_test(
                    "Health Check",
                    False,
                    f"HTTP {response.status_code}",
                    response_time
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
    
    def test_static_assets(self):
        """Test static asset loading"""
        static_files = [
            "/static/css/style.css",
            "/static/js/main.js",
            "/favicon.ico"
        ]
        
        for file_path in static_files:
            try:
                start_time = time.time()
                response = requests.get(f"{self.app_url}{file_path}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code in [200, 204]:  # 204 for favicon
                    self.log_test(
                        f"Static Asset: {file_path}",
                        True,
                        f"HTTP {response.status_code}",
                        response_time
                    )
                else:
                    self.log_test(
                        f"Static Asset: {file_path}",
                        False,
                        f"HTTP {response.status_code}",
                        response_time
                    )
                    
            except requests.exceptions.RequestException as e:
                self.log_test(f"Static Asset: {file_path}", False, f"Connection error: {str(e)}")
    
    def test_admin_dashboard(self):
        """Test admin dashboard accessibility"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.app_url}/admin/dashboard", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 302:  # Redirect to login (expected)
                self.log_test(
                    "Admin Dashboard",
                    True,
                    "Redirects to login (expected behavior)",
                    response_time
                )
            elif response.status_code == 200:
                self.log_test(
                    "Admin Dashboard",
                    True,
                    "Accessible (already logged in)",
                    response_time
                )
            else:
                self.log_test(
                    "Admin Dashboard",
                    False,
                    f"HTTP {response.status_code}",
                    response_time
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test("Admin Dashboard", False, f"Connection error: {str(e)}")
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        api_endpoints = [
            "/api/health",
            "/admin/bot-status",
            "/admin/refresh-activity"
        ]
        
        for endpoint in api_endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.app_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code in [200, 401, 403]:  # 401/403 expected for protected endpoints
                    self.log_test(
                        f"API Endpoint: {endpoint}",
                        True,
                        f"HTTP {response.status_code}",
                        response_time
                    )
                else:
                    self.log_test(
                        f"API Endpoint: {endpoint}",
                        False,
                        f"HTTP {response.status_code}",
                        response_time
                    )
                    
            except requests.exceptions.RequestException as e:
                self.log_test(f"API Endpoint: {endpoint}", False, f"Connection error: {str(e)}")
    
    def test_database_connectivity(self):
        """Test database connectivity through API"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.app_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                db_status = data.get('database', 'unknown')
                
                if db_status == 'connected':
                    self.log_test(
                        "Database Connectivity",
                        True,
                        "Database connection successful",
                        response_time
                    )
                else:
                    self.log_test(
                        "Database Connectivity",
                        False,
                        f"Database not connected: {db_status}",
                        response_time
                    )
            else:
                self.log_test(
                    "Database Connectivity",
                    False,
                    f"Health check failed: HTTP {response.status_code}",
                    response_time
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test("Database Connectivity", False, f"Connection error: {str(e)}")
    
    def test_page_load_times(self):
        """Test page load times for key pages"""
        pages = [
            ("/", "Home Page"),
            ("/login", "Login Page"),
            ("/admin/login", "Admin Login"),
            ("/faculty/login", "Faculty Login")
        ]
        
        for path, name in pages:
            try:
                start_time = time.time()
                response = requests.get(f"{self.app_url}{path}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code in [200, 302]:
                    status = "Good" if response_time < 2 else "Slow" if response_time < 5 else "Very Slow"
                    self.log_test(
                        f"Page Load: {name}",
                        True,
                        f"HTTP {response.status_code} - {status}",
                        response_time
                    )
                else:
                    self.log_test(
                        f"Page Load: {name}",
                        False,
                        f"HTTP {response.status_code}",
                        response_time
                    )
                    
            except requests.exceptions.RequestException as e:
                self.log_test(f"Page Load: {name}", False, f"Connection error: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling"""
        error_pages = [
            ("/nonexistent-page", "404 Error"),
            ("/admin/protected", "403 Error")
        ]
        
        for path, name in error_pages:
            try:
                start_time = time.time()
                response = requests.get(f"{self.app_url}{path}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code in [404, 403, 302]:  # 302 for protected pages
                    self.log_test(
                        f"Error Handling: {name}",
                        True,
                        f"Proper error handling: HTTP {response.status_code}",
                        response_time
                    )
                else:
                    self.log_test(
                        f"Error Handling: {name}",
                        False,
                        f"Unexpected response: HTTP {response.status_code}",
                        response_time
                    )
                    
            except requests.exceptions.RequestException as e:
                self.log_test(f"Error Handling: {name}", False, f"Connection error: {str(e)}")
    
    def run_all_tests(self):
        """Run all deployment tests"""
        print("🧪 Starting Deployment Tests")
        print("=" * 50)
        print(f"Testing URL: {self.app_url}")
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # Run tests
        self.test_health_endpoint()
        self.test_database_connectivity()
        self.test_static_assets()
        self.test_admin_dashboard()
        self.test_api_endpoints()
        self.test_page_load_times()
        self.test_error_handling()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        avg_response_time = sum(
            result['response_time'] for result in self.test_results 
            if result['response_time'] > 0
        ) / len([r for r in self.test_results if r['response_time'] > 0]) if self.test_results else 0
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"Duration: {duration:.2f}s")
        print(f"Average Response Time: {avg_response_time:.2f}s")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['message']}")
        
        # Overall status
        if failed_tests == 0:
            print("\n🎉 All tests passed! Deployment is working correctly.")
        elif failed_tests <= 2:
            print("\n⚠️  Minor issues detected. Deployment is mostly functional.")
        else:
            print("\n❌ Multiple issues detected. Please review deployment.")
        
        # Save results to file
        self.save_test_results()
    
    def save_test_results(self):
        """Save test results to file"""
        results_file = f"deployment_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results_data = {
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results if r['success']),
                'failed_tests': sum(1 for r in self.test_results if not r['success']),
                'test_url': self.app_url,
                'start_time': self.start_time.isoformat(),
                'duration': (datetime.now() - self.start_time).total_seconds()
            },
            'results': self.test_results
        }
        
        try:
            with open(results_file, 'w') as f:
                import json
                json.dump(results_data, f, indent=2)
            print(f"\n📄 Test results saved to: {results_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save test results: {str(e)}")

def main():
    """Main test function"""
    if len(sys.argv) > 1:
        app_url = sys.argv[1]
        os.environ['PRODUCTION_APP_URL'] = app_url
    
    tester = DeploymentTester()
    tester.run_all_tests()

if __name__ == "__main__":
    print("Deployment Testing Tool")
    print("Usage: python test_deployment.py [app_url]")
    print("")
    print("Examples:")
    print("  python test_deployment.py https://your-app.onrender.com")
    print("  python test_deployment.py http://localhost:5000")
    print("")
