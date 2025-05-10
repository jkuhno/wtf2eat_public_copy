#!/bin/bash

# Get variables from env configuration file
set -o allexport
source "$(dirname "$0")/../.env"
set +o allexport

DNS_RECORD_NAME="wtf2eat.com"
DNS_RECORD_TYPE="A"

# Define the full paths to commands to be able run this script with cron
CURL="/usr/bin/curl"
JQ="/usr/bin/jq"

# Get the current public IP address
IP=$($CURL -s http://ipv4.icanhazip.com)

# Cloudflare API endpoint to get the current DNS record
GET_API_ENDPOINT="https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$CF_DNS_RECORD_ID"

# Get the current DNS record's IP address from Cloudflare
current_ip=$($CURL -s -X GET "$GET_API_ENDPOINT" \
     -H "Authorization: Bearer $CF_API_KEY" \
     -H "Content-Type: application/json" | $JQ -r '.result.content')

# Check if the IP addresses are different
if [[ "$IP" == "$current_ip" ]]; then
  echo "$(date): No update needed. IP address has not changed: $IP"
else
  echo "$(date): IP address has changed from $current_ip to $IP. Updating record..."

  # Cloudflare API endpoint to update the DNS record
  UPDATE_API_ENDPOINT="https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$CF_DNS_RECORD_ID"

  # Update the DNS record
  response=$($CURL -s -X PUT "$UPDATE_API_ENDPOINT" \
       -H "Authorization: Bearer $CF_API_KEY" \
       -H "Content-Type: application/json" \
       --data '{
         "type": "'"$DNS_RECORD_TYPE"'",
         "name": "'"$DNS_RECORD_NAME"'",
         "content": "'"$IP"'",
         "ttl": 120,
         "proxied": true
       }')

  # Check if the update was successful
  if [[ $response == *"\"success\":true"* ]]; then
    echo "$(date): DNS record updated successfully to IP: $IP"
  else
    echo "$(date): Failed to update DNS record. Response: $response"
  fi
fi