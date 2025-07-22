from API.iriusrisk_api import get_product_components_and_threats, upadte_cm_test, list_all_products, update_cm_genai_name_and_desc
from Main.prompt_helper import create_countermeasure_details, generate_prompt, extract_cm_exaplain_output, TestPlan
from AI.langchain_api_access import simple_message, structered_output_message
from tqdm import tqdm
import General.Logger as Logger
from General.Entities import export_components_to_dict, load_components_from_dict
from General.JobClasses import JobType
from General.Helpers import get_output_folder, save_dict_as_json, load_dict_from_json
import os


def handle_product(product_id, job_type=JobType.CREATE_TEST):
    try:
        comps = get_product_components_and_threats(product_id)
    except Exception as e:
        Logger.log_error(f"Error in getting components for product {product_id}")
        Logger.log_error(e)
        return
    
    for component_name in tqdm(comps):
        component = comps[component_name]
        for threat_ref in component.threats:
            threat = component.threats[threat_ref]
            for countermeasure_name in threat.counterMeasures:
                countermeasure = threat.counterMeasures[countermeasure_name]
                try:
                    cm_details = create_countermeasure_details(component, threat, countermeasure)
                    print("\n\n")
                    print(cm_details)
                    print("\n\n")
                    prompt = generate_prompt(cm_details, job_type)
                    if ( countermeasure.should_update(job_type)):
                            if ( job_type == JobType.CREATE_TEST):
                                ai_response_test_plan = structered_output_message(prompt, TestPlan)
                                countermeasure.genai_test = ai_response_test_plan.dict()
                                upadte_cm_test(product_id, component.ref, countermeasure.ref, ai_response)
                            elif ( job_type == JobType.EXPLAIN_COUNTERMEASURE):
                                ai_response = simple_message(prompt)
                                new_name, new_desc = extract_cm_exaplain_output(ai_response)
                                countermeasure.genai_cm_name = new_name
                                countermeasure.genai_cm_desc = new_desc
                                update_cm_genai_name_and_desc(product_id, component.ref, countermeasure.ref, new_name, new_desc)
                except Exception as e:
                    Logger.log_error(f"Error in generating test steps for {component_name} - {threat.name} - {countermeasure.name}")
                    Logger.log_error(e)  
    return comps


def export_product_components(product_id, comps, job_type=JobType.CREATE_TEST):
    output_folder = get_output_folder(product_id, job_type)
    save_dict_as_json(export_components_to_dict(comps), output_folder, f"{product_id}_components")


def run_job_on_specific_product(product_id, job_type=JobType.CREATE_TEST):
        Logger.log_info(f"Starting the integration process for product {product_id}. job type: {job_type}")
        comps = handle_product(product_id, job_type)
        export_product_components(product_id, comps, job_type)
        Logger.log_info(f"Ended the integration process for product {product_id}. job type: {job_type}")


def create_tests_for_all_products_first_time():
    Logger.log_info("Starting the integration process.")
    products = list_all_products().keys()
    products = list(products)
    for product in tqdm(products):
        run_job_on_specific_product(product, "create_test")
    Logger.log_info("Ended the integration process.")


def load_product_components(product_id):
    output_folder = get_output_folder(product_id)
    filename = os.path.join(output_folder, f"{product_id}.json")
    comps = load_components_from_dict(load_dict_from_json(filename))
    return comps

def get_genai_test(product_id, component_ref, threat_ref, countermeasure_ref):
    try:
        comps = load_product_components(product_id)
    except Exception as e:
        Logger.log_error(f"Error in loading components for product {product_id}")
        Logger.log_error(e)
        return None
    try:
        component = comps[component_ref]
    except Exception as e:
        Logger.log_error(f"Error in getting component {component_ref} for product {product_id}")
        Logger.log_error(e)
        return None
    try:
        threat = component.threats[threat_ref]
    except Exception as e:
        Logger.log_error(f"Error in getting threat {threat_ref} for component {component_ref} of product {product_id}")
        Logger.log_error(e)
        return None
    try:
        countermeasure = threat.counterMeasures[countermeasure_ref]
    except Exception as e:
        Logger.log_error(f"Error in getting countermeasure {countermeasure_ref} for threat {threat_ref} of component {component_ref} of product {product_id}")
        Logger.log_error(e)
        return None
    
    return countermeasure.genai_test

if __name__ == "__main__":  
    run_job_on_specific_product("product_1", JobType.EXPLAIN_COUNTERMEASURE)
    