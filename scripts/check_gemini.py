"""Run manually after configuring a replacement key. Never prints credentials."""
import argparse
from google import genai
from app.config import settings

def main():
    p=argparse.ArgumentParser();p.add_argument('--list-models',action='store_true');args=p.parse_args()
    cfg=settings()
    if not cfg.gemini_api_key: raise SystemExit('Set GEMINI_API_KEY in .env first.')
    with genai.Client(api_key=cfg.gemini_api_key) as client:
        try:
            if args.list_models:
                for model in client.models.list():
                    if 'flash' in (model.name or ''): print(model.name)
            else:
                response=client.models.generate_content(model=cfg.gemini_model,contents='أجب بكلمة واحدة بالعربية: جاهز')
                print(response.text)
        except Exception as error:
            print('Gemini check failed. Verify key, model availability, quota, and network. HTTP code:',getattr(error,'code','unknown'))
            raise SystemExit(1) from None
if __name__=='__main__':main()
