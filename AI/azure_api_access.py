from General.EncryptedTokens import get_azure_key
from General.EnvConfig import get_env_var
from openai import AzureOpenAI

def get_api_headers():
    """
    Get Azure OpenAI API configuration from environment variables.
    Falls back to encrypted tokens for API key if not in .env.
    """
    # Try to get API key from .env first, fall back to encrypted tokens
    api_key = get_env_var("AZURE_OPENAI_API_KEY")
    if not api_key:
        api_key = get_azure_key()
    
    return {
        "AZURE_OPENAI_ENDPOINT": get_env_var("AZURE_OPENAI_ENDPOINT"),
        "OPENAI_API_TYPE": "azure",
        "OPENAI_API_VERSION": get_env_var("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        "AZURE_OPENAI_API_KEY": api_key,
        "deployment names": [get_env_var("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"), "gpt-4-32k"]
    }

def get_chat_model():
    headers = get_api_headers()
    return AzureOpenAI( api_key =           headers["AZURE_OPENAI_API_KEY"],
                        azure_endpoint =    headers["AZURE_OPENAI_ENDPOINT"],
                        api_version  =      headers["OPENAI_API_VERSION"]  )


def cretae_completion(client, prompt):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )

if __name__ == "__main__":
    chat_model = get_chat_model()
    print(cretae_completion(chat_model, "I need to create a prompt that asks given information about archtiecture and threat, to build a code that suppose to check the countermeasure applied. what should I consider?"))
