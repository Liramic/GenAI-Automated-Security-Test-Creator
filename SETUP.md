# Setup Guide for GenAI Security Test Creator

## Overview
This project now supports **two AI backend options**:
1. **Azure OpenAI** (requires API credentials)
2. **Local Ollama** (free, runs on your machine)

---

## Quick Start

### Option 1: Using Local Ollama (Recommended for Testing)

1. **Install Ollama** (if not already installed):
   ```bash
   # macOS
   brew install ollama
   
   # Or download from: https://ollama.ai
   ```

2. **Start Ollama service**:
   ```bash
   ollama serve
   ```

3. **Run the script** - it will automatically fallback to Ollama:
   ```bash
   python exploring_prompts.py
   ```
   
   The first run will download the llama3.1 model (~4.9 GB). Subsequent runs will be fast.

### Option 2: Using Azure OpenAI

#### Method A: Using Environment Variables

1. **Set environment variables**:
   ```bash
   export PYTHON_SECRET='your-secret-passphrase'
   export PYTHON_NONCE='your-nonce-value'
   ```

2. **Encrypt your tokens** (one-time setup):
   ```python
   from General.EncryptedTokens import encrypt_to_b64
   
   # Encrypt your Azure API key
   encrypted_key = encrypt_to_b64("your-azure-api-key")
   print(encrypted_key)
   
   # Update the encrypted tokens in General/EncryptedTokens.py
   ```

3. **Update `AI/azure_api_access.py`** with your Azure endpoint and deployment names.

#### Method B: Using In-Code Overrides

```python
from General.EncryptedTokens import set_overrides

# Set credentials programmatically (not recommended for production)
set_overrides(
    secret="your-secret-passphrase",
    nonce="your-nonce-value"
)

# Now run your code
```

---

## Configuration Options

### Force Ollama Usage
Even if Azure credentials are configured, you can force Ollama:
```bash
export USE_OLLAMA=true
python exploring_prompts.py
```

### Change Ollama Model
Edit `AI/langchain_api_access.py`:
```python
def get_ollama_model(model_name="llama3.1"):  # Change model here
```

Available models: `llama3.1`, `llama3`, `mistral`, `codellama`, etc.
See: https://ollama.ai/library

---

## Installation

### Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Key Dependencies
- `langchain` - LLM framework
- `langchain-openai` - Azure OpenAI integration
- `langchain-community` - Ollama integration
- `pycryptodome` - Token encryption
- `pydantic` - Data validation

---

## How It Works

1. **Automatic Fallback**: When you run the script, it checks for Azure credentials
2. **If Azure is configured**: Uses Azure OpenAI (GPT-4o)
3. **If Azure is NOT configured**: Automatically falls back to local Ollama
4. **Error Handling**: If API errors occur, the script provides clear error messages

---

## Troubleshooting

### "Azure API not configured, falling back to local Ollama model"
✅ This is normal! The script is using your local Ollama installation.

### "langchain_community not installed"
```bash
pip install langchain-community
```

### "Connection refused" (Ollama)
Make sure Ollama is running:
```bash
ollama serve
```

### Slow first run with Ollama
The first run downloads the model (~4.9 GB). Subsequent runs are fast.

### Import error with pydantic
We've updated to use `from pydantic import BaseModel` (no longer using deprecated `langchain_core.pydantic_v1`).

---

## Security Notes

- **Never commit** unencrypted API keys to version control
- **Use environment variables** for sensitive data in production
- **In-code overrides** are only for development/testing
- The `EncryptedTokens.py` module uses AES-GCM encryption for token storage

---

## Examples

### Run with Azure (if configured)
```bash
export PYTHON_SECRET='my-secret'
export PYTHON_NONCE='my-nonce'
python exploring_prompts.py
```

### Run with Ollama
```bash
# Just run it - will auto-detect and use Ollama
python exploring_prompts.py
```

### Run specific test files
```python
from Main.main_integration import run_job_on_specific_product
from General.JobClasses import JobType

run_job_on_specific_product("product_1", JobType.CREATE_TEST)
```

---

## Support

For issues or questions:
1. Check the logs in `Logs/` directory
2. Verify Ollama is running: `ollama list`
3. Test encryption: `python -m General.EncryptedTokens`

Enjoy using GenAI Security Test Creator! 🚀
