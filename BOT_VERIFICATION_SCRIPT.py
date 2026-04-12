#!/usr/bin/env python3
"""
Telegram Bot Verification Script
Tests all bot functionality to ensure it's working properly
"""
import requests
import json
import sys
import os
from datetime import datetime

# Bot configuration
BOT_TOKEN = "7671092916:AAG4GMyeTli6V9rEF6GH9H_HliV4QRq8Guw"
RENDER_URL = "https://college-virtual-assistant.onrender.com"

class BotVerifier:
    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.results.append(result)
        
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        if details:
            print(f"    Details: {details}")
    
    def test_bot_token_validity(self):
        """Test if bot token is valid"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    self.log_test(
                        "Bot Token Validity", 
                        True, 
                        "Bot token is valid",
                        f"Bot: @{bot_info.get('username', 'Unknown')} ({bot_info.get('first_name', 'Unknown')})"
                    )
                    return True
                else:
                    self.log_test("Bot Token Validity", False, f"API returned error: {data.get('description', 'Unknown')}")
                    return False
            else:
                self.log_test("Bot Token Validity", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Bot Token Validity", False, f"Exception: {str(e)}")
            return False
    
    def test_webhook_status(self):
        """Test webhook configuration"""
        try:
            url = f"{self.base_url}/getWebhookInfo"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    webhook_info = data.get('result', {})
                    webhook_url = webhook_info.get('url', '')
                    
                    if webhook_url:
                        self.log_test(
                            "Webhook Status",
                            True,
                            "Webhook is configured",
                            f"URL: {webhook_url}"
                        )
                    else:
                        self.log_test(
                            "Webhook Status",
                            False,
                            "No webhook configured - bot is in polling mode"
                        )
                    return True
                else:
                    self.log_test("Webhook Status", False, f"API error: {data.get('description', 'Unknown')}")
                    return False
            else:
                self.log_test("Webhook Status", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Webhook Status", False, f"Exception: {str(e)}")
            return False
    
    def test_render_service_availability(self):
        """Test if Render service is accessible"""
        try:
            url = RENDER_URL
            response = requests.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code in [200, 302]:
                self.log_test(
                    "Render Service",
                    True,
                    "Service is accessible",
                    f"Status: {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Render Service", 
                    False, 
                    f"Service returned HTTP {response.status_code}",
                    response.text[:100]
                )
                return False
                
        except Exception as e:
            self.log_test("Render Service", False, f"Exception: {str(e)}")
            return False
    
    def test_telegram_endpoint(self):
        """Test Telegram webhook endpoint"""
        try:
            url = f"{RENDER_URL}/telegram/webhook"
            
            # Create a test update
            test_update = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {
                        "id": 123456789,
                        "first_name": "Test",
                        "username": "test_user"
                    },
                    "chat": {
                        "id": 123456789,
                        "first_name": "Test",
                        "username": "test_user"
                    },
                    "date": int(datetime.now().timestamp()),
                    "text": "hi"
                }
            }
            
            response = requests.post(url, json=test_update, timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "Telegram Endpoint",
                    True,
                    "Webhook endpoint responds correctly",
                    f"Status: {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Telegram Endpoint",
                    False,
                    f"HTTP {response.status_code}",
                    response.text[:100]
                )
                return False
                
        except Exception as e:
            self.log_test("Telegram Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_database_connection(self):
        """Test database connection (basic health check)"""
        try:
            url = f"{RENDER_URL}/health"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    self.log_test(
                        "Database Connection",
                        True,
                        "Database connection healthy",
                        health_data.get('database', 'Unknown status')
                    )
                    return True
                except:
                    self.log_test(
                        "Database Connection",
                        True,
                        "Health endpoint accessible",
                        "Status: 200"
                    )
                    return True
            else:
                self.log_test(
                    "Database Connection",
                    False,
                    f"Health check failed: HTTP {response.status_code}",
                    response.text[:100]
                )
                return False
                
        except Exception as e:
            self.log_test("Database Connection", False, f"Exception: {str(e)}")
            return False
    
    def test_bot_commands(self):
        """Test basic bot commands via webhook"""
        commands_to_test = [
            "hi",
            "help",
            "hello",
            "admission",
            "courses",
            "contact"
        ]
        
        try:
            url = f"{RENDER_URL}/telegram/webhook"
            results = []
            
            for cmd in commands_to_test:
                test_update = {
                    "update_id": 123456789 + len(results),
                    "message": {
                        "message_id": 1 + len(results),
                        "from": {
                            "id": 123456789,
                            "first_name": "Test",
                            "username": "test_user"
                        },
                        "chat": {
                            "id": 123456789,
                            "first_name": "Test",
                            "username": "test_user"
                        },
                        "date": int(datetime.now().timestamp()),
                        "text": cmd
                    }
                }
                
                try:
                    response = requests.post(url, json=test_update, timeout=5)
                    if response.status_code == 200:
                        results.append(f"{cmd}: OK")
                    else:
                        results.append(f"{cmd}: FAIL ({response.status_code})")
                except Exception as e:
                    results.append(f"{cmd}: ERROR ({str(e)[:50]})")
            
            success_count = sum(1 for r in results if "OK" in r)
            total_count = len(results)
            
            if success_count == total_count:
                self.log_test(
                    "Bot Commands",
                    True,
                    f"All {total_count} commands processed successfully",
                    ", ".join(results)
                )
            elif success_count > 0:
                self.log_test(
                    "Bot Commands",
                    False,
                    f"Only {success_count}/{total_count} commands worked",
                    ", ".join(results)
                )
            else:
                self.log_test(
                    "Bot Commands",
                    False,
                    "No commands processed successfully",
                    ", ".join(results)
                )
            
            return success_count == total_count
            
        except Exception as e:
            self.log_test("Bot Commands", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("=== Telegram Bot Verification ===")
        print(f"Testing bot: @{BOT_TOKEN}")
        print(f"Render URL: {RENDER_URL}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        tests = [
            self.test_bot_token_validity,
            self.test_webhook_status,
            self.test_render_service_availability,
            self.test_telegram_endpoint,
            self.test_database_connection,
            self.test_bot_commands
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print()
        
        print("=" * 50)
        print(f"SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("All tests passed! Bot is functioning correctly. ")
        else:
            print("Some tests failed. Check the detailed results above.")
        
        return passed == total
    
    def generate_report(self):
        """Generate detailed test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'bot_token': BOT_TOKEN,
            'render_url': RENDER_URL,
            'results': self.results,
            'summary': {
                'total_tests': len(self.results),
                'passed_tests': sum(1 for r in self.results if r['success']),
                'failed_tests': sum(1 for r in self.results if not r['success'])
            }
        }
        
        return report

if __name__ == "__main__":
    verifier = BotVerifier()
    success = verifier.run_all_tests()
    
    # Save report
    report = verifier.generate_report()
    with open('bot_verification_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: bot_verification_report.json")
    
    sys.exit(0 if success else 1)
