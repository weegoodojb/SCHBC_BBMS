"""
Comprehensive API Test Script for SCHBC BBMS
Tests authentication and inventory management endpoints
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "emp_id": "TEST001",
    "password": "test123"
}

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_json(data, indent=2):
    """Print JSON data"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def test_health_check():
    """Test health check endpoint"""
    print_header("1. Health Check Test")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            print_success("Health check passed")
            print_info("Response:")
            print_json(response.json())
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_login():
    """Test login endpoint"""
    print_header("2. Authentication Test - Login")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Login successful")
            print_info("Response:")
            print_json(data)
            return data.get("access_token")
        else:
            print_error(f"Login failed with status {response.status_code}")
            print_json(response.json())
            return None
    except Exception as e:
        print_error(f"Login test failed: {e}")
        return None


def test_login_invalid():
    """Test login with invalid credentials"""
    print_header("3. Authentication Test - Invalid Credentials")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"emp_id": "INVALID", "password": "wrong"}
        )
        
        if response.status_code == 401:
            print_success("Invalid credentials correctly rejected")
            print_info("Response:")
            print_json(response.json())
            return True
        else:
            print_error(f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Invalid login test failed: {e}")
        return False


def test_inventory_status():
    """Test inventory status endpoint"""
    print_header("4. Inventory Status Test")
    
    try:
        response = requests.get(f"{BASE_URL}/api/inventory/status")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Inventory status retrieved")
            print_info(f"Total items: {data['total_items']}")
            print_info(f"Alert count: {data['alert_count']}")
            print_info(f"RBC ratio: {data['rbc_ratio']}")
            
            # Show sample items
            print_info("\nSample inventory items (first 5):")
            for item in data['items'][:5]:
                alert_flag = "🔴 ALERT" if item['is_alert'] else "✓"
                target_info = f", Target: {item['target_qty']}" if item['target_qty'] is not None else ""
                print(f"  {alert_flag} {item['blood_type']}형 {item['preparation']}: "
                      f"{item['current_qty']}/{item['safety_qty']}{target_info}")
            
            # Show RBC items with target calculation
            print_info("\nRBC items with dynamic targets:")
            rbc_items = [item for item in data['items'] if item['component'] == 'RBC']
            for item in rbc_items[:8]:  # Show first 8 RBC items
                print(f"  {item['blood_type']}형 {item['preparation']}: "
                      f"Current={item['current_qty']}, "
                      f"Safety={item['safety_qty']}, "
                      f"Target={item['target_qty']}, "
                      f"Alert<{item['alert_threshold']}")
            
            return data
        else:
            print_error(f"Inventory status failed with status {response.status_code}")
            print_json(response.json())
            return None
    except Exception as e:
        print_error(f"Inventory status test failed: {e}")
        return None


def test_inventory_update():
    """Test inventory update endpoint"""
    print_header("5. Inventory Update Test")
    
    try:
        # Get PRBC prep_id (should be 1 from seed data)
        update_data = {
            "blood_type": "A",
            "prep_id": 1,  # PRBC
            "in_qty": 10,
            "out_qty": 0,
            "remark": "API 테스트 입고 - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print_info("Updating inventory:")
        print_json(update_data)
        
        response = requests.post(
            f"{BASE_URL}/api/inventory/update",
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Inventory updated successfully")
            print_info("Response:")
            print_json(data)
            return data
        else:
            print_error(f"Inventory update failed with status {response.status_code}")
            print_json(response.json())
            return None
    except Exception as e:
        print_error(f"Inventory update test failed: {e}")
        return None


def test_inventory_update_with_outgoing():
    """Test inventory update with outgoing quantity"""
    print_header("6. Inventory Update Test - Outgoing")
    
    try:
        update_data = {
            "blood_type": "A",
            "prep_id": 1,  # PRBC
            "in_qty": 0,
            "out_qty": 3,
            "remark": "API 테스트 출고 - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print_info("Updating inventory (outgoing):")
        print_json(update_data)
        
        response = requests.post(
            f"{BASE_URL}/api/inventory/update",
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Inventory updated successfully")
            print_info(f"Previous quantity: {data['previous_qty']}")
            print_info(f"Current quantity: {data['current_qty']}")
            print_info(f"Change: -{update_data['out_qty']}")
            return data
        else:
            print_error(f"Inventory update failed with status {response.status_code}")
            print_json(response.json())
            return None
    except Exception as e:
        print_error(f"Inventory update test failed: {e}")
        return None


def test_inventory_update_missing_remark():
    """Test inventory update without required remark"""
    print_header("7. Inventory Update Test - Missing Remark (Should Fail)")
    
    try:
        update_data = {
            "blood_type": "A",
            "prep_id": 1,
            "in_qty": 5,
            "out_qty": 0,
            "remark": ""  # Empty remark should fail validation
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory/update",
            json=update_data
        )
        
        if response.status_code == 422:  # Validation error
            print_success("Empty remark correctly rejected")
            print_info("Validation error response:")
            print_json(response.json())
            return True
        else:
            print_error(f"Expected 422 validation error, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Missing remark test failed: {e}")
        return False


def run_all_tests():
    """Run all API tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          SCHBC BBMS API Test Suite                        ║")
    print("║          FastAPI Backend Verification                     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    
    print_info(f"Testing API at: {BASE_URL}")
    print_info(f"Test user: {TEST_USER['emp_id']}")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run tests
    results['health'] = test_health_check()
    results['login'] = test_login() is not None
    results['login_invalid'] = test_login_invalid()
    results['inventory_status'] = test_inventory_status() is not None
    results['inventory_update'] = test_inventory_update() is not None
    results['inventory_outgoing'] = test_inventory_update_with_outgoing() is not None
    results['missing_remark'] = test_inventory_update_missing_remark()
    
    # Print summary
    print_header("Test Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if passed else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"  {test_name.ljust(25)}: {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed_tests}/{total_tests} tests passed{Colors.RESET}")
    
    if passed_tests == total_tests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.RESET}\n")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.RESET}\n")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}\n")
        exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test suite failed with error: {e}{Colors.RESET}\n")
        exit(1)
