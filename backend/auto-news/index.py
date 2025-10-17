import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime, timedelta
import random
import requests
import base64
import time

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Автоматически генерирует и добавляет новости в базу данных
    Args: event - dict с httpMethod, body, queryStringParameters
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
        if not db_url:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'DATABASE_URL not configured'})
            }
        
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        if not api_key:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'DEEPSEEK_API_KEY not configured'})
            }
        
        categories = ['Политика', 'Экономика', 'Технологии', 'Спорт', 'Культура', 'Мир', 'Общество']
        
        body_data = json.loads(event.get('body', '{}'))
        count = body_data.get('count', 3)
        category = body_data.get('category', random.choice(categories))
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        news_created = 0
        
        for i in range(count):
            prompt = f"""Создай новость для категории "{category}" в формате JSON:
{{
  "title": "Заголовок (50-70 символов)",
  "excerpt": "Краткое описание (150-160 символов)",
  "content": "Полный текст (800-1200 символов, 3-5 абзацев)",
  "category": "{category}",
  "meta_title": "SEO заголовок (50-60 символов)",
  "meta_description": "SEO описание (150-160 символов)",
  "meta_keywords": "ключевое слово 1, ключевое слово 2, ключевое слово 3",
  "slug": "url-friendly-slug"
}}

Требования:
- Актуальная новость на русском языке
- SEO-оптимизация
- Структурированный контент
- Естественное вхождение ключевых слов"""

            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek/deepseek-chat',
                    'messages': [
                        {'role': 'system', 'content': 'Ты опытный SEO-журналист, создающий новости для топ-5 в поисковиках.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 2000
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            content_text = result['choices'][0]['message']['content']
            content_text = content_text.strip()
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
            news_category = news_data.get('category', category)
            meta_title = news_data.get('meta_title', title)
            meta_description = news_data.get('meta_description', excerpt)
            meta_keywords = news_data.get('meta_keywords', category)
            slug = news_data.get('slug', '')
            
            default_images = {
                'Политика': 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800',
                'Экономика': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800',
                'Технологии': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800',
                'Спорт': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800',
                'Культура': 'https://images.unsplash.com/photo-1499781350541-7783f6c6a0c8?w=800',
                'Мир': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800',
                'Общество': 'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800'
            }
            
            image = default_images.get(category, 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800')
            
            published_time = datetime.now().isoformat()
            
            is_hot = random.choice([True, False, False])
            
            if not slug:
                slug = title.lower().replace(' ', '-').replace(',', '').replace('.', '')[:100]
            
            insert_query = """
                INSERT INTO news (title, excerpt, content, category, image_url, published_at, is_hot, 
                                  meta_title, meta_description, meta_keywords, slug, author)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(insert_query, (
                title, excerpt, content, news_category, image, published_time, is_hot,
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
                'category': category,
                'message': f'Создано {news_created} новостей в категории {category}'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }