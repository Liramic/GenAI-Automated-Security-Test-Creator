from Main.prompt_helper import generate_test_creation_general_prompt
from AI.langchain_api_access import simple_message, structered_output_message, get_available_ollama_models, get_ollama_model, set_ollama_preference, AI_ERROR
from Main.main_integration import handle_product
from General.JobClasses import JobType
from API.iriusrisk_api import list_all_products
from Main.prompt_helper import TestPlan, TestStep, pretty_print_test_plan, format_test_plan_as_string
from General.ConfigHelper import get_model_selection
from langchain_community.chat_models import ChatOllama
import os
from datetime import datetime
import threading
import queue
from pydantic import ValidationError
import json

# Import cloud-based LLM modules
from AI import gemini_api_access
from AI import claude_api_access

####################################################
# INTERACTIVE MODEL SELECTION
####################################################
# Get available Ollama models first
available_ollama_models = get_available_ollama_models()
# Ask user for their choice
MODE, OLLAMA_SELECTION = get_model_selection(available_ollama_models)
# Set preference for langchain_api_access
set_ollama_preference(MODE == 'ollama')

####################################################
# Examples of cm details
####################################################

cm_1 = """Component name: ETL
Threat name: Attackers gain unauthorized access to the root account due to the lack of configuration of the account
Threat ref: AWS-LOST-ACCESS-ROOT
Threat description: <div>
                                Attackers could gain unauthorized access to the administrator account due to the lack of
                                the account and its security mechanisms, like modifying credentials and adding/removing
                                user accounts.
                                </div>
Countermeasure name: Create Individual Accounts
Countermeasure ref: Hydras-AWS-IAM-2.3
Countermeasure description: By creating individual IAM users for people accessing your account, you can give each IAM user a unique set of security credentials. You can also grant different permissions to each IAM user. If necessary, you can change or revoke an IAM user's permissions any time. (If you give out your AWS root credentials, it can be difficult to revoke them, and it is impossible to restrict their permissions.).
Remediation:
Login to the AWS Management Console as an administrator.
Select IAM.
Select Users.
Click "Create New Users".
Complete the required information.
Uncheck "Create access key for users".
Click "Create".
Select the user.
Click "Manage Password".
Select the required options and click "apply".
Select "Show User Security Credentials".
Securely supply the password to your user."""

cm_2 = """Component name: ETL
Threat name: Attackers gain unauthorized access to the root account due to the lack of configuration of the account
Threat ref: AWS-LOST-ACCESS-ROOT
Threat description: <div>
                                Attackers could gain unauthorized access to the administrator account due to the lack of
                                the account and its security mechanisms, like modifying credentials and adding/removing
                                user accounts.
                                </div>
Countermeasure name: Enable MFA for root accounts
Countermeasure ref: Hydras-AWS-IAM-2.2
Countermeasure description: Root is highly privileged and therefore using a multi-factor authentication (MFA) device enhances the security of the login process. With MFA, users have a device that generates a unique authentication code (a one-time password, or OTP) and users must provide both their normal credentials (like their username and password) and the OTP. The MFA device can either be a special piece of hardware, or it can be a virtual device. The recommendation for the root account is to use a hardware based device as it has a smaller attack surface and cannot be duplicated.
Remediation:
Login to the AWS Management Console as root.
Select "Dashboard" and under "Security Status" choose "Activate MFA" on your root account.
Select Activate MFA".
In the wizard, choose "A hardware MFA" device and then select Next Step.
In the Serial Number box, enter the serial number that is found on the back of the MFA device.&nbsp;
In the Authentication Code 1 box, enter the six-digit number displayed by the MFA device.
Wait until the device refreshes the code, and then enter the next six-digit number into the Authentication Code 2 box.
Select "Next Step".&nbsp;
The MFA device is now associated with the AWS account.&nbsp;
&nbsp;
"""

