from langchain_openai.chat_models import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from AI.azure_api_access import get_api_headers
import time

class AI_ERROR:
    def __init__(self, error, e = None):
        self.error = error
        self.exception = e
    
    def __str__(self):
        return f"error: {self.error}, exception: {self.exception}"

def get_chat_model(is_gpt4o = False):
    headers = get_api_headers()
    deployment = headers["deployment names"][0] if is_gpt4o else headers["deployment names"][1]
    
    return AzureChatOpenAI( api_key         =    headers["AZURE_OPENAI_API_KEY"],
                        azure_endpoint      =    headers["AZURE_OPENAI_ENDPOINT"],
                        api_version         =    headers["OPENAI_API_VERSION"],
                        azure_deployment    =    deployment)


def simple_message(prompt, isRetry = False):
    chat_model = get_chat_model(is_gpt4o = True)
    hm = HumanMessage(content = prompt)
    try:
        response = chat_model([hm])
        if response.content is not None and len(response.content) > 0:
            return response.content
        elif isRetry:
            return AI_ERROR("empty_response")
    except Exception as e:
        if isRetry:
            return AI_ERROR("error_raised", e)
    
    #retry with maximum waiting time between requests.
    time.sleep(60)
    return simple_message(prompt, True)

def structered_output_message(prompt, structure, isRetry = False):
    model = get_chat_model( is_gpt4o = True )
    model_with_structure = model.with_structured_output(structure)
    hm = HumanMessage(content = prompt)
    try:
        response = model_with_structure.invoke(prompt)
        if response is not None:
            return response
        elif isRetry:
            return AI_ERROR("empty_response")
    except Exception as e:
        if isRetry:
            return AI_ERROR("error_raised", e)
    
    #retry once, wait 60:
    time.sleep(60)
    return structered_output_message(prompt, structure, True)

if __name__ == "__main__":
    s = simple_message("please conduct a research regarding facial mimicry using emg sensor and how to create an artifact removal algorithm. provide sources.")
    print(s)
