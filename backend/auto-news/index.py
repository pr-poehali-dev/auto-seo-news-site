import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime
import random
import requests

def get_random_image(category: str) -> str:
    '''Получает заглушку картинки (потом можно заменить)'''
    placeholders = {
        'IT': 'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=1200&h=800&fit=crop',
        'Игры': 'https://images.unsplash.com/photo-1511512578047-dfb367046420?w=1200&h=800&fit=crop',
        'Экономика': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=800&fit=crop',
        'Технологии': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&h=800&fit=crop',
        'Спорт': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1200&h=800&fit=crop',
        'Культура': 'https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=1200&h=800&fit=crop',
        'Мир': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&h=800&fit=crop'
    }
    
    return placeholders.get(category, 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1200&h=800&fit=crop')

def title_exists(cursor, title: str) -> bool:
    '''Проверяет, существует ли новость с таким заголовком'''
    cursor.execute(
        'SELECT COUNT(*) FROM t_p74494482_auto_seo_news_site.news WHERE title = %s',
        (title,)
    )
    result = cursor.fetchone()
    return result[0] > 0

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Генерирует 1 уникальную новость в случайной категории без дубликатов
    Args: event - dict с httpMethod, body
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
        
        all_categories = ['IT', 'Игры', 'Экономика', 'Технологии', 'Спорт', 'Культура', 'Мир']
        category = random.choice(all_categories)
        categories = [category]
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        news_created = 0
        
        for category in categories:
            max_attempts = 3
            
            for attempt in range(max_attempts):
                prompt = f"""Создай актуальную новость для категории "{category}" в формате JSON:
{{
  "title": "Уникальный заголовок новости (50-70 символов)",
  "excerpt": "Краткое описание сути новости (200-250 символов)",
  "content": "Подробный текст новости из 6-8 абзацев (3000-4500 символов). Каждый абзац из 4-6 предложений. Добавь цитаты, статистику, мнения экспертов.",
  "meta_title": "SEO заголовок с ключевыми словами (50-60 символов)",
  "meta_description": "SEO описание для поисковиков (150-160 символов)",
  "meta_keywords": "ключ1, ключ2, ключ3, ключ4, ключ5",
  "slug": "url-friendly-translit-slug"
}}

Требования:
- Новость должна быть актуальной на октябрь 2025 года
- ОБЯЗАТЕЛЬНО уникальный заголовок, не повторяющийся с другими
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
                            {'role': 'system', 'content': 'Ты опытный журналист топовых российских СМИ. Пишешь уникальные актуальные новости.'},
                            {'role': 'user', 'content': prompt}
                        ],
                        'temperature': 0.9,
                        'max_tokens': 5000
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
                        continue
                
                title = news_data.get('title', 'Новость')
                
                if title_exists(cur, title):
                    continue
                
                excerpt = news_data.get('excerpt', '')
                content = news_data.get('content', '')
                meta_title = news_data.get('meta_title', title)
                meta_description = news_data.get('meta_description', excerpt)
                meta_keywords = news_data.get('meta_keywords', category)
                slug = news_data.get('slug', '')
                
                image = get_random_image(category)
                
                published_time = datetime.now().isoformat()
                is_hot = random.choice([True, False, False, False])
                
                if not slug:
                    slug = title.lower().replace(' ', '-').replace(',', '').replace('.', '')[:100]
                
                insert_query = """
                    INSERT INTO t_p74494482_auto_seo_news_site.news (title, excerpt, content, category, image_url, published_at, is_hot, 
                                      meta_title, meta_description, meta_keywords, slug, author)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cur.execute(insert_query, (
                    title, excerpt, content, category, image, published_time, is_hot,
                    meta_title, meta_description, meta_keywords, slug, 'Редакция'
                ))
                news_created += 1
                break
        
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
                'message': f'Создано {news_created} уникальных новостей'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }