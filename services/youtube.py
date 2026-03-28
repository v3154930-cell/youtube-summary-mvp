import os
import requests


def get_transcript(video_url: str) -> str:
    api_key = os.getenv("SUPADATA_API_KEY")
    if not api_key:
        raise Exception("Не настроен API-ключ сервиса транскрипции.")

    endpoint = "https://api.supadata.ai/v1/transcript"
    headers = {
        "x-api-key": api_key,
    }
    params = {
        "url": video_url,
        "text": "true",
        "mode": "auto",
    }

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=60)

        if response.status_code == 200:
            data = response.json()
            content = data.get("content")
            if not content:
                raise Exception("Не удалось получить текст видео. Попробуйте другое видео.")
            return content

        if response.status_code == 202:
            raise Exception("Видео еще обрабатывается сервисом. Попробуйте снова через несколько секунд.")

        if response.status_code in (400, 404):
            raise Exception("Не удалось получить текст видео. Попробуйте другое видео.")

        if response.status_code == 401:
            raise Exception("Не настроен API-ключ сервиса транскрипции.")

        raise Exception("Произошла ошибка при обработке видео. Попробуйте снова.")

    except requests.RequestException:
        raise Exception("Произошла ошибка при обработке видео. Попробуйте снова.")
