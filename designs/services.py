from pathlib import Path
import requests
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

def generate_base44_image(prompt: str, size: str) -> str:
    size_mapping = {
        '80': 'small 80cc espresso cup, short and compact proportions, 60mm tall',
        '120': '120cc cortado cup, small compact proportions, 80mm tall',
        '220': 'standard 220cc latte cup, medium proportions, 105mm tall',
        '330': 'large 330cc cup, tall proportions, 120mm tall',
        '400': 'extra large 400cc cup, tall and slender proportions, 140mm tall',
    }

    size_desc = size_mapping.get(str(size), 'paper coffee cup')

    full_prompt = (
        f"Design for a disposable paper coffee cup ({size_desc}). {prompt}. "
        "The cup must be a paper cup with a visible paper texture and rolled rim, "
        "not plastic, glass, or ceramic. The cup shape and proportions must match this exact size. "
        "Wrap-around pattern for a cylindrical paper cup. Premium studio photography, "
        "soft lighting, cream background, no people."
    )

    url = "https://luma-craft-lab.base44.app/api/integrations/core/generate-image/"

    headers = {
        "api_key": env('BASE44_API_KEY'),
        "app_id": env('BASE44_APP_ID'),
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": full_prompt
    }
    try:
        print(f"--- Sending request to AI --- Prompt: {prompt}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # اگر ارور 4xx یا 5xx بود اکسپشن میده
        print("AI Response Status:", response.status_code)
        print("AI Response Text:", response.text)

        response.raise_for_status()
        return response.json().get('url')
    except Exception as e:
        print("=== [ERROR IN AI SERVICE] ===")
        print(str(e))
        raise e