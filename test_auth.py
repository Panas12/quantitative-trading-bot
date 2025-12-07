"""
Quick test script to verify Capital.com authentication with better debugging
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Get credentials
api_key = os.getenv('CAPITAL_API_KEY')
api_password = os.getenv('CAPITAL_API_PASSWORD')
email = os.getenv('CAPITAL_EMAIL')
environment = os.getenv('CAPITAL_ENVIRONMENT', 'LIVE')

print("=== Capital.com Authentication Test ===\n")
print(f"Environment: {environment}")
print(f"Email: {email}")
print(f"API Key (first 10 chars): {api_key[:10] if api_key else 'NOT SET'}...")
print(f"Password set: {'Yes' if api_password else 'No'}\n")

# Select base URL
if environment.upper() == 'DEMO':
    base_url = 'https://demo-api-capital.backend-capital.com'
else:
    base_url = 'https://api-capital.backend-capital.com'

print(f"Using URL: {base_url}/api/v1/session\n")

# Authentication payload
auth_data = {
    'identifier': email,
    'password': api_password,
    'encryptedPassword': False
}

headers = {
    'Content-Type': 'application/json',
    'X-CAP-API-KEY': api_key
}

print("Attempting authentication...")
print(f"Payload: identifier={email}, encryptedPassword=False\n")

try:
    response = requests.post(
        f"{base_url}/api/v1/session",
        json=auth_data,
        headers=headers,
        timeout=30
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}\n")
    
    if response.status_code == 200:
        print("✓ SUCCESS! Authentication worked!")
        data = response.json() 
        print(f"\nAccount ID: {data.get('currentAccountId')}")
        print(f"Account Type: {data.get('accountType')}")
        print(f"Currency: {data.get('currencyIsoCode')}")
        
        # Extract tokens
        cst = response.headers.get('CST')
        x_security = response.headers.get('X-SECURITY-TOKEN')
        print(f"\nTokens received:")
        print(f"CST: {cst[:20] if cst else 'NOT FOUND'}...")
        print(f"X-SECURITY-TOKEN: {x_security[:20] if x_security else 'NOT FOUND'}...")
        
    else:
        print(f"✗ FAILED!")
        print(f"Error: {response.text}")
        
        # Common issues
        print("\n=== Troubleshooting ===")
        error_data = response.json() if response.text else {}
        error_code = error_data.get('errorCode', '')
        
        if 'invalid.api.key' in error_code:
            print("• API key is not valid or not active")
            print("• Check that the API key was copied correctly")
            print("• Verify the key is activated in Capital.com settings")
            print(f"• Current environment is {environment} - make sure key matches")
        elif 'invalid.details' in error_code:
            print("• Email or password is incorrect")
            print("• Verify credentials in .env file")
        
except Exception as e:
    print(f"✗ Request failed: {e}")

print("\n" + "="*50)
