'''
Business: Генератор новостей - создаёт новости по запросу или в фоновом режиме каждые 30 секунд
Args: event - dict с httpMethod, queryStringParameters (action=generate для ручной генерации)
      context - object с request_id, function_name
Returns: HTTP response с результатом генерации
'''

import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any
from datetime import datetime
import random
import requests

def get_random_image(category: str) -> str:
    random_num = random.randint(1, 999)
    return f'https://picsum.photos/seed/{random_num}/800/400'

def escape_string(value: str) -> str:
    return value.replace("'", "''")

def create_slug(title: str) -> str:
    slug = title.lower()
    slug = ''.join(c if c.isalnum() or c.isspace() else '' for c in slug)
    slug = '-'.join(slug.split())
    return slug[:100]

def title_exists(cursor, title: str) -> bool:
    escaped_title = escape_string(title)
    cursor.execute(
        f"SELECT COUNT(*) as cnt FROM t_p74494482_auto_seo_news_site.news WHERE title = '{escaped_title}'"
    )
    result = cursor.fetchone()
    return result['cnt'] > 0

def generate_single_news(cursor, conn, api_key: str) -> bool:
    all_categories = ['IT', 'Игры', 'Экономика', 'Технологии', 'Спорт', 'Культура', 'Мир', 'Криптовалюта']
    category = random.choice(all_categories)
    
    max_attempts = 3
    
    for attempt in range(max_attempts):
        prompt = f"""Создай новость категории "{category}" в JSON:
{{
  "title": "Заголовок (50-60 символов)",
  "excerpt": "Краткое описание (200-250 символов)",
  "content": "Подробный текст из 8-10 абзацев по 4-5 предложений (~1500 слов). Добавь цитаты, статистику, факты.",
  "meta_title": "SEO заголовок (50-60 символов)",
  "meta_description": "SEO описание (150-160 символов)",
  "meta_keywords": "ключ1, ключ2, ключ3, ключ4, ключ5"
}}

Требования: актуальность октябрь 2025, уникальный заголовок, естественный язык."""

        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek/deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': 'Ты опытный журналист топовых российских СМИ. Пишешь уникальные актуальные новости.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.9,
                'max_tokens': 3000
            },
            timeout=25
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
        
        content_text = content_text.strip()
        
        try:
            news_data = json.loads(content_text)
        except json.JSONDecodeError:
            first_brace = content_text.find('{')
            last_brace = content_text.rfind('}')
            if first_brace != -1 and last_brace != -1:
                content_text = content_text[first_brace:last_brace+1]
                news_data = json.loads(content_text)
            else:
                continue
        
        title = news_data.get('title', 'Новость')
        
        if title_exists(cursor, title):
            continue
        
        excerpt = news_data.get('excerpt', '')
        content = news_data.get('content', '')
        meta_title = news_data.get('meta_title', title)
        meta_description = news_data.get('meta_description', excerpt)
        meta_keywords = news_data.get('meta_keywords', category)
        
        slug = create_slug(title)
        slug_unique = slug
        counter = 1
        
        while True:
            escaped_slug = escape_string(slug_unique)
            cursor.execute(
                f"SELECT id FROM t_p74494482_auto_seo_news_site.news WHERE slug = '{escaped_slug}'"
            )
            if cursor.fetchone() is None:
                break
            slug_unique = f"{slug}-{counter}"
            counter += 1
        
        image = get_random_image(category)
        published_time = datetime.now().isoformat()
        is_hot = random.choice([True, False, False, False])
        
        escaped_title = escape_string(title)
        escaped_excerpt = escape_string(excerpt)
        escaped_content = escape_string(content)
        escaped_category = escape_string(category)
        escaped_image = escape_string(image)
        escaped_slug = escape_string(slug_unique)
        escaped_meta_title = escape_string(meta_title)
        escaped_meta_desc = escape_string(meta_description)
        escaped_meta_keys = escape_string(meta_keywords)
        escaped_time = escape_string(published_time)
        
        insert_query = f"""
            INSERT INTO t_p74494482_auto_seo_news_site.news 
            (title, excerpt, content, category, image_url, published_at, is_hot, 
             meta_title, meta_description, meta_keywords, slug, author)
            VALUES ('{escaped_title}', '{escaped_excerpt}', '{escaped_content}', 
                    '{escaped_category}', '{escaped_image}', '{escaped_time}', {is_hot},
                    '{escaped_meta_title}', '{escaped_meta_desc}', '{escaped_meta_keys}', 
                    '{escaped_slug}', 'Редакция')
        """
        
        cursor.execute(insert_query)
        conn.commit()
        return True
    
    return False

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        db_url = os.environ.get('DATABASE_URL')
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        
        if not db_url or not api_key:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing configuration'}),
                'isBase64Encoded': False
            }
        
        params = event.get('queryStringParameters') or {}
        action = params.get('action', 'auto')
        
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        if action == 'auto' or method == 'GET':
            success = generate_single_news(cursor, conn, api_key)
            
            cursor.close()
            conn.close()
            
            if success:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': True,
                        'message': 'Новость успешно создана'
                    }),
                    'isBase64Encoded': False
                }
            else:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'message': 'Не удалось создать уникальную новость'
                    }),
                    'isBase64Encoded': False
                }
        
        elif action == 'bulk':
            all_categories = ['IT', 'Игры', 'Экономика', 'Технологии', 'Спорт', 'Культура', 'Мир', 'Криптовалюта']
            news_created = 0
            
            for _ in range(len(all_categories) * 2):
                if generate_single_news(cursor, conn, api_key):
                    news_created += 1
            
            cursor.close()
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'created': news_created,
                    'message': f'Создано {news_created} новостей'
                }),
                'isBase64Encoded': False
            }
        
        else:
            cursor.close()
            conn.close()
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Invalid action'}),
                'isBase64Encoded': False
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e), 'type': type(e).__name__}),
            'isBase64Encoded': False
        }
