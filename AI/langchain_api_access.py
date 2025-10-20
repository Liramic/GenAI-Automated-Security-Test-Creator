from langchain_openai.chat_models import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from AI.azure_api_access import get_api_headers
import time
import os
import subprocess
import re
import json
from pydantic import ValidationError

# Try to import Ollama support
try:
    from langchain_community.chat_models import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Check if we should use Ollama (no Azure config or explicit override)
# This will be set by the main script based on user's interactive choice
USE_OLLAMA = False

def set_ollama_preference(use_ollama):
    """Set whether to use Ollama or Azure. Called by main script."""
    global USE_OLLAMA
    USE_OLLAMA = use_ollama

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

def get_azure_chat_model():
    """
    Returns an AzureChatOpenAI instance.
    """
    headers = get_api_headers()
    return AzureChatOpenAI(
        azure_endpoint=headers["AZURE_OPENAI_ENDPOINT"],
        openai_api_version=headers["OPENAI_API_VERSION"],
        azure_deployment="gpt-4o",
        openai_api_key=headers["AZURE_OPENAI_API_KEY"],
        openai_api_type="azure",
    )

def get_ollama_model(model_name):
    """
    Returns a ChatOllama instance for the specified model.
    """
    if not OLLAMA_AVAILABLE:
        return None
    
    # This print statement is now the single source of truth for model instantiation
    print(f"ℹ️  Instantiating Ollama model: {model_name}")
    return ChatOllama(
        model=model_name,
        format="json",
        temperature=0,
    )

def get_chat_model(use_ollama=False, model_name="default"):
    """
    Returns a chat model instance, either from Azure OpenAI or Ollama.
    """
    if use_ollama:
        return get_ollama_model(model_name)
    else:
        return get_azure_chat_model()

def simple_message(prompt, isRetry = False):
    try:
        chat_model = get_chat_model(is_gpt4o = True)
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
    return simple_message(prompt, True)

def structered_output_message(model, structure, prompt, isRetry, model_name=""):
    """
    Invokes the chat model with a prompt and returns a structured output.
    Handles differences between Azure and Ollama models, with a retry and robust parsing.
    """
    # Handle Ollama models that don't support with_structured_output
    if isinstance(model, ChatOllama):
        # For Ollama, we need to be very explicit about generating DATA, not just the schema
        json_prompt = f"""{prompt}

You must respond with a valid JSON object that contains actual test plan data.
Do NOT just return the schema. Generate real test steps with meaningful content.

Your response must be ONLY valid JSON in this format (replace the placeholders with actual data):
{{
  "test_name": "Your generated test name here",
  "steps": [
    {{
      "step_number": 1,
      "instruction": "Actual instruction for step 1",
      "expected_result": "Actual expected result for step 1"
    }},
    {{
      "step_number": 2,
      "instruction": "Actual instruction for step 2",
      "expected_result": "Actual expected result for step 2"
    }}
  ]
}}
"""
        hm = HumanMessage(content=json_prompt)
        
        for attempt in range(2):
            try:
                response = model.invoke([hm])
                content = response.content

                # Find the start and end of the JSON object
                start = content.find('{')
                end = content.rfind('}') + 1
                
                if start == -1 or end == 0:
                    raise json.JSONDecodeError("No JSON object found in response", content, 0)

                json_str = content[start:end]
                result_json = json.loads(json_str)
                
                if 'steps' in result_json and isinstance(result_json['steps'], list):
                    for step in result_json['steps']:
                        if 'expected_result' in step and not isinstance(step['expected_result'], str):
                            step['expected_result'] = str(step['expected_result'])

                validated_data = structure(**result_json)
                return validated_data
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"⚠️  Attempt {attempt + 1} failed for {model_name}: {type(e).__name__}.")
                # Log the raw output for debugging
                print(f"   Raw model output on failure:\n---\n{response.content}\n---")
                if attempt == 1 and isRetry: # If it's the last attempt
                    return AI_ERROR(f"{type(e).__name__}_after_retry", e)
            except Exception as e:
                 if isRetry:
                    return AI_ERROR("error_raised", e)

    # Handle Azure and other models that support with_structured_output
    else:
        try:
            structured_llm = model.with_structured_output(structure)
            return structured_llm.invoke([HumanMessage(content=prompt)])
        except Exception as e:
            if isRetry:
                return AI_ERROR("error_raised", e)

    return AI_ERROR("unknown_error", "Model invocation failed without a specific error.")

if __name__ == "__main__":
    s = simple_message("please conduct a research regarding facial mimicry using emg sensor and how to create an artifact removal algorithm. provide sources.")
    print(s)
