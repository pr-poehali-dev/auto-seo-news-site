import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime
import random
import requests

def get_unsplash_image(category: str, unsplash_key: str) -> str:
    '''Получает случайное изображение из Unsplash API по категории'''
    search_queries = {
        'Политика': 'government politics official',
        'Экономика': 'business finance economy',
        'Технологии': 'technology innovation computer',
        'Спорт': 'sports stadium competition',
        'Культура': 'culture art museum',
        'Мир': 'world globe international',
        'Общество': 'society people community'
    }
    
    query = search_queries.get(category, 'news')
    
    try:
        response = requests.get(
            'https://api.unsplash.com/photos/random',
            params={
                'query': query,
                'orientation': 'landscape',
                'client_id': unsplash_key
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['urls']['regular']
    except:
        pass
    
    fallback_images = {
        'Политика': 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=1200',
        'Экономика': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200',
        'Технологии': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1200',
        'Спорт': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1200',
        'Культура': 'https://images.unsplash.com/photo-1499781350541-7783f6c6a0c8?w=1200',
        'Мир': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200',
        'Общество': 'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=1200'
    }
    
    return fallback_images.get(category, 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1200')

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Автоматически генерирует и добавляет актуальные новости в базу данных
    Args: event - dict с httpMethod, body (count - количество новостей)
          context - object с request_id, function_name
    Returns: HTTP response с количеством созданных новостей
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        db_url = os.environ.get('DATABASE_URL')
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        unsplash_key = os.environ.get('UNSPLASH_ACCESS_KEY')
        
        if not db_url or not api_key:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing configuration'})
            }
        
        categories = ['Политика', 'Экономика', 'Технологии', 'Спорт', 'Культура', 'Мир', 'Общество']
        
        body_data = json.loads(event.get('body', '{}'))
        total_count = body_data.get('count', 28)
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        news_created = 0
        news_per_category = total_count // len(categories)
        remainder = total_count % len(categories)
        
        for idx, category in enumerate(categories):
            count_for_category = news_per_category + (1 if idx < remainder else 0)
            
            for i in range(count_for_category):
                prompt = f"""Создай актуальную новость для категории "{category}" в формате JSON:
{{
  "title": "Интересный заголовок новости (50-70 символов)",
  "excerpt": "Краткое описание сути новости (150-180 символов)",
  "content": "Подробный текст новости из 3-4 абзацев (1000-1500 символов). Каждый абзац начинается с новой строки.",
  "meta_title": "SEO заголовок с ключевыми словами (50-60 символов)",
  "meta_description": "SEO описание для поисковиков (150-160 символов)",
  "meta_keywords": "ключ1, ключ2, ключ3, ключ4, ключ5",
  "slug": "url-friendly-translit-slug"
}}

Требования:
- Новость должна быть актуальной на октябрь 2025 года
- Реалистичные события и факты
- Естественный русский язык
- SEO-оптимизация"""

                response = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'deepseek/deepseek-chat',
                        'messages': [
                            {'role': 'system', 'content': 'Ты опытный журналист топовых российских СМИ. Пишешь актуальные новости.'},
                            {'role': 'user', 'content': prompt}
                        ],
                        'temperature': 0.8,
                        'max_tokens': 2500
                    },
                    timeout=30
                )
                
                response.raise_for_status()
                result = response.json()
                
                content_text = result['choices'][0]['message']['content'].strip()
                if content_text.startswith('```json'):
                    content_text = content_text[7:]
                if content_text.startswith('```'):
                    content_text = content_text[3:]
                if content_text.endswith('```'):
                    content_text = content_text[:-3]
                
                news_data = json.loads(content_text.strip())
                
                title = news_data.get('title', 'Новость')
                excerpt = news_data.get('excerpt', '')
                content = news_data.get('content', '')
                meta_title = news_data.get('meta_title', title)
                meta_description = news_data.get('meta_description', excerpt)
                meta_keywords = news_data.get('meta_keywords', category)
                slug = news_data.get('slug', '')
                
                if unsplash_key:
                    image = get_unsplash_image(category, unsplash_key)
                else:
                    image = get_unsplash_image(category, '')
                
                published_time = datetime.now().isoformat()
                is_hot = random.choice([True, False, False, False])
                
                if not slug:
                    slug = title.lower().replace(' ', '-').replace(',', '').replace('.', '')[:100]
                
                insert_query = """
                    INSERT INTO news (title, excerpt, content, category, image_url, published_at, is_hot, 
                                      meta_title, meta_description, meta_keywords, slug, author)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cur.execute(insert_query, (
                    title, excerpt, content, category, image, published_time, is_hot,
                    meta_title, meta_description, meta_keywords, slug, 'Редакция'
                ))
                news_created += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'isBase64Encoded': False,
            'body': json.dumps({
                'success': True,
                'created': news_created,
                'message': f'Создано {news_created} актуальных новостей'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
