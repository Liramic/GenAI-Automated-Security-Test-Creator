from langchain_openai.chat_models import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from AI.azure_api_access import get_api_headers
import time
import os
import subprocess
import re

# Try to import Ollama support
try:
    from langchain_community.chat_models import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Check if we should use Ollama (no Azure config or explicit override)
USE_OLLAMA = os.environ.get("USE_OLLAMA", "false").lower() in ("true", "1", "yes")

def get_available_ollama_models():
    """Get list of locally installed Ollama models."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        models = []
        for line in lines:
            if line.strip():
                # Extract model name (first column)
                match = re.match(r'([^\s]+)', line)
                if match:
                    models.append(match.group(1))
        return models
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

class AI_ERROR:
    def __init__(self, error, e = None):
        self.error = error
        self.exception = e
    
    def __str__(self):
        return f"error: {self.error}, exception: {self.exception}"

def get_ollama_model(model_name=None):
    """Fallback to local Ollama model when Azure is not configured."""
    if not OLLAMA_AVAILABLE:
        raise ImportError("langchain_community not installed. Run: pip install langchain-community")
    
    # Get available models
    available_models = get_available_ollama_models()
    
    if not available_models:
        raise RuntimeError(
            "No Ollama models found. Install one with:\n"
            "  ollama pull llama3.1\n"
            "Or list available models: ollama list"
        )
    
    # Use first available model if none specified
    if model_name is None:
        model_name = available_models[0]
        print(f"ℹ️  Using Ollama model: {model_name}")
    elif model_name not in available_models:
        raise ValueError(
            f"Model '{model_name}' not found. Available models:\n" +
            "\n".join(f"  - {m}" for m in available_models)
        )
    
    return ChatOllama(
        model=model_name,
        temperature=0.7,
    )

def get_chat_model(is_gpt4o = False, fallback_to_ollama=True):
    """Get chat model, with optional Ollama fallback if Azure not configured."""
    try:
        headers = get_api_headers()
        
        # Check if Azure is properly configured
        if (headers.get("AZURE_OPENAI_API_KEY") in (None, "CONFIG_PLACEHOLDER", "CONFIG_DECRYPT_ERROR") or
            USE_OLLAMA):
            if fallback_to_ollama and OLLAMA_AVAILABLE:
                print("⚠️  Azure API not configured, falling back to local Ollama model")
                return get_ollama_model()
            else:
                raise ValueError("Azure API credentials not configured and Ollama not available")
        
        deployment = headers["deployment names"][0] if is_gpt4o else headers["deployment names"][1]
        
        return AzureChatOpenAI(
            api_key=headers["AZURE_OPENAI_API_KEY"],
            azure_endpoint=headers["AZURE_OPENAI_ENDPOINT"],
            api_version=headers["OPENAI_API_VERSION"],
            azure_deployment=deployment
        )
    except Exception as e:
        if fallback_to_ollama and OLLAMA_AVAILABLE:
            print(f"⚠️  Azure API error ({e}), falling back to local Ollama model")
            return get_ollama_model()
        raise


def simple_message(prompt, isRetry = False, use_ollama_fallback=True):
    try:
        chat_model = get_chat_model(is_gpt4o = True, fallback_to_ollama=use_ollama_fallback)
    except Exception as e:
        return AI_ERROR("model_initialization_failed", e)
    
    hm = HumanMessage(content = prompt)
    try:
        response = chat_model([hm])
        if response.content is not None and len(response.content) > 0:
            return response.content
        elif isRetry:
            return AI_ERROR("empty_response")
    except Exception as e:
        if isRetry:
            return AI_ERROR("error_raised", e)
    
    #retry with maximum waiting time between requests.
    time.sleep(60)
    return simple_message(prompt, True, use_ollama_fallback)

def structered_output_message(prompt, structure, isRetry = False, use_ollama_fallback=True):
    try:
        model = get_chat_model(is_gpt4o = True, fallback_to_ollama=use_ollama_fallback)
    except Exception as e:
        return AI_ERROR("model_initialization_failed", e)
    
    model_with_structure = model.with_structured_output(structure)
    hm = HumanMessage(content = prompt)
    try:
        response = model_with_structure.invoke(prompt)
        if response is not None:
            return response
        elif isRetry:
            return AI_ERROR("empty_response")
    except Exception as e:
        if isRetry:
            return AI_ERROR("error_raised", e)
    
    #retry once, wait 60:
    time.sleep(60)
    return structered_output_message(prompt, structure, True, use_ollama_fallback)

if __name__ == "__main__":
    s = simple_message("please conduct a research regarding facial mimicry using emg sensor and how to create an artifact removal algorithm. provide sources.")
    print(s)
