#!/usr/bin/env python3
"""Performance testing script for wildcard domain exclusion feature."""

import time
import requests
import statistics
from typing import List, Dict, Any


# API Configuration
BASE_URL = "http://localhost:5001"
USERNAME = "admin"
PASSWORD = "LegoRocks"

# Test runs per scenario
TEST_RUNS = 10


def get_auth_token() -> str:
    """Get JWT token from API."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10
    )
    response.raise_for_status()
    return response.json()["access_token"]


def time_request(url: str, headers: dict, params: dict = None) -> tuple[float, dict]:
    """Time a single API request."""
    start = time.perf_counter()
    response = requests.get(url, headers=headers, params=params, timeout=30)
    elapsed = time.perf_counter() - start
    response.raise_for_status()
    return elapsed, response.json()


def run_test_scenario(
    endpoint: str,
    headers: dict,
    base_params: dict,
    exclude_patterns: List[str] = None,
    scenario_name: str = ""
) -> Dict[str, Any]:
    """Run a test scenario multiple times and collect statistics."""
    times = []

    for _ in range(TEST_RUNS):
        params = base_params.copy()
        if exclude_patterns:
            params["exclude"] = exclude_patterns

        elapsed, response_data = time_request(
            f"{BASE_URL}{endpoint}",
            headers,
            params
        )
        times.append(elapsed)

    return {
        "scenario": scenario_name,
        "endpoint": endpoint,
        "exclude_patterns": exclude_patterns,
        "runs": TEST_RUNS,
        "min_ms": round(min(times) * 1000, 2),
        "max_ms": round(max(times) * 1000, 2),
        "avg_ms": round(statistics.mean(times) * 1000, 2),
        "median_ms": round(statistics.median(times) * 1000, 2),
        "stdev_ms": round(statistics.stdev(times) * 1000, 2) if len(times) > 1 else 0,
    }


def print_results(results: List[Dict[str, Any]]):
    """Print performance test results in a formatted table."""
    print("\n" + "=" * 120)
    print("WILDCARD DOMAIN EXCLUSION - PERFORMANCE TEST RESULTS")
    print("=" * 120)
    print(f"{'Scenario':<40} {'Endpoint':<25} {'Min (ms)':<12} {'Avg (ms)':<12} {'Median (ms)':<12} {'Max (ms)':<12}")
    print("-" * 120)

    for result in results:
        print(
            f"{result['scenario']:<40} "
            f"{result['endpoint']:<25} "
            f"{result['min_ms']:<12} "
            f"{result['avg_ms']:<12} "
            f"{result['median_ms']:<12} "
            f"{result['max_ms']:<12}"
        )

    print("=" * 120)

    # Calculate overhead percentages
    print("\nPERFORMANCE IMPACT ANALYSIS")
    print("-" * 120)

    # Group by endpoint
    endpoints = {}
    for result in results:
        endpoint = result['endpoint']
        if endpoint not in endpoints:
            endpoints[endpoint] = []
        endpoints[endpoint].append(result)

    for endpoint, endpoint_results in endpoints.items():
        baseline = next((r for r in endpoint_results if r['exclude_patterns'] is None), None)
        if not baseline:
            continue

        print(f"\n{endpoint}:")
        print(f"  Baseline (no exclusion): {baseline['avg_ms']:.2f}ms")

        for result in endpoint_results:
            if result['exclude_patterns']:
                overhead = ((result['avg_ms'] - baseline['avg_ms']) / baseline['avg_ms']) * 100
                print(
                    f"  {result['scenario']}: {result['avg_ms']:.2f}ms "
                    f"({overhead:+.1f}% overhead)"
                )


def main():
    """Run all performance tests."""
    print("🧱 NextDNS Optimized Analytics - Wildcard Exclusion Performance Test")
    print("=" * 120)

    # Authenticate
    print("\n🔐 Authenticating...")
    try:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    # Check database size
    print("\n📊 Checking database size...")
    try:
        response = requests.get(f"{BASE_URL}/health/detailed", headers=headers, timeout=10)
        data = response.json()
        total = data.get('total_dns_records', data.get('total_records', 0))
        print(f"✅ Database contains {total:,} DNS log records")
    except Exception as e:
        print(f"⚠️  Could not get database size: {e}")

    results = []

    # Test 1: /logs endpoint - No exclusion (baseline)
    print("\n📈 Test 1/13: /logs - Baseline (no exclusion)")
    results.append(run_test_scenario(
        "/logs",
        headers,
        {"limit": 100, "time_range": "24h"},
        None,
        "Baseline - No exclusion"
    ))

    # Test 2: /logs endpoint - Single exact match
    print("📈 Test 2/13: /logs - Single exact match")
    results.append(run_test_scenario(
        "/logs",
        headers,
        {"limit": 100, "time_range": "24h"},
        ["google.com"],
        "Single exact match"
    ))

    # Test 3: /logs endpoint - Leading wildcard
    print("📈 Test 3/13: /logs - Leading wildcard")
    results.append(run_test_scenario(
        "/logs",
        headers,
        {"limit": 100, "time_range": "24h"},
        ["*.apple.com"],
        "Leading wildcard (*.apple.com)"
    ))

    # Test 4: /logs endpoint - Trailing wildcard
    print("📈 Test 4/13: /logs - Trailing wildcard")
    results.append(run_test_scenario(
        "/logs",
        headers,
        {"limit": 100, "time_range": "24h"},
        ["tracking.*"],
        "Trailing wildcard (tracking.*)"
    ))

    # Test 5: /logs endpoint - Middle wildcard
    print("📈 Test 5/13: /logs - Middle wildcard")
    results.append(run_test_scenario(
        "/logs",
        headers,
        {"limit": 100, "time_range": "24h"},
        ["*tracking*"],
        "Middle wildcard (*tracking*)"
    ))

    # Test 6: /logs endpoint - Multiple patterns (mixed)
    print("📈 Test 6/13: /logs - Multiple mixed patterns")
    results.append(run_test_scenario(
        "/logs",
        headers,
        {"limit": 100, "time_range": "24h"},
        ["google.com", "*.apple.com", "*tracking*", "facebook.*"],
        "Multiple mixed patterns (4)"
    ))

    # Test 7: /logs/stats endpoint - No exclusion
    print("📈 Test 7/13: /logs/stats - Baseline")
    results.append(run_test_scenario(
        "/logs/stats",
        headers,
        {"time_range": "24h"},
        None,
        "Baseline - No exclusion"
    ))

    # Test 8: /logs/stats endpoint - With wildcards
    print("📈 Test 8/13: /logs/stats - With wildcards")
    results.append(run_test_scenario(
        "/logs/stats",
        headers,
        {"time_range": "24h"},
        ["*.apple.com", "*tracking*"],
        "With wildcards"
    ))

    # Test 9: /stats/overview endpoint - No exclusion
    print("📈 Test 9/13: /stats/overview - Baseline")
    results.append(run_test_scenario(
        "/stats/overview",
        headers,
        {"time_range": "24h"},
        None,
        "Baseline - No exclusion"
    ))

    # Test 10: /stats/overview endpoint - With wildcards
    print("📈 Test 10/13: /stats/overview - With wildcards")
    results.append(run_test_scenario(
        "/stats/overview",
        headers,
        {"time_range": "24h"},
        ["*.apple.com", "*tracking*", "*.google.com"],
        "With wildcards (3 patterns)"
    ))

    # Test 11: /stats/domains endpoint - No exclusion
    print("📈 Test 11/13: /stats/domains - Baseline")
    results.append(run_test_scenario(
        "/stats/domains",
        headers,
        {"time_range": "24h", "limit": 10},
        None,
        "Baseline - No exclusion"
    ))

    # Test 12: /stats/domains endpoint - With wildcards
    print("📈 Test 12/13: /stats/domains - With wildcards")
    results.append(run_test_scenario(
        "/stats/domains",
        headers,
        {"time_range": "24h", "limit": 10},
        ["*.apple.com", "*ads*", "*tracking*"],
        "With wildcards (3 patterns)"
    ))

    # Test 13: /stats/tlds endpoint - With wildcards
    print("📈 Test 13/13: /stats/tlds - With wildcards")
    results.append(run_test_scenario(
        "/stats/tlds",
        headers,
        {"time_range": "24h", "limit": 10},
        ["*.icloud.com", "*analytics*"],
        "With wildcards (2 patterns)"
    ))

    # Print results
    print_results(results)

    print("\n✅ Performance testing complete!")
    print("\nKEY FINDINGS:")
    print("- Exact match exclusions use optimized NOT IN queries (minimal overhead)")
    print("- Wildcard patterns use ILIKE for flexibility (slightly higher overhead)")
    print("- Performance impact depends on dataset size and pattern complexity")
    print("- Leading wildcards (*.domain.com) are less index-friendly than trailing (domain.*)")


if __name__ == "__main__":
    main()
