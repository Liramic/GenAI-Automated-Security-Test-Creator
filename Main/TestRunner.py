import os
import shutil
import subprocess
import json
import importlib.util
import sys
from tqdm import tqdm
from General.Logger import log_error

def install_requirements(folder):
    requirements_path = os.path.join(folder, 'requirements.txt')
    if os.path.exists(requirements_path):
        # don't mind errors and output:
        subprocess.check_call(['pip', 'install', '-r', requirements_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def copy_test_helpers(folder):
    test_helper_path = r"\General\TestHelpers.py"
    shutil.copy(test_helper_path, folder)

def run_test_code(folder):
    test_code_path = os.path.join(folder, 'test_code.py')
    if os.path.exists(test_code_path):
        # Add the folder containing TestHelpers.py to sys.path
        sys.path.append(os.path.abspath(folder))
        spec = importlib.util.spec_from_file_location("test_code", test_code_path)
        test_code = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_code)
        return test_code.run_test()
    return None, None, None

def save_results(results,save_at, product_id, component, threat, countermeasure):
    save_at = os.path.join(save_at, 'test_results.json')
    with open(save_at, 'w') as f:
        json.dump({
            'product_id': product_id,
            'component': component,
            'threat': threat,
            'countermeasure': countermeasure,
            'test_passed': results.get('test_passed', False),
            'log_for_each_step': results.get('log_for_each_step', []),
            'errors': results.get('errors', [])
        }, f, indent=4)

def run_all_tests(product_id):
    product_path = os.path.join(r"\TestsOutput", product_id)
    if os.path.isdir(product_path):
        for component in tqdm(os.listdir(product_path)):
            component_path = os.path.join(product_path, component)
            if os.path.isdir(component_path):
                for threat in os.listdir(component_path):
                    threat_path = os.path.join(component_path, threat)
                    if os.path.isdir(threat_path):
                        for countermeasure in os.listdir(threat_path):
                            countermeasure_path = os.path.join(threat_path, countermeasure)
                            if os.path.isdir(countermeasure_path):
                                try:
                                    copy_test_helpers(countermeasure_path)
                                    install_requirements(countermeasure_path)
                                    results = run_test_code(countermeasure_path)
                                    if results:
                                        save_results(results,countermeasure_path, product_id, component, threat, countermeasure)
                                except Exception as e:
                                    log_error(f"Error in running test for {countermeasure_path}")
                                    log_error(e)

if __name__ == "__main__":
    run_all_tests(r"product_1")