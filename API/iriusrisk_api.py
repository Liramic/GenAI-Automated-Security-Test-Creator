from General.RequestManager import RequestManager
from General.EncryptedTokens import get_irius_token
from General.Entities import Component, Threat, CounterMeasure, export_components_to_dict, load_components_from_dict
from General.Helpers import list_to_html_list, html_to_python_list, is_html_list_response, base64_decode, base64_encode, get_output_folder, save_dict_as_html, save_dict_as_json, load_dict_from_json
import os
import General.Logger as Logger

api_token = get_irius_token()
base_url = "https://your_name.iriusrisk.com/"

request_manager = RequestManager(api_token, False)


def list_all_products():
    url = base_url + "api/v1/products"
    products = dict()
    response = request_manager.SendRequestWithRetry(url, {}, {}, "get")
    if response.status_code == 200:
        products_json = response.json()
        for product in products_json:
            key = product.get("ref", "")
            if(key!=""):
                products[key] = product
    return products

def get_product_details(product_id):
    url = base_url + f"api/v1/products/{product_id}"
    response = request_manager.SendRequestWithRetry(url, {}, {}, "get")
    if response.status_code == 200:
        return response.json()

def get_product_components_from_json(details_json):
    components = dict()
    for component in details_json.get("components", []):
        key = component.get("ref", "")
        if(key!=""):
            components[key] = component
    return components

def get_product_components_and_threats(product_id):
    url = base_url + f"api/v1/products/{product_id}/threats"
    response = request_manager.SendRequestWithRetry(url, {}, {}, "get")
    if response.status_code == 200:
        components = dict()
        components_uc_dicts = response.json()
        # save_as_html(components_uc_dicts, "./output", "components_uc_dicts")
        for component_uc_dict in components_uc_dicts:
            component_name = component_uc_dict.get("name", "")
            component_ref = component_uc_dict.get("ref", "") 
            if ( component_ref == ""):
                continue
            
            if (component_ref not in components):
                components[component_ref] = Component(name=component_name, ref =component_ref,  threats={})

            uc = component_uc_dict.get("useCase", "")
            uc_name = uc.get("name", "")
            threats = uc.get("threats", [])

            for threat in threats:
                threat_name = threat.get("name", "")
                if ( threat_name == ""):
                    continue
                threat_desc = threat.get("desc", "")
                threat_ref = threat.get("ref", "")
                threatObj = Threat(name=threat_name, counterMeasures={}, ref=threat_ref, desc=threat_desc)
                threatObj.counterMeasures = convert_to_countermeasure_dict(threat.get("controls", {}), product_id, component_ref)
                components[component_ref].threats[threat_ref] = threatObj
        
        return components

def convert_to_countermeasure_dict(controls, product_id, component_id):
    countermeasures = dict()
    for control in controls:
        ref = control.get("ref", "")
        if (ref == ""):
            continue
        cm_details = get_countermeasure_details(product_id, component_id, ref)
        countermeasures[ref] = CounterMeasure(name=cm_details.get("name", ""),
                                            description=cm_details.get("desc", ""),
                                            ref=ref, library=cm_details.get("library", ""), 
                                            current_test_steps=get_countermeasure_current_test_steps(cm_details),
                                            genai_test=get_countermeasure_genai_test(cm_details),
                                            udts = get_udts_as_dict(cm_details),
                                            risk=cm_details.get("risk", -1))
    return countermeasures


def update_cm_genai_name_and_desc(product_id, component_id, control_ref, new_name, new_desc):
    Logger.log_info(f"Updating countermeasure name and desc for {product_id} - {component_id} - {control_ref}")
    #todo - followup.

def upadte_cm_test(product_id, component_id, control_ref, gen_ai_response):
    Logger.log_info(f"Updating test for {product_id} - {component_id} - {control_ref}")
    #print(new_test)
    #todo - followup.

def get_countermeasure_details(product_id, component_id, control_ref):
    url = base_url + f"api/v1/products/{product_id}/components/{component_id}/controls/{control_ref}"
    response = request_manager.SendRequestWithRetry(url, {}, {}, "get")
    #the countermeasure "desc" is important to understand it and to help create tests.
    if response.status_code == 200:
        return response.json()


def get_countermeasure_current_test(control_json):
    return control_json.get("test", {})

def get_udts_as_dict(control_json):
    udts = dict()
    for udt in control_json.get("udts", []):
        ref = udt.get("ref", "")
        if (ref != ""):
            udts[ref] = udt.get("value", "")
    return udts

def get_string_udt_from_details_json(control_json, udt_name):
    for udt in control_json.get("udts", []):
        ref = udt.get("ref", "")
        if (ref == udt_name):
            return udt.get("value", "")
    return ""

def get_countermeasure_genai_test(control_json):
    return get_string_udt_from_details_json(control_json, "genai_test")

def get_countermeasure_current_test_steps(control_json):
    res = str(get_countermeasure_current_test(control_json).get("steps", ""))
    if (res == ""):
        return []
    
    if (is_html_list_response(res)):
        return html_to_python_list(res)
    
    return [res]


def update_custom_field_in_product(product_ref, product_name, field_ref, value):
    url = base_url + f"api/v1/products/{product_ref}"
    body = {
        "name": product_name,
        "udts": [{
            "ref": field_ref,
            "value": value
        }]
    }
    response = request_manager.SendRequestWithRetry(url, method="put", body=body)
    if response.status_code == 200:
        return True
    return False




#Deprecated graph idea:
def build_components_graph(details_json):
    data_flows = details_json.get("dataflows", [])
    components = get_product_components_from_json(details_json)
    graph = dict()
    for data_flow in data_flows:
        source = data_flow.get("source", "")
        target = data_flow.get("target", "")
        if (source in components and target in components):
            source = components[source].get("name", "")
            target = components[target].get("name", "")
            if (source not in graph):
                graph[source] = []
            graph[source].append(target)
    return graph

def textually_present_graph(graph):
    res = ""
    for source in graph:
        res += f"{source} -> {list_to_html_list(graph[source])}\n"
    return res

def get_mx_graph_model(product_details):
    graph_schema = product_details.get("diagram", {}).get("schema", "")
    if (graph_schema != ""):
        return base64_decode(graph_schema)
    return ""

def get_textual_graph_plot(product_details):
    graph = build_components_graph(product_details)
    simple_graph_text = "graph data flows:\n"
    for key in graph:
        simple_graph_text += f"{key} -> {graph[key]}\n"

    return simple_graph_text

def get_product_diagram(product_id, save_at=""):
    url = base_url + f"api/v1/products/{product_id}/diagram/image"
    response = request_manager.SendRequestWithRetry(url, {}, {}, "get")
    if response.status_code == 200:
        with open(os.path.join(save_at, f"{product_id}.png"), 'wb') as f:
            f.write(response.content)
        return f"{product_id}_diagram.png"


def create_a_graph_folder_for_product(product_id):
    base_output_folder = get_output_folder(product_id)
    folder_name = f"graph"
    folder_name = os.path.join(base_output_folder, folder_name)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

def create_graph_information_for_product(product_id):
    save_at = create_a_graph_folder_for_product(product_id)
    get_product_diagram(product_id, save_at)
    
    product_details = get_product_details(product_id)
    graph_text = get_textual_graph_plot(product_details)
    with open(os.path.join(save_at, f"{product_id}_textual_graph_plot.txt"), 'w', encoding="utf-8") as f:
        f.write(graph_text)

    mx_graph_model = get_mx_graph_model(product_details)
    with open(os.path.join(save_at, f"{product_id}_mx_graph_model.txt"), 'w', encoding="utf-8") as f:
        f.write(mx_graph_model)
    
    return save_at