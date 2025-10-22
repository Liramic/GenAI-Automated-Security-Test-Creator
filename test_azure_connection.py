import os
from openai import AzureOpenAI, APIConnectionError, AuthenticationError
from AI.azure_api_access import get_api_headers
from General.EnvConfig import load_env

# Ensure .env is loaded
load_env()

def test_azure_connection():
    """
    Tests the connection to the Azure OpenAI endpoint and validates credentials.
    """
    print("🚀 Starting Azure connection test...")
    
    try:
        # Get credentials from the existing function
        print("   - Fetching API headers...")
        headers = get_api_headers()
        
        api_key = headers.get("AZURE_OPENAI_API_KEY")
        endpoint = headers.get("AZURE_OPENAI_ENDPOINT")

        if not api_key or api_key == "CONFIG_PLACEHOLDER":
            print("❌ TEST FAILED: API Key is missing or is a placeholder.")
            return

        if not endpoint or endpoint == "your_endpoint":
            print("❌ TEST FAILED: API Endpoint is missing or is a placeholder.")
            return
            
        print(f"   - Endpoint: {endpoint}")
        print(f"   - API Key: ...{api_key[-4:]}") # Print last 4 chars for verification

        # 2. Initialize the AzureOpenAI client
        print("   - Initializing Azure OpenAI client...")
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=headers.get("OPENAI_API_VERSION"),
            timeout=10.0, # Add a timeout
        )

        # 3. Make a lightweight test API call
        print("   - Making a test API call to list models...")
        models = client.models.list()
        
        print("\n✅ SUCCESS: Connection to Azure OpenAI is valid.")
        print("   Available models found:")
        for model in models:
            print(f"     - {model.id}")

    except AuthenticationError as e:
        print("\n❌ TEST FAILED: Authentication Error.")
        print("   - The provided API Key is likely incorrect, expired, or lacks permissions.")
        print(f"   - Details: {e}")
        
    except APIConnectionError as e:
        print("\n❌ TEST FAILED: Connection Error.")
        print("   - Could not connect to the specified endpoint.")
        print("   - Please verify the Endpoint URL, and check for firewalls or network issues.")
        print(f"   - Details: {e}")

    except Exception as e:
        print(f"\n❌ TEST FAILED: An unexpected error occurred.")
        print(f"   - Details: {e}")

if __name__ == "__main__":
    test_azure_connection()
