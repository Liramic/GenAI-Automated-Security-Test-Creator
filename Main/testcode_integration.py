from API.iriusrisk_api import get_product_components_and_threats, upadte_cm_test, list_all_products, update_cm_genai_name_and_desc
from Main.prompt_helper import create_countermeasure_details, generate_prompt, interpret_create_test_code_response, TestWithCode
from AI.langchain_api_access import simple_message, structered_output_message
from tqdm import tqdm
import General.Logger as Logger
from General.Entities import JobType
import os
import json
from Main.main_integration import load_product_components
from General.Helpers import to_valid_windows_folder_name, get_output_folder


def create_folder(path, env_type="", origname=""):
    if not os.path.exists(path):
        os.makedirs(path)
        if env_type != "" and env_type!= "countermeasure":
            #create a json file with the env_type:
            with open(os.path.join(path, f"{env_type}_environment.json"), 'w', encoding="utf-8") as outfile:
                dic = {"env_type": env_type}
                if (origname != ""):
                    dic["origname"] = origname
                json.dump(dic, outfile, indent=4)
    return path



def handle_product(product_id):
    job_type = JobType.CREATE_CODE_TEST
    try:
        #comps = get_product_components_and_threats(product_id)
        comps = load_product_components(product_id)
    except Exception as e:
        Logger.log_error(f"Error in getting components for product {product_id}")
        Logger.log_error(e)
        return
    
    product_output_folder = get_output_folder(product_id, job_type)

    for component_ref in tqdm(comps):
        component = comps[component_ref]
        comp_name = component.name
        component_folder = os.path.join(product_output_folder, to_valid_windows_folder_name(comp_name))
        create_folder(component_folder, "component", comp_name)
        for threat_ref in tqdm(component.threats):
            threat = component.threats[threat_ref]
            threat_folder = fr"{component_folder}/{to_valid_windows_folder_name(threat_ref)}"
            create_folder(threat_folder, "threat", threat_ref)
            for countermeasure_name in tqdm(threat.counterMeasures):
                countermeasure = threat.counterMeasures[countermeasure_name]
                folder_path_for_cm = fr"{threat_folder}/{to_valid_windows_folder_name(countermeasure.name)}"
                create_folder(folder_path_for_cm, "countermeasure", countermeasure.name)
                try:
                    cm_details = create_countermeasure_details(component, threat, countermeasure)
                    with open(os.path.join(folder_path_for_cm, "cm_details.txt"), 'w', encoding="utf-8") as outfile:
                        outfile.write(cm_details)

                    prompt = generate_prompt(cm_details, job_type)
                    if ( True ): #countermeasure.should_update(job_type)):
                        ai_response = structered_output_message(prompt, TestWithCode)
                        if (isinstance(ai_response, TestWithCode)):
                            #create test code file in the right folder:
                            code, parameters, requirements_file = interpret_create_test_code_response(ai_response)
                            with open(os.path.join(folder_path_for_cm, "test_code.py"), 'w', encoding="utf-8") as outfile:
                                outfile.write(code)
                            with open(os.path.join(folder_path_for_cm, "test_parameters.json"), 'w', encoding="utf-8") as outfile:
                                outfile.write(parameters)
                            with open(os.path.join(folder_path_for_cm, "requirements.txt"), 'w', encoding="utf-8") as outfile:
                                outfile.write(requirements_file)
                        else:
                            Logger.log_error(f"AI response error Error in generating test steps for {component_ref} - {threat.name} - {countermeasure.name}")
                            Logger.log_error(ai_response)
                except Exception as e:
                    Logger.log_error(f"Error in generating test steps for {component_ref} - {threat.name} - {countermeasure.name}")
                    Logger.log_error(e)  
    return comps

def collect_parameters(component_folder):
    parameter_counts = {}
    for threat_folder in os.listdir(component_folder):
        threat_path = os.path.join(component_folder, threat_folder)
        if os.path.isdir(threat_path):
            for cm_folder in os.listdir(threat_path):
                cm_path = os.path.join(threat_path, cm_folder)
                try:
                    if os.path.isdir(cm_path):
                        param_file = os.path.join(cm_path, "test_parameters.json")
                        if os.path.exists(param_file):
                            with open(param_file, 'r', encoding="utf-8") as f:
                                params = json.load(f)
                                for param in params:
                                    value = params[param]
                                    if param in parameter_counts:
                                        #parameter_counts[param][0] += value : maybe can be aggregated later using AI.
                                        parameter_counts[param][1] += 1
                                    else:
                                        parameter_counts[param] = [value, 1]
                except Exception as e:
                    Logger.log_error(f"Error in collecting parameters for {cm_path}")
                    Logger.log_error(e)
    return parameter_counts

def create_component_environment(component_folder, parameter_counts):
    general_params = {param: count_item[0] for param, count_item in parameter_counts.items() if count_item[1] > 1}
    component_env = {"env_type": "component", "general_parameters": general_params}
    with open(os.path.join(component_folder, "component_environment.json"), 'w', encoding="utf-8") as outfile:
        json.dump(component_env, outfile, indent=4)


def filter_parameters(component_folder):
    component_env_file = os.path.join(component_folder, "component_environment.json")
    if os.path.exists(component_env_file):
        with open(component_env_file, 'r', encoding="utf-8") as f:
            component_env = json.load(f)
            general_params = component_env.get("general_parameters", {})
            for threat_folder in os.listdir(component_folder):
                threat_path = os.path.join(component_folder, threat_folder)
                if os.path.isdir(threat_path):
                    for cm_folder in os.listdir(threat_path):
                        try:
                            cm_path = os.path.join(threat_path, cm_folder)
                            if os.path.isdir(cm_path):
                                param_file = os.path.join(cm_path, "test_parameters.json")
                                if os.path.exists(param_file):
                                    with open(param_file, 'r', encoding="utf-8") as f:
                                        params = json.load(f)
                                        filtered_params = {k: v for k, v in params.items() if k not in general_params}
                                        with open(os.path.join(cm_path, "test_parameters_filtered.json"), 'w', encoding="utf-8") as outfile:
                                            json.dump(filtered_params, outfile, indent=4)
                        except Exception as e:
                            Logger.log_error(f"Error in filtering parameters for {cm_path}")
                            Logger.log_error(e)


def handle_parameters_collection(product_id):
    try:
        comps = load_product_components(product_id)
    except Exception as e:
        Logger.log_error(f"Error in getting components for product {product_id}")
        Logger.log_error(e)
        return
    
    product_folder = get_output_folder(product_id, JobType.CREATE_CODE_TEST)
    for component_ref in tqdm(comps):
        component = comps[component_ref]
        comp_name = component.name
        component_folder = os.path.join(product_folder, to_valid_windows_folder_name(comp_name))
        create_folder(component_folder, "component", comp_name)
        parameter_counts = collect_parameters(component_folder)
        create_component_environment(component_folder, parameter_counts)
        filter_parameters(component_folder)


def run(prod_id):
    handle_product(prod_id)
    handle_parameters_collection(prod_id)