cm_3 = """Component name: ETL
Threat name: Attackers gain unauthorized access to the root account due to the lack of configuration of the account
Threat ref: AWS-LOST-ACCESS-ROOT
Threat description: <div>
                                Attackers could gain unauthorized access to the administrator account due to the lack of
                                the account and its security mechanisms, like modifying credentials and adding/removing
                                user accounts.
                                </div>
Countermeasure name: Avoid the use of the root account unless absolutely necessary
Countermeasure ref: Hydras-AWS-IAM-2.1
Countermeasure description: The root account is the one which was used to open the AWS account with Amazon. Therefore it has full unrestricted access to all resources within the account including billing information. Reducing the use of this account and instead using personalized accounts with restricted permissions ensures the principles of least privilege and can help prevent accidental disclosure of credentials or unintended changes.
Remediation:
Follow the remediation in "Create Individual Accounts".
"""

cm_4 = """Component name: ETL
Threat name: Attackers gain unauthorized access to the user account due to the lack of configuration of the account
Threat ref: AWS-LOST-ACCESS-USER
Threat description: <p>Attackers could gain unauthorized access to the user account due to a lack of configuration of the account, such as an incorrect configuration of the security question to reset the password.</p>
Countermeasure name: Create a Password Policy enforcing strong passwords
Countermeasure ref: Hydras-AWS-IAM-2.6
Countermeasure description: Enforcing a strong password policy increases resiliency and reduces the chances of the password being compromised either through brute force attempts, keystroke logging tools or stolen credentials amongst others.Remediation:&nbsp;&nbsp;Login to AWS Console (ensure you have 
permissions to update IAM).Go to IAM Service on the AWS Console.Click on Account Settings.Set "Minimum password length" to 14 or greater.Check "Require at least one uppercase letter".Check "Require at least one lowercase letter".Check "Require at least one number".Check "Require at least one non-alphanumeric character"Check "Enable password expiration" and set the period to at least 90 days.Check "Prevent password reuse" and set the number to at least 10.
"""


####################################################
# choose your prerferref CM and generate your prompt
####################################################

#change however you find. don't worry about how the output looks.
base_prompt = """
    Conduct research on the specified countermeasure provided below.
    Craft a detailed test plan tailored for individuals not well-versed in cybersecurity.
    This plan should be specific to a particular threat existing within a designated component.
    Ensure clarity by providing explicit instructions, no more than 8 steps, on how to conduct security validation.
    Each instruction clearly detailing actions to validate the countermeasure's effectiveness against the threat. no generalsecurtiy suggestions.
    If there are existing test steps for the component, enhance them for better understanding. you can also conduct research forthe improvement, research instruction are in the next line.
    If not, conduct research to create them and in the research avoid mentioning specific component names or referring to anyparticular entities.
"""

# List of countermeasures to test
countermeasures = [cm_1, cm_2, cm_3, cm_4]

# ANSI color codes for bold colored output
COLORS = {
    'red': '\033[1;31m',
    'green': '\033[1;32m',
    'yellow': '\033[1;33m',
    'blue': '\033[1;34m',
    'magenta': '\033[1;35m',
    'cyan': '\033[1;36m',
    'white': '\033[1;37m',
    'reset': '\033[0m'
}
color_list = ['cyan', 'magenta', 'yellow', 'green', 'blue', 'red']

