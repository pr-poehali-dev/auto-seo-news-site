import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime
import random
import requests

def get_unsplash_image(category: str) -> str:
    '''Получает случайное изображение из Unsplash Source API по категории'''
    search_queries = {
        'Политика': ['government', 'politics', 'official', 'parliament', 'flag'],
        'Экономика': ['business', 'finance', 'economy', 'chart', 'money'],
        'Технологии': ['technology', 'computer', 'innovation', 'ai', 'tech'],
        'Спорт': ['sports', 'stadium', 'competition', 'athlete', 'fitness'],
        'Культура': ['culture', 'art', 'museum', 'exhibition', 'painting'],
        'Мир': ['world', 'globe', 'international', 'earth', 'travel'],
        'Общество': ['society', 'people', 'community', 'city', 'crowd']
    }
    
    keywords = search_queries.get(category, ['news'])
    random_keyword = random.choice(keywords)
    random_seed = random.randint(1, 10000)
    
    return f'https://source.unsplash.com/1200x800/?{random_keyword}&sig={random_seed}'

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
                        raise
                
                title = news_data.get('title', 'Новость')
                excerpt = news_data.get('excerpt', '')
                content = news_data.get('content', '')
                meta_title = news_data.get('meta_title', title)
                meta_description = news_data.get('meta_description', excerpt)
                meta_keywords = news_data.get('meta_keywords', category)
                slug = news_data.get('slug', '')
                
                image = get_unsplash_image(category)
                
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