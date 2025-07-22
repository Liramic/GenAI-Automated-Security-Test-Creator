from General.Entities import *
from AI.langchain_api_access import simple_message
from General.Entities import JobType
import json
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional


class TestWithCode(BaseModel):
    code: str = Field(description="Test's python code")
    test_parameters: str = Field(description="json content of test_parameters.json")
    requirements_file : str = Field(description="requirements.txt file content of python libraries to install")

class TestStep(BaseModel):
    step_number: int = Field(..., description="The number of the step in the test plan")
    instruction: str = Field(..., description="Clear instruction for the test step")
    expected_result: str = Field(..., description="Expected outcome after performing the step")

class TestPlan(BaseModel):
    test_name: str = Field(..., description="Name of the test")
    steps: List[TestStep] = Field(..., description="List of steps to perform the test, ideally no more than 8")

def pretty_print_test_plan(test_plan: TestPlan):
    print(f"\nTest name: {test_plan.test_name}\n")
    for step in sorted(test_plan.steps, key=lambda s: s.step_number):
        print(f"{step.step_number}. {step.instruction}")
        print(f"   Expected result: {step.expected_result}\n")

def format_test_plan_as_string(test_plan: TestPlan) -> str:
    output = [f"\nTest name: {test_plan.test_name}\n"]
    for step in sorted(test_plan.steps, key=lambda s: s.step_number):
        output.append(f"{step.step_number}. {step.instruction}")
        output.append(f"   Expected result: {step.expected_result}\n")
    return "\n".join(output)


def create_countermeasure_details(component : Component, threat: Threat, countermeasure: CounterMeasure):
    component_details = component.get_description()
    threat_details = threat.get_description()
    countermeasure_details = countermeasure.get_description()

    return f"{component_details}\n{threat_details}\n{countermeasure_details}"

def explain_cm_prompt_start():
    return """
        Using the component, threat, and countermeasure below as context, explain the countermeasure in a clear way to someone not familiar with cybersecurity.
        Create a new name for a cybersecurity countermeasure that clearly indicates its main function, the specific component name it protects, and the system or software it is associated with, if relevant. 
        Also, create a description of the countermeasure, explain its importance and how it mitigates the threat. Use layman's terms and avoid technical jargon. you don't need to repeat the name in the description unless it's necessary.
        Include any specific examples or practical steps from the original countermeasure description and rephrase them for clarity if necessary. If there are no examples or practical steps,  create a relevant example to illustrate how the countermeasure operates.
        If there is a link provided in the original countermeasure description, use that exact link in your description.
        """

def generate_test_creation_general_prompt(cm_details, prompt):
    return f""""
    {prompt}

    Current countermeasure details:
    {cm_details}
    """

def generate_prompt(cm_details, job_type = JobType.CREATE_TEST):
    if job_type == JobType.CREATE_TEST:
        return f"""
            Using the component, threat, and countermeasure below as context, explain the countermeasure in a clear way to someone not familiar with cybersecurity.
            Create a new name for a cybersecurity countermeasure that clearly indicates its main function, the specific component name it protects, and the system or software it is associated with, if relevant. 
            Also, create a description of the countermeasure, explain its importance and how it mitigates the threat. Use layman's terms and avoid technical jargon. you don't need to repeat the name in the description unless it's necessary.
            Include any specific examples or practical steps from the original countermeasure description and rephrase them for clarity if necessary. If there are no examples or practical steps,  create a relevant example to illustrate how the countermeasure operates.
            If there is a link provided in the original countermeasure description, use that exact link in your description.
                
            Current countermeasure details:
            {cm_details}
            """

    elif job_type == JobType.EXPLAIN_COUNTERMEASURE:
        return f"""
        {explain_cm_prompt_start()}

        output should look like {example_of_cm_explain()}
        
        Current countermeasure details:
        {cm_details}
        """
    
    elif job_type == JobType.CREATE_CODE_TEST:
        return f"""
        output code should comply these : {test_code_checkboxes()}

        the code is suppose to check weather the countermeasure is applied correctly or not. the should try to bypass the countermeasure, and a successful bypass should be considered a failure.
        together with the code provided, you will provide the parameters assumed to be in "test_parameters.json", with all values set to defaults you see fit, so that later the person that
        runs the code can change these parameters and won't have to touch the code. these are very simple parameters that should help the code to run, such as ip address, tennant id, etc..
        you should also return the cvontent of the file "requirements.txt" which is the python libraries and versions to install before using the code.
        
        Current countermeasure details:
        {cm_details}
        """