def process_cloud_llm(provider_name, results_list, color='cyan'):
    """Generic function to process countermeasures using any cloud-based LLM.
    
    Args:
        provider_name: 'azure', 'gemini', or 'claude'
        results_list: List to append results to
        color: Color for terminal output
    """
    print(f"\n{COLORS[color]}{'='*80}")
    print(f"🎯 STARTING {provider_name.upper()} LLM")
    print(f"{'='*80}{COLORS['reset']}\n")
    
    for cm_idx, cm_i in enumerate(countermeasures, start=1):
        try:
            whole_prompt = generate_test_creation_general_prompt(cm_i, base_prompt)
            
            if provider_name == 'azure':
                from AI.langchain_api_access import get_chat_model
                model = get_chat_model(use_ollama=False)
                test_plan = structered_output_message(model, TestPlan, whole_prompt, False)
                
            elif provider_name == 'gemini':
                # Add instruction for JSON output with exact schema
                json_prompt = f"{whole_prompt}\n\nRespond ONLY with valid JSON matching this EXACT structure (no markdown, no explanations): {{\"test_name\": \"...\", \"steps\": [{{\"step_number\": 1, \"instruction\": \"...\", \"expected_result\": \"...\"}}]}}"
                result = gemini_api_access.generate_content(
                    prompt=json_prompt,
                    temperature=0,
                    max_tokens=4096
                )
                if result["success"]:
                    # Parse JSON response
                    try:
                        json_text = result["text"].strip()
                        # Clean markdown code blocks if present
                        if json_text.startswith('```'):
                            json_text = json_text.split('```')[1]
                            if json_text.startswith('json'):
                                json_text = json_text[4:].strip()
                            else:
                                json_text = json_text.strip()
                        
                        # Find JSON boundaries (handle cases where response includes text)
                        start_idx = json_text.find('{')
                        end_idx = json_text.rfind('}')
                        if start_idx != -1 and end_idx != -1:
                            json_text = json_text[start_idx:end_idx+1]
                        
                        json_data = json.loads(json_text)
                        test_plan = TestPlan(**json_data)
                    except (json.JSONDecodeError, ValidationError) as e:
                        test_plan = AI_ERROR(f"Failed to parse JSON: {e}")
                else:
                    test_plan = AI_ERROR(result["error"])
                    
            elif provider_name == 'claude':
                # Add instruction for JSON output with exact schema
                json_prompt = f"{whole_prompt}\n\nRespond ONLY with valid JSON matching this EXACT structure (no explanations, no markdown): {{\"test_name\": \"...\", \"steps\": [{{\"step_number\": 1, \"instruction\": \"...\", \"expected_result\": \"...\"}}]}}"
                result = claude_api_access.generate_content(
                    prompt=json_prompt,
                    temperature=0,
                    max_tokens=4096
                )
                if result["success"]:
                    try:
                        json_text = result["text"].strip()
                        # Clean markdown code blocks if present
                        if json_text.startswith('```'):
                            json_text = json_text.split('```')[1]
                            if json_text.startswith('json'):
                                json_text = json_text[4:].strip()
                            else:
                                json_text = json_text.strip()
                        
                        # Find JSON boundaries (handle cases where response includes text)
                        start_idx = json_text.find('{')
                        end_idx = json_text.rfind('}')
                        if start_idx != -1 and end_idx != -1:
                            json_text = json_text[start_idx:end_idx+1]
                        
                        json_data = json.loads(json_text)
                        test_plan = TestPlan(**json_data)
                    except (json.JSONDecodeError, ValidationError) as e:
                        test_plan = AI_ERROR(f"Failed to parse JSON: {e}")
                else:
                    test_plan = AI_ERROR(result["error"])
            else:
                test_plan = AI_ERROR(f"Unknown provider: {provider_name}")

            if isinstance(test_plan, AI_ERROR):
                print(f"⚠️  API Error from {provider_name.upper()} for CM #{cm_idx}: {test_plan}")
                results_list.append((cm_idx, f"API Error: {test_plan}"))
            else:
                results_list.append((cm_idx, test_plan))
                pretty_print_test_plan(test_plan)

        except Exception as e:
            print(f"❌ Unhandled exception with {provider_name.upper()} for CM #{cm_idx}: {e}")
            results_list.append((cm_idx, f"Unhandled Error: {e}"))
    
    print(f"\n{COLORS[color]}✅ FINISHED {provider_name.upper()}{COLORS['reset']}\n")


def process_model(model_name, results_queue, color):
    """Function to be run in a thread for processing a single Ollama model."""
    print(f"\n{COLORS[color]}{'='*80}")
    print(f"🎯 STARTING MODEL: {model_name}")
    print(f"{'='*80}{COLORS['reset']}\n")

    # Instantiate the model once for all countermeasures
    model = get_ollama_model(model_name)
    
    model_results = []
    for cm_idx, cm_i in enumerate(countermeasures, start=1):
        try:
            whole_prompt = generate_test_creation_general_prompt(cm_i, base_prompt)
            test_plan = structered_output_message(model, TestPlan, whole_prompt, False, model_name=model_name)

            if isinstance(test_plan, AI_ERROR):
                print(f"⚠️  API Error from {model_name} for CM #{cm_idx}: {test_plan}")
                model_results.append((cm_idx, f"API Error: {test_plan}"))
            else:
                model_results.append((cm_idx, test_plan))

        except Exception as e:
            print(f"❌ Unhandled exception with model {model_name} for CM #{cm_idx}: {e}")
            model_results.append((cm_idx, f"Unhandled Error: {e}"))

    results_queue.put((model_name, model_results))
    print(f"\n{COLORS[color]}✅ FINISHED MODEL: {model_name}{COLORS['reset']}\n")

