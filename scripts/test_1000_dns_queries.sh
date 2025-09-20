#!/bin/bash

# NextDNS Analytics Test Script
# Downloads top 1000 domains and generates DNS queries to test log collection
# Run this script to generate traffic that NextDNS will log and your analytics will capture

echo "🧪 NextDNS Analytics Test - Generating DNS queries from Top 1000 domains..."
echo "📅 Started at: $(date)"
echo ""

# URL to the top 1000 domains list
DOMAINS_URL="https://gist.githubusercontent.com/jgamblin/62fadd8aa321f7f6a482912a6a317ea3/raw/urls.txt"
DOMAINS_FILE="/tmp/top1000_domains.txt"

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up temporary files..."
    rm -f "$DOMAINS_FILE"
    echo "✅ Cleanup completed"
}

# Ensure cleanup runs on exit (success, failure, or interruption)
trap cleanup EXIT

# Download the domains list
echo "📥 Downloading top 1000 domains list..."
if command -v curl >/dev/null 2>&1; then
    curl -s "$DOMAINS_URL" -o "$DOMAINS_FILE"
else
    echo "❌ curl not found. Please install curl or manually download the domains list."
    exit 1
fi

# Check if download was successful
if [ ! -f "$DOMAINS_FILE" ] || [ ! -s "$DOMAINS_FILE" ]; then
    echo "❌ Failed to download domains list. Please check your internet connection."
    exit 1
fi

# Read domains into array and filter out empty lines (macOS compatible)
domains=()
while IFS= read -r line; do
    if [ -n "$line" ]; then
        domains+=("$line")
    fi
done < <(grep -v '^$' "$DOMAINS_FILE" | head -n 1000)
domain_count=${#domains[@]}

if [ $domain_count -eq 0 ]; then
    echo "❌ No domains found in the downloaded file."
    exit 1
fi

echo "✅ Successfully downloaded $domain_count domains"

# Counters
total_queries=0
successful_queries=0
failed_queries=0
start_time=$(date +%s)

echo "🔍 Starting DNS queries to $domain_count unique domains..."
echo "📊 This will generate logs that NextDNS will capture and your analytics will process"
echo ""

# Loop through domains and make DNS queries
for i in "${!domains[@]}"; do
    domain="${domains[$i]}"
    query_num=$((i + 1))
    
    # Use dig to make DNS query (more reliable than nslookup on macOS)
    if command -v dig >/dev/null 2>&1; then
        result=$(dig +short +time=3 +tries=1 "$domain" A 2>/dev/null)
        if [ $? -eq 0 ] && [ -n "$result" ]; then
            echo "✅ Query $query_num/$domain_count: $domain → $result"
            ((successful_queries++))
        else
            echo "❌ Query $query_num/$domain_count: $domain → Failed"
            ((failed_queries++))
        fi
    else
        # Fallback to nslookup if dig is not available
        result=$(nslookup "$domain" 2>/dev/null | grep -A1 "Name:" | tail -n1 | awk '{print $2}')
        if [ $? -eq 0 ] && [ -n "$result" ]; then
            echo "✅ Query $query_num/$domain_count: $domain → $result"
            ((successful_queries++))
        else
            echo "❌ Query $query_num/$domain_count: $domain → Failed"
            ((failed_queries++))
        fi
    fi
    
    ((total_queries++))
    
    # Small delay to avoid overwhelming DNS servers (0.1 second)
    sleep 0.1
    
    # Progress indicator every 100 queries (or every 50 if less than 200 domains)
    progress_interval=$((domain_count > 200 ? 100 : 50))
    if [ $((query_num % progress_interval)) -eq 0 ]; then
        echo ""
        echo "📊 Progress: $query_num/$domain_count queries completed ($successful_queries successful, $failed_queries failed)"
        echo ""
    fi
done

# Calculate statistics
end_time=$(date +%s)
total_time=$((end_time - start_time))
success_rate=$((successful_queries * 100 / total_queries))

echo ""
echo "🏁 DNS Query Test Completed!"
echo "================================="
echo "📅 Finished at: $(date)"
echo "⏱️  Total time: ${total_time} seconds"
echo "📊 Total queries: $total_queries"
echo "✅ Successful: $successful_queries"
echo "❌ Failed: $failed_queries"
echo "📈 Success rate: $success_rate%"
echo ""
echo "🔮 Expected Results:"
echo "• Your NextDNS dashboard should show $successful_queries new queries"
echo "• Your analytics backend should capture these logs within 1-2 minutes"
echo "• Check your analytics at: http://192.168.2.64:3000"
echo "• Check backend API at: http://192.168.2.64:5001/health"
echo ""
echo "💡 Tip: Wait 2-3 minutes for NextDNS to process the logs, then check your analytics dashboard!"