#todo: how to support an update of the code by the developer so that it fixes other instances.

def test_code_checkboxes():
    return """
    the code should be able to run on any system with python3 installed.
    the code assumes external parameters are provided in a json format, in a file named "test_parameters.json" that is saved in the same library as the code.
    these parameters are unrelated to the test results! they are only used to be able to run the test, for example: ip address, tennant id, etc..
    the code should send request, use clever way to bypass countermeasures, and not just check values in the json.
    when reading the parameters in the code, assume you have a function named : load_parameters_for_test(current_dir = None). you send the script dir to it. the import is "from TestHelpers import load_parameters_for_test"
    the test code should run when we call externally to "run_test()" function in the code.
    For example only: if you want to check IAM role - prepare a request that will check it. if you want to assume a XSS is blocked - make a request that tries to inject a script. etc.. 
    the code should be specific for the countemeasure that is being checked.
    use specific exception types but also a general exception catch so that no excetion is throwed from the function.
    run_test function output should be a dictionary with the following structure:
    test_passed (bool), log_for_each_step (list of strings), errors if any (list of strings).
    """

def example_of_cm_explain():
    return """{"name": "XX", "description": "XX"}"""

def extract_cm_exaplain_output(output: str):
    json_data = json.loads(output, strict=False)
    name = json_data.get("name", "")
    desc = json_data.get("description", "")
    return [name, desc]

def example_of_the_output():
    return """
    Test name: XXXXXXX
    1. Clearly state the first step to be taken...
    Expected result: [Describe the expected outcome of the step]
    2. Continue in this manner up to 8 steps...less if possible.
    """

def interpret_create_test_code_response(response):
    return response.code, response.test_parameters, response.requirements_file


if __name__ == "__main__":
    cm_details = """
        Component name: Commander API Endpoint
        Threat name: An attacker exploits a weakness in the configuration of access controls and is able to bypass the intended protection that these measures guard against and thereby obtain unauthorized access to the application, ref: CAPEC-180-BROKEN-ACCESS-CONTROL, desc: <p>An Access Control functionality often spans many areas of software depending on the complexity of the access control system. For example, managing access control metadata or building caching for scalability purposes are often additional components in an access control system that need to be built or managed. Vulnerabilities appear when a user is able to successfully request access to something they usually shouldn't have access to. Oftentimes this is found when the authorization is not implemented properly. A typical example would be a certain endpoint on a website that throws a 403 forbidden error which is then bypassed by adding an X-Forwarded-For: "127.0.0.1" header.</p>
        Countermeasure name: Apply authorization checks to segregate and control access to user data, ref: CWE-285, description: <p>Applications protecting sensitive or otherwise restricted resources must ensure that only appropriate and authorized users can access the application data. It is important that an application prevent unauthorized users gaining inappropriate access to each other's data. Although user A and user B may both be trusted to access data within the application, they may be only authorized to access different subsets of the protected resources.&nbsp; E.g. user 
        A should not be able to access user B's personal data by manipulating a request (typical examples are the manipulation of an ID value or other object reference sent in the URL or body of an HTTP request).</p><p>It is not sufficient to rely on obscurity, for example obfuscated or secret URLs or filenames. The application must validate each request for protected data against the proven identity of the user. Before providing access to restricted resources the application must:</p><ul><li>Ensure the user has undergone appropriate authentication (identification and verification, or ID&amp;V). E.g. they must have provided their identity and confirmed this with a password, token, or other verification. Typically this is done by checking the validity of the session token issued after login.</li><li>Confirm the user is authorized to access the data or resource they are requesting. E.g. their confirmed identify is checked against a server-side access control matrix to determine whether they may access the requested resource.</li><li>Access controls should be granular and make it possible to issue to individual resources to individual users or roles.</li></ul><p>URL and asset based access control is provided by most web-frameworks, and it is preferable to use an established and proven framework.</p>
    """
    print(cm_details)
    prompt = generate_prompt(cm_details)
    print(simple_message(prompt))



