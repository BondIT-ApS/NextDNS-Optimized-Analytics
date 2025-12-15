#!/bin/bash
# Rate Limiting Test Script for NextDNS Optimized Analytics API
# Tests rate limiting on health endpoint and login endpoint

# Configuration
BASE_URL="http://localhost:5001"
HEALTH_ENDPOINT="$BASE_URL/health"
LOGIN_ENDPOINT="$BASE_URL/auth/login"

# Credentials (update these based on your .env configuration)
CORRECT_USERNAME="admin"
CORRECT_PASSWORD="LegoRocks"
WRONG_USERNAME="hacker"
WRONG_PASSWORD="wrongpass"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BOLD}${CYAN}======================================================================${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}======================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test 1: Health Endpoint Flood Test
test_health_endpoint_flood() {
    print_header "TEST 1: Health Endpoint Flood Test (10s)"
    print_info "Target: $HEALTH_ENDPOINT"
    print_info "Goal: Send as many requests as possible"
    echo ""
    
    local count=0
    local success=0
    local rate_limited=0
    local end_time=$((SECONDS + 10))
    
    echo "🚀 Flooding health endpoint..."
    
    while [ $SECONDS -lt $end_time ]; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT" 2>/dev/null)
        ((count++))
        
        if [ "$response" = "200" ]; then
            ((success++))
        elif [ "$response" = "429" ]; then
            ((rate_limited++))
        fi
        
        if [ $((count % 100)) -eq 0 ]; then
            echo "  📊 $count requests sent..."
        fi
    done
    
    echo -e "\n${BOLD}📈 Results:${NC}"
    echo "  Total requests: $count"
    echo "  Successful (200): $success"
    echo "  Rate limited (429): $rate_limited"
    
    if [ $rate_limited -gt 0 ]; then
        print_warning "Health endpoint has rate limiting: $rate_limited requests blocked"
    else
        print_success "Health endpoint has no rate limiting (as expected)"
    fi
}

# Test 2: Login with Wrong Credentials
test_login_wrong_credentials() {
    print_header "TEST 2: Login Rate Limiting - Wrong Credentials"
    print_info "Target: $LOGIN_ENDPOINT"
    print_info "Rate limit: 5 requests per minute"
    print_info "Credentials: $WRONG_USERNAME/$WRONG_PASSWORD (incorrect)"
    print_info "Attempts: 10"
    echo ""
    
    local attempts=10
    local auth_failures=0
    local rate_limited=0
    local first_rate_limit=0
    
    echo "🔐 Attempting logins with wrong credentials..."
    
    for i in $(seq 1 $attempts); do
        response=$(curl -s -w "\n%{http_code}" -X POST "$LOGIN_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d "{\"username\":\"$WRONG_USERNAME\",\"password\":\"$WRONG_PASSWORD\"}" \
            2>/dev/null)
        
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n-1)
        
        if [ "$status_code" = "429" ]; then
            print_warning "Attempt $i: Rate limited (429)"
            echo "    Response: $body"
            ((rate_limited++))
            if [ $first_rate_limit -eq 0 ]; then
                first_rate_limit=$i
            fi
        elif [ "$status_code" = "401" ]; then
            print_info "Attempt $i: Authentication failed (401) - Expected"
            ((auth_failures++))
        else
            print_error "Attempt $i: Unexpected status $status_code"
        fi
        
        sleep 0.5
    done
    
    echo -e "\n${BOLD}📈 Results:${NC}"
    echo "  Total attempts: $attempts"
    echo "  Authentication failures (401): $auth_failures"
    echo "  Rate limited (429): $rate_limited"
    
    if [ $rate_limited -gt 0 ]; then
        print_success "Rate limiting activated after $first_rate_limit attempts"
    else
        print_error "Rate limiting NOT working - all requests went through!"
    fi
}

