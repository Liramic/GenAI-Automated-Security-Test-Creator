"""
Test script for Claude API connection
"""
from AI.claude_api_access import get_api_config, generate_content
import warnings

# Suppress SSL warnings when verification is disabled
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

def test_claude_connection():
    """Test the Claude API connection."""
    
    print("🚀 Starting Claude API connection test...")
    print("   - Fetching API configuration from .env file...")
    print("   ⚠️  SSL verification disabled for corporate proxy")
    
    try:
        # Get configuration
        config = get_api_config()
        
        print(f"   - API Key: ...{config['api_key'][-4:]}")
        print(f"   - Model: {config['model']}")
        print(f"   - Endpoint: {config['endpoint']}")
        print("   - Making a test API call...")
        
        # Test 1: Simple message
        result = generate_content(
            prompt="Say 'Connection successful!' if you can read this.",
            temperature=0,
            max_tokens=100
        )
        
        if result["success"]:
            print("\n✅ TEST PASSED: Claude API is working!")
            print(f"   Model: {config['model']}")
            print(f"   Response: {result['text']}")
            
            # Test 2: Cybersecurity-related prompt
            print("\n🔒 Testing cybersecurity prompt...")
            result2 = generate_content(
                prompt="List 3 common cloud security threats in one sentence each.",
                temperature=0,
                max_tokens=300
            )
            
            if result2["success"]:
                print(f"   Response:\n{result2['text']}")
                return True
            else:
                print(f"   ⚠️  Second test failed: {result2['error']}")
                return False
        else:
            print(f"\n❌ TEST FAILED: {result['error']}")
            print("\n📋 Troubleshooting steps:")
            print("1. Verify CLAUDE_API_KEY is set in .env file")
            print("2. Check you have credits: https://console.anthropic.com/settings/billing")
            print("3. Verify API key at: https://console.anthropic.com/settings/keys")
            print("4. If SSL errors persist, contact IT about corporate proxy certificate")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\n📋 Troubleshooting steps:")
        print("1. Verify CLAUDE_API_KEY is set in .env file")
        print("2. Check you have credits: https://console.anthropic.com/settings/billing")
        print("3. Verify API key at: https://console.anthropic.com/settings/keys")
        if "SSL" in str(e):
            print("4. SSL verification has been disabled for corporate proxy")
            print("   If this doesn't work, contact IT for the corporate CA certificate")
        return False

if __name__ == "__main__":
    import sys
    success = test_claude_connection()
    sys.exit(0 if success else 1)