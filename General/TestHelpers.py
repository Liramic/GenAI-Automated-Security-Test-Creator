import os
import json

def load_parameters_from_component(component_folder):
    component_env_file = os.path.join(component_folder, "component_environment.json")
    if os.path.exists(component_env_file):
        with open(component_env_file, 'r', encoding="utf-8") as f:
            component_env = json.load(f)
            return component_env.get("general_parameters", {})
    return {}

def load_parameters_for_test(current_dir = None):
    #assuming
    if not current_dir:
        current_dir = os.getcwd()
    #traverse two back:
    component_folder = os.path.join(current_dir, "..", "..")
    component_parameters = load_parameters_from_component(component_folder)

    #load test level parameters:
    test_parameters_file = os.path.join(current_dir, "test_parameters_filtered.json")
    test_parameters = {}
    try:
        if os.path.exists(test_parameters_file):
            with open(test_parameters_file, 'r', encoding="utf-8") as f:
                test_parameters = json.load(f)
        else:
            test_parameters_file = os.path.join(current_dir, "test_parameters.json")
            if os.path.exists(test_parameters_file):
                with open(test_parameters_file, 'r', encoding="utf-8") as f:
                    test_parameters = json.load(f)
            else:
                test_parameters = {}
    except Exception as e:
        print(f"Error in loading test parameters from {test_parameters_file}")
        print(e)

    #test parameters are more relevant to the test, so they will override the component parameters.
    if test_parameters:
        for param_key in test_parameters:
            component_parameters[param_key] = test_parameters[param_key]
    
    return component_parameters

if __name__ == "__main__":
    cm_directory = ""
    params = load_parameters_for_test(cm_directory)
    print(params["bucket_name"])
