import os
import requests
from General.EnvConfig import get_env_var

def test_gemini_connection():
    """
    Tests the connection to the Google Gemini Pro API and validates credentials.
    """
    print("🚀 Starting Gemini Pro connection test...")
    
    try:
        # 1. Get API key from .env file
        print("   - Fetching API key from .env file...")
        api_key = get_env_var("GEMINI_API_KEY")
        
        if not api_key:
            print("❌ TEST FAILED: GEMINI_API_KEY-PERSONAL environment variable is not set.")
            print("   Set it with: export GEMINI_API_KEY-PERSONAL='your-api-key-here'")
            return
            
        print(f"   - API Key: ...{api_key[-4:]}") # Print last 4 chars for verification

        # 2. Prepare the API endpoint (using gemini-2.5-flash which is the latest stable version)
        model_name = "gemini-2.5-flash"
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        print(f"   - Endpoint: https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent")
        print(f"   - Model: Gemini 2.5 Flash")

        # 3. Make a lightweight test API call
        print("   - Making a test API call...")
        
        test_payload = {
            "contents": [{
                "parts": [{
                    "text": "Hello, this is a test. Please respond with 'Connection successful!'"
                }]
            }]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            endpoint,
            json=test_payload,
            headers=headers,
            timeout=10.0
        )
        
        # 4. Check response
        if response.status_code == 200:
            response_data = response.json()
            
            # Extract the text from the response
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                text_response = response_data["candidates"][0]["content"]["parts"][0]["text"]
                
                print("\n✅ SUCCESS: Connection to Gemini Pro API is valid.")
                print(f"   API Response: {text_response}")
                
                # Test with a more complex prompt
                print("\n   - Testing with a cybersecurity prompt...")
                security_payload = {
                    "contents": [{
                        "parts": [{
                            "text": "List 3 common cloud security threats in one sentence each."
                        }]
                    }]
                }
                
                security_response = requests.post(
                    endpoint,
                    json=security_payload,
                    headers=headers,
                    timeout=15.0
                )
                
                if security_response.status_code == 200:
                    security_data = security_response.json()
                    security_text = security_data["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"   Security Test Response:\n{security_text}")
                    print("\n✅ All tests passed! Gemini Pro API is ready to use.")
                else:
                    print(f"   ⚠️  Security test returned status code: {security_response.status_code}")
            else:
                print("\n⚠️  Unexpected response format from Gemini API.")
                print(f"   Response: {response_data}")
                
        elif response.status_code == 400:
            print("\n❌ TEST FAILED: Bad Request (400)")
            print("   - The API request format may be incorrect.")
            print(f"   - Details: {response.text}")
            
        elif response.status_code == 403:
            print("\n❌ TEST FAILED: Authentication Error (403)")
            print("   - The provided API Key is likely incorrect or lacks permissions.")
            print("   - Verify your API key at: https://makersuite.google.com/app/apikey")
            print(f"   - Details: {response.text}")
            
        elif response.status_code == 404:
            print("\n❌ TEST FAILED: Not Found (404)")
            print("   - The API endpoint or model name may be incorrect.")
            print(f"   - Details: {response.text}")
            
        else:
            print(f"\n❌ TEST FAILED: Unexpected status code {response.status_code}")
            print(f"   - Details: {response.text}")

    except requests.exceptions.ConnectionError as e:
        print("\n❌ TEST FAILED: Connection Error.")
        print("   - Could not connect to the Gemini API.")
        print("   - Please check your internet connection and firewall settings.")
        print(f"   - Details: {e}")

    except requests.exceptions.Timeout as e:
        print("\n❌ TEST FAILED: Timeout Error.")
        print("   - The request to Gemini API timed out.")
        print(f"   - Details: {e}")

    except Exception as e:
        print(f"\n❌ TEST FAILED: An unexpected error occurred.")
        print(f"   - Details: {e}")

if __name__ == "__main__":
    test_gemini_connection()