# Test 3: Login with Correct Credentials
test_login_correct_credentials() {
    print_header "TEST 3: Login Rate Limiting - Correct Credentials"
    print_info "Target: $LOGIN_ENDPOINT"
    print_info "Rate limit: 5 requests per minute"
    print_info "Credentials: $CORRECT_USERNAME/$CORRECT_PASSWORD (correct)"
    print_info "Attempts: 10"
    echo ""
    
    local attempts=10
    local successful_logins=0
    local rate_limited=0
    local first_rate_limit=0
    
    echo "🔐 Attempting logins with correct credentials..."
    
    for i in $(seq 1 $attempts); do
        response=$(curl -s -w "\n%{http_code}" -X POST "$LOGIN_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d "{\"username\":\"$CORRECT_USERNAME\",\"password\":\"$CORRECT_PASSWORD\"}" \
            2>/dev/null)
        
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n-1)
        
        if [ "$status_code" = "429" ]; then
            print_warning "Attempt $i: Rate limited (429)"
            echo "    Response: $body"
            ((rate_limited++))
            if [ $first_rate_limit -eq 0 ]; then
                first_rate_limit=$i
            fi
        elif [ "$status_code" = "200" ]; then
            print_success "Attempt $i: Login successful (200) - Token received"
            ((successful_logins++))
        else
            print_error "Attempt $i: Unexpected status $status_code"
        fi
        
        sleep 0.5
    done
    
    echo -e "\n${BOLD}📈 Results:${NC}"
    echo "  Total attempts: $attempts"
    echo "  Successful logins (200): $successful_logins"
    echo "  Rate limited (429): $rate_limited"
    
    if [ $rate_limited -gt 0 ]; then
        print_success "Rate limiting activated after $first_rate_limit attempts"
        print_info "Rate limiting works correctly even with valid credentials"
    else
        print_error "Rate limiting NOT working - all requests went through!"
    fi
}

# Test 4: Rate Limit Recovery
test_rate_limit_recovery() {
    print_header "TEST 4: Rate Limit Recovery Test"
    print_info "Testing that rate limits reset after 60 seconds"
    print_info "Target: $LOGIN_ENDPOINT"
    echo ""
    
    echo "🔐 Phase 1: Trigger rate limit..."
    
    for i in $(seq 1 7); do
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LOGIN_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d "{\"username\":\"$WRONG_USERNAME\",\"password\":\"$WRONG_PASSWORD\"}" \
            2>/dev/null)
        echo "  Attempt $i: $response"
        sleep 0.3
    done
    
    print_warning "\n⏳ Waiting 61 seconds for rate limit to reset..."
    for i in $(seq 61 -5 1); do
        echo -ne "  ${i}s remaining...\r"
        sleep 5
    done
    echo ""
    
    echo -e "\n🔐 Phase 2: Test after cooldown..."
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$LOGIN_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$WRONG_USERNAME\",\"password\":\"$WRONG_PASSWORD\"}" \
        2>/dev/null)
    
    if [ "$response" = "401" ]; then
        print_success "Rate limit recovered! Got expected 401 (not 429)"
    elif [ "$response" = "429" ]; then
        print_error "Rate limit NOT recovered - still getting 429"
    else
        print_warning "Unexpected status code: $response"
    fi
}

# Main execution
main() {
    echo -e "\n${BOLD}${CYAN}"
    echo "🧪 NextDNS Analytics - Rate Limiting Test Suite"
    echo "======================================================================"
    echo -e "${NC}"
    
    print_info "Base URL: $BASE_URL"
    print_info "Test started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Check backend connectivity
    echo "🔍 Checking backend connectivity..."
    if curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT" | grep -q "200"; then
        print_success "Backend is reachable"
    else
        print_error "Cannot reach backend at $BASE_URL"
        print_error "Please ensure the backend is running on http://localhost:5001"
        exit 1
    fi
    echo ""
    
    # Run tests
    test_health_endpoint_flood
    sleep 2
    
    test_login_wrong_credentials
    sleep 2
    
    test_login_correct_credentials
    
    # Optional recovery test
    echo -e "\n${BOLD}Optional Test:${NC}"
    read -p "Run rate limit recovery test? (takes 61 seconds) [y/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_rate_limit_recovery
    fi
    
    print_header "🎉 All Tests Complete!"
    print_info "Test completed: $(date '+%Y-%m-%d %H:%M:%S')"
}

main
