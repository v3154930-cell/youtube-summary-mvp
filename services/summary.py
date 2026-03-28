import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def generate_summary(transcript: str) -> str:
    """Generate brief summary of the transcript using OpenRouter"""
    if not transcript:
        return "Не удалось получить транскрипт для анализа."
    
    try:
        # Get API key from environment
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise Exception("Не настроен API-ключ LLM-сервиса.")
        
        # OpenRouter API endpoint
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Prepare request
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Prepare prompt for brief summary in Russian
        prompt = f"""Создай краткий пересказ видео по следующему транскрипту. 
        Ответ должен быть ТОЛЬКО на русском языке.
        Формат ответа:
        О чем ролик:
        <2-4 предложения>
        
        3 главные мысли:
        1. ...
        2. ...
        3. ...
        
        Короткий вывод:
        <1-2 предложения>
        
        Транскрипт: {transcript[:3000]}"""
        
        payload = {
            'model': 'openrouter/free',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }
        
        # Make request
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            if summary and summary.strip():
                return summary.strip()
            else:
                raise Exception("Не удалось сформировать краткий пересказ. Попробуйте снова.")
        elif response.status_code == 429:
            raise Exception("Превышен лимит запросов к LLM-сервису. Попробуйте позже.")
        elif response.status_code == 401:
            raise Exception("Не настроен API-ключ LLM-сервиса.")
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            raise Exception("Не удалось сформировать краткий пересказ. Попробуйте снова.")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e}")
        raise Exception("Не удалось сформировать краткий пересказ. Попробуйте снова.")
    except Exception as e:
        # Generic error
        error_msg = str(e)
        if "Не настроен API-ключ" in error_msg or "Превышен лимит" in error_msg or "Не удалось сформировать" in error_msg:
            raise Exception(error_msg)
        else:
            raise Exception("Не удалось сформировать краткий пересказ. Попробуйте снова.")
