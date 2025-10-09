from Main.prompt_helper import generate_test_creation_general_prompt
from AI.langchain_api_access import simple_message, structered_output_message, get_available_ollama_models, get_ollama_model
from Main.main_integration import handle_product
from General.JobClasses import JobType
from API.iriusrisk_api import list_all_products
from Main.prompt_helper import TestPlan, TestStep, pretty_print_test_plan, format_test_plan_as_string
from langchain_community.chat_models import ChatOllama
import os
from datetime import datetime

####################################################
# code I used to fetch some CM details
####################################################
#at first I listed the current products in irius.
#products = list_all_products()
#print(products.keys())
# handle_product("product_name", JobType.CREATE_TEST)

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

#trying over all cms, you can try over just one if you want.
# Get available Ollama models
ollama_models = get_available_ollama_models()

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

# If Ollama models available, test each one
if ollama_models:
    print(f"\n{'='*80}")
    print(f"🤖 Found {len(ollama_models)} Ollama model(s). Testing each...")
    print(f"{'='*80}\n")
    
    # Create output directory for model results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"model_outputs_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Saving outputs to: {output_dir}/\n")
    
    for model_idx, model_name in enumerate(ollama_models):
        color = color_list[model_idx % len(color_list)]
        
        print(f"\n{COLORS[color]}{'='*80}")
        print(f"🎯 TESTING MODEL: {model_name}")
        print(f"{'='*80}{COLORS['reset']}\n")
        
        # Create model instance for this specific model
        model_instance = ChatOllama(model=model_name, temperature=0.7, format='json')
        
        # Create a file for this model's output
        safe_model_name = model_name.replace('/', '_').replace(':', '_')
        output_file_path = os.path.join(output_dir, f"{safe_model_name}.txt")
        
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            # Write header to file
            output_file.write(f"{'='*80}\n")
            output_file.write(f"MODEL: {model_name}\n")
            output_file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output_file.write(f"{'='*80}\n\n")
            
            for cm_idx, cm_i in enumerate([cm_1, cm_2, cm_3, cm_4], start=1):  # Test all CMs
                # Enhanced prompt for JSON output
                json_prompt = f"""{base_prompt}

IMPORTANT: Respond ONLY with valid JSON matching this exact structure:
{{
  "test_name": "string - name of the test",
  "steps": [
    {{
      "step_number": 1,
      "instruction": "string - clear instruction for the step",
      "expected_result": "string - expected outcome"
    }}
  ]
}}

Current countermeasure details:
{cm_i}
"""
                
                try:
                    from langchain_core.messages import HumanMessage
                    import json
                    
                    # Get response from model
                    response = model_instance([HumanMessage(content=json_prompt)])
                    
                    # Parse JSON response
                    try:
                        result_json = json.loads(response.content)
                        # Create TestPlan from JSON
                        test_plan = TestPlan(
                            test_name=result_json.get('test_name', 'Untitled Test'),
                            steps=[TestStep(**step) for step in result_json.get('steps', [])]
                        )
                    except json.JSONDecodeError as je:
                        print(f"⚠️  JSON Parse Error: {je}")
                        print(f"Raw response: {response.content[:500]}...")
                        continue
                    
                    # Extract countermeasure name from cm_i
                    cm_name_line = [line for line in cm_i.split('\n') if 'Countermeasure name:' in line]
                    cm_name = cm_name_line[0].replace('Countermeasure name:', '').strip() if cm_name_line else f"CM #{cm_idx}"
                    
                    # Print with colored model name header
                    print(f"{COLORS[color]}┌─ Countermeasure #{cm_idx} ─────────────────────┐{COLORS['reset']}")
                    print(f"{COLORS[color]}│ Model: {model_name:40s} │{COLORS['reset']}")
                    print(f"{COLORS[color]}│ CM: {cm_name:43s} │{COLORS['reset']}")
                    print(f"{COLORS[color]}└────────────────────────────────────────────────┘{COLORS['reset']}\n")
                    pretty_print_test_plan(test_plan)
                    print(f"\n{COLORS[color]}{'─'*60}{COLORS['reset']}\n")
                    
                    # Write to file
                    output_file.write(f"\n{'='*80}\n")
                    output_file.write(f"Countermeasure #{cm_idx}: {cm_name}\n")
                    output_file.write(f"{'='*80}\n\n")
                    output_file.write(format_test_plan_as_string(test_plan))
                    output_file.write(f"\n{'-'*80}\n")
                    
                except Exception as e:
                    print(f"\n❌ Error with model {model_name}: {e}\n")
                    output_file.write(f"\n❌ Error processing countermeasure #{cm_idx}: {e}\n")
                    continue
        
        print(f"\n{COLORS[color]}✅ Model {model_name} results saved to: {output_file_path}{COLORS['reset']}\n")
else:
    # Fallback to default behavior (Azure or single Ollama)
    print("No Ollama models found or using Azure API...")
    for cm_i in [cm_1, cm_2, cm_3, cm_4]:
        whole_prompt = generate_test_creation_general_prompt(cm_i, base_prompt)
        test_plan = structered_output_message(whole_prompt, TestPlan)
        
        # Check if API returned an error
        if hasattr(test_plan, 'error'):
            print(f"\n⚠️  API Error: {test_plan}")
            print("Please configure Azure OpenAI credentials (PYTHON_SECRET, PYTHON_NONCE, and encrypted tokens)\n")
            break
        
        pretty_print_test_plan(test_plan)

