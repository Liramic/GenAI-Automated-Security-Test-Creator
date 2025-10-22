"""
Claude API Access Module
Provides functions to interact with Anthropic's Claude API
"""

import requests
import json
import urllib3
from General.EnvConfig import get_env_var

# Disable SSL warnings for corporate proxy environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_api_config():
    """
    Returns Claude API configuration from environment variables.
    
    Returns:
        dict: Configuration dictionary with api_key, model, and endpoint
    """
    return {
        "api_key": get_env_var("CLAUDE_API_KEY"),
        "model": get_env_var("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
        "endpoint": get_env_var("CLAUDE_ENDPOINT", "https://api.anthropic.com/v1")
    }

def get_claude_client():
    """
    Returns a configured session for Claude API calls.
    
    Returns:
        dict: Client configuration dictionary
    """
    config = get_api_config()
    api_key = config["api_key"]
    
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")
    
    return config

def generate_content(prompt, temperature=0, max_tokens=2048, system_prompt=None):
    """
    Generate content using Claude API.
    
    Args:
        prompt (str): The user prompt
        temperature (float): Controls randomness (0-1)
        max_tokens (int): Maximum tokens to generate
        system_prompt (str): Optional system prompt
        
    Returns:
        dict: Response from Claude API
    """
    client = get_claude_client()
    
    endpoint = f"{client['endpoint']}/messages"
    
    payload = {
        "model": client['model'],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    # Add system prompt if provided
    if system_prompt:
        payload["system"] = system_prompt
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": client['api_key'],
        "anthropic-version": "2023-06-01"
    }
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30.0,
            verify=False  # Disable SSL verification for corporate proxy
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract the generated text
        if "content" in data and len(data["content"]) > 0:
            text = data["content"][0]["text"]
            return {
                "success": True,
                "text": text,
                "raw_response": data
            }
        else:
            return {
                "success": False,
                "error": "No content generated",
                "raw_response": data
            }
            
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if hasattr(e, 'response') else str(e)
        return {
            "success": False,
            "error": f"HTTP Error: {error_detail}"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def generate_structured_output(prompt, temperature=0, max_tokens=2048):
    """
    Generate JSON-formatted output using Claude.
    
    Args:
        prompt (str): The user prompt (should request JSON output)
        temperature (float): Controls randomness (0-1)
        max_tokens (int): Maximum tokens to generate
        
    Returns:
        dict: Response from Claude API
    """
    system_prompt = "You are a helpful assistant that always responds with valid JSON."
    return generate_content(prompt, temperature, max_tokens, system_prompt)

if __name__ == "__main__":
    # Test the connection
    print("Testing Claude API connection...")
    result = generate_content("Hello, this is a test. Respond with 'Connection successful!'")
    
    if result["success"]:
        print(f"✅ Success: {result['text']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
