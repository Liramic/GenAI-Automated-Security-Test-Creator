"""
Helper module for managing user configuration preferences.
"""
import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.user_config.json')

def load_config():
    """Load user configuration from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_config(config):
    """Save user configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print(f"Warning: Could not save config: {e}")
        return False

def get_model_selection(available_ollama_models):
    """
    Interactively ask the user to select a model (Azure, Gemini, Claude, or Ollama).
    If Ollama is chosen, ask for a specific model or all.
    """
    config = load_config()

    # Main choice: Cloud LLMs vs. Ollama
    if 'mode' in config:
        mode = config['mode']
        print(f"ℹ️  Using saved mode: {mode.upper()}")
    else:
        print("\n" + "="*80)
        print("🤖 MODEL SELECTION")
        print("="*80)
        print("\nWhich language model would you like to use?")
        print("  1. Azure OpenAI (GPT-4o) - Enterprise-grade, high quality")
        print("  2. Google Gemini (2.5 Flash) - Fast, cost-effective")
        print("  3. Anthropic Claude (3.5 Sonnet) - Complex reasoning, safety")
        print("  4. Ollama (local models) - Privacy, offline, free")
        print()
        while True:
            choice = input("Enter choice (1-4): ").strip()
            if choice in ('1', '2', '3', '4'):
                break
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        
        mode_map = {'1': 'azure', '2': 'gemini', '3': 'claude', '4': 'ollama'}
        mode = mode_map[choice]

    ollama_selection = 'all'
    if mode == 'ollama':
        if 'ollama_selection' in config:
            ollama_selection = config['ollama_selection']
            print(f"ℹ️  Using saved Ollama selection: {ollama_selection}")
        elif available_ollama_models:
            print("\nWhich Ollama model(s) would you like to use?")
            for i, model_name in enumerate(available_ollama_models):
                print(f"  {i+1}. {model_name}")
            print(f"  {len(available_ollama_models)+1}. All models in parallel")
            print()
            while True:
                choice = input(f"Enter choice (1-{len(available_ollama_models)+1}): ").strip()
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(available_ollama_models):
                        ollama_selection = available_ollama_models[choice_num-1]
                        break
                    elif choice_num == len(available_ollama_models)+1:
                        ollama_selection = 'all'
                        break
                except ValueError:
                    pass
                print("❌ Invalid choice. Please enter a valid number.")
        else:
            print("⚠️  No Ollama models found. Please make sure Ollama is running and models are installed.")
            return 'azure', None # Fallback to azure

    # Ask to remember choice
    if 'remember_choice' not in config:
        print()
        remember = input("Remember this choice for future runs? (y/n): ").strip().lower()
        if remember in ('y', 'yes'):
            config['mode'] = mode
            config['ollama_selection'] = ollama_selection
            config['remember_choice'] = True
            if save_config(config):
                print(f"✅ Preference saved to {CONFIG_FILE}")
    
    print("="*80 + "\n")
    return mode, ollama_selection

def clear_config():
    """Clear all saved preferences."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print(f"✅ Cleared config file: {CONFIG_FILE}")
    else:
        print("ℹ️  No config file to clear")