# Main logic
if MODE == 'ollama':
    models_to_run = []
    if OLLAMA_SELECTION == 'all':
        models_to_run = available_ollama_models
        print(f"\n{'='*80}")
        print(f"🤖 Running all {len(models_to_run)} Ollama models in parallel...")
        print(f"{'='*80}\n")
    elif OLLAMA_SELECTION in available_ollama_models:
        models_to_run = [OLLAMA_SELECTION]
        print(f"\n{'='*80}")
        print(f"🤖 Running selected Ollama model: {OLLAMA_SELECTION}")
        print(f"{'='*80}\n")
    else:
        print(f"⚠️ Model '{OLLAMA_SELECTION}' not found. Exiting.")

    if models_to_run:
        # Create a single output directory
        output_dir = "Output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"📁 Saving outputs to: {output_dir}/\n")

        threads = []
        results_queue = queue.Queue()
        
        for i, model_name in enumerate(models_to_run):
            color = color_list[i % len(color_list)]
            thread = threading.Thread(target=process_model, args=(model_name, results_queue, color))
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # Process results from the queue
        while not results_queue.empty():
            model_name, results = results_queue.get()
            safe_model_name = model_name.replace('/', '_').replace(':', '_')
            output_file_path = os.path.join(output_dir, f"{safe_model_name}_{timestamp}.txt")
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(f"MODEL: {model_name}\n\n")
                print(f"\n\n{COLORS['green']}{'='*30} RESULTS FOR: {model_name.upper()} {'='*30}{COLORS['reset']}")
                for cm_idx, result in results:
                    f.write(f"--- Countermeasure #{cm_idx} ---\n")
                    print(f"\n{COLORS['yellow']}--- Countermeasure #{cm_idx} ---{COLORS['reset']}")
                    if isinstance(result, TestPlan):
                        formatted_plan = format_test_plan_as_string(result)
                        f.write(formatted_plan + "\n\n")
                        print(formatted_plan)
                    else:
                        f.write(f"{result}\n\n")
                        print(result)
            print(f"\n{COLORS['green']}{'='*80}{COLORS['reset']}")
            print(f"📝 Results for {model_name} saved to {output_file_path}")

elif MODE in ['azure', 'gemini', 'claude']:
    # Generic cloud LLM processing
    provider_display_names = {
        'azure': 'Azure OpenAI (GPT-4o)',
        'gemini': 'Google Gemini (2.5 Flash)',
        'claude': 'Anthropic Claude (3.5 Sonnet)'
    }
    
    display_name = provider_display_names.get(MODE, MODE.upper())
    print(f"🤖 Using {display_name}...")
    
    # Create output directory
    output_dir = "Output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate provider-specific filename
    file_prefixes = {
        'azure': 'azure_gpt-4o',
        'gemini': 'gemini_2.5-flash',
        'claude': 'claude_3.5-sonnet'
    }
    file_prefix = file_prefixes.get(MODE, MODE)
    output_file_path = os.path.join(output_dir, f"{file_prefix}_{timestamp}.txt")
    print(f"📁 Saving outputs to: {output_dir}/\n")
    
    try:
        cloud_results = []
        process_cloud_llm(MODE, cloud_results, color='cyan')
        
        # Save all results to file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(f"MODEL: {display_name}\n\n")
            for cm_idx, result in cloud_results:
                f.write(f"--- Countermeasure #{cm_idx} ---\n")
                if isinstance(result, TestPlan):
                    formatted_plan = format_test_plan_as_string(result)
                    f.write(formatted_plan + "\n\n")
                else:
                    f.write(f"{result}\n\n")
        
        print(f"\n{COLORS['green']}{'='*80}{COLORS['reset']}")
        print(f"📝 {display_name} results saved to {output_file_path}")
        
    except Exception as e:
        print(f"\n❌ An unexpected error occurred during {display_name} processing: {e}")
        print(f"Please ensure {MODE.upper()} credentials are correct and the service is available.")
        print("The script will now exit.")