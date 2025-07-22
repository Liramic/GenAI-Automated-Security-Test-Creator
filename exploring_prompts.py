from Main.prompt_helper import generate_test_creation_general_prompt
from AI.langchain_api_access import simple_message, structered_output_message
from Main.main_integration import handle_product
from General.JobClasses import JobType
from API.iriusrisk_api import list_all_products
from Main.prompt_helper import TestPlan, TestStep, pretty_print_test_plan

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
    Using the component, threat, and countermeasure below as context, explain the countermeasure in a clear way to someone not familiar with cybersecurity.
    Create a new name for a cybersecurity countermeasure that clearly indicates its main function, the specific component name it protects, and the system or software it is associated with, if relevant. 
    Also, create a description of the countermeasure, explain its importance and how it mitigates the threat. Use layman's terms and avoid technical jargon. you don't need to repeat the name in the description unless it's necessary.
    Include any specific examples or practical steps from the original countermeasure description and rephrase them for clarity if necessary. If there are no examples or practical steps,  create a relevant example to illustrate how the countermeasure operates.
    If there is a link provided in the original countermeasure description, use that exact link in your description.
"""

#trying over all cms, you can try over just one if you want.
for cm_i in [cm_1, cm_2, cm_3, cm_4]:
    whole_prompt = generate_test_creation_general_prompt(cm_i, base_prompt)
    test_plan = structered_output_message(whole_prompt, TestPlan)
    pretty_print_test_plan(test_plan)

