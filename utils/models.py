MODEL_CONFIGS = {
    "mistral-7b": "mistralai/mistral-7b-instruct:free",
    "mistral-small-24b": "mistralai/mistral-small-24b-instruct-2501:free",
    
    "llama-3.3-8b": "meta-llama/llama-3.3-8b-instruct:free",
    "llama-3.2-3b": "meta-llama/llama-3.2-3b-instruct:free",
    
    "gemma-3-4b": "google/gemma-3-4b-it:free",
    "gemma-3-12b": "google/gemma-3-12b-it:free",
}

DEFAULT_MODEL_ID = MODEL_CONFIGS["mistral-7b"]

def get_model_id(model_name):
    return MODEL_CONFIGS.get(model_name, DEFAULT_MODEL_ID)

def list_available_models():
    return list(MODEL_CONFIGS.keys())

def get_model_family(model_name):
    if model_name.startswith("llama"):
        return "LLaMa"
    elif model_name.startswith("mistral"):
        return "Mistral"
    elif model_name.startswith("gemma"):
        return "Gemma"
    else:
        return "Unknown"
