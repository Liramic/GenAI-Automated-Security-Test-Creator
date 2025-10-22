"""
Google Gemini API Access Module
Provides functions to interact with Google's Gemini API
"""
import requests
from General.EnvConfig import get_env_var

def get_api_config():
    """
    Returns Gemini API configuration from environment variables.
    """
    return {
        "GEMINI_API_KEY": get_env_var("GEMINI_API_KEY"),
        "GEMINI_MODEL": get_env_var("GEMINI_MODEL", "gemini-2.5-flash"),
        "GEMINI_ENDPOINT": get_env_var("GEMINI_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta")
    }

def get_gemini_client():
    """
    Returns a configured session for Gemini API calls.
    """
    config = get_api_config()
    api_key = config["GEMINI_API_KEY"]
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    return {
        "api_key": api_key,
        "model": config["GEMINI_MODEL"],
        "endpoint": config["GEMINI_ENDPOINT"]
    }

def generate_content(prompt, temperature=0, max_tokens=2048):
    """
    Generate content using Gemini API.
    
    Args:
        prompt (str): The input prompt
        temperature (float): Controls randomness (0-1)
        max_tokens (int): Maximum tokens to generate
        
    Returns:
        dict: Response from Gemini API
    """
    client = get_gemini_client()
    
    endpoint = f"{client['endpoint']}/models/{client['model']}:generateContent?key={client['api_key']}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30.0
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract the generated text
        if "candidates" in data and len(data["candidates"]) > 0:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
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
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def list_models():
    """
    List all available Gemini models.
    
    Returns:
        list: List of available models
    """
    client = get_gemini_client()
    endpoint = f"{client['endpoint']}/models?key={client['api_key']}"
    
    try:
        response = requests.get(endpoint, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        return data.get('models', [])
    except requests.exceptions.RequestException as e:
        return []

if __name__ == "__main__":
    # Test the connection
    print("Testing Gemini API connection...")
    result = generate_content("Hello, this is a test. Respond with 'Connection successful!'")
    
    if result["success"]:
        print(f"✅ Success: {result['text']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
