import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime, timedelta
import random

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
        groq_key = os.environ.get('GROQ_API_KEY')
        if not groq_key:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'GROQ_API_KEY not configured'})
            }
        
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'DATABASE_URL not configured'})
            }
        
        from groq import Groq
        client = Groq(api_key=groq_key)
        
        categories = ['Политика', 'Экономика', 'Технологии', 'Спорт', 'Культура', 'Мир', 'Общество']
        
        body_data = json.loads(event.get('body', '{}'))
        count = body_data.get('count', 3)
        category = body_data.get('category', random.choice(categories))
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        news_created = 0
        
        for i in range(count):
            prompt = f"""Создай новость для категории "{category}" с SEO-оптимизацией. 
Формат ответа строго JSON:
{{
  "title": "Заголовок новости (50-70 символов, включи ключевые слова)",
  "excerpt": "Краткое описание (150-160 символов, продающее, с ключевыми словами)",
  "content": "Полный текст новости (3-5 абзацев, 800-1200 символов, структурированный)",
  "category": "{category}",
  "meta_title": "SEO заголовок (50-60 символов, с ключевыми словами)",
  "meta_description": "SEO описание (150-160 символов, призыв к действию)",
  "meta_keywords": "ключевое слово 1, ключевое слово 2, ключевое слово 3",
  "slug": "url-friendly-slug-na-russkom"
}}

Требования к SEO:
- Заголовок должен быть цепляющим и содержать главное ключевое слово
- Meta description должен побуждать кликнуть
- Keywords - 3-5 релевантных ключевых слов через запятую
- Slug - короткий, понятный URL на кириллице (5-7 слов максимум)
- Контент структурированный, с естественным вхождением ключевых слов

Пиши на русском языке."""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Ты опытный SEO-журналист, создающий новости для топ-5 в поисковиках. Твои новости всегда оптимизированы под поисковые запросы."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            news_data = json.loads(response.choices[0].message.content)
            
            title = news_data.get('title', 'Новость')
            excerpt = news_data.get('excerpt', '')
            content = news_data.get('content', '')
            news_category = news_data.get('category', category)
            meta_title = news_data.get('meta_title', title)
            meta_description = news_data.get('meta_description', excerpt)
            meta_keywords = news_data.get('meta_keywords', category)
            slug = news_data.get('slug', '')
            
            image = f"https://cdn.poehali.dev/projects/7ba64612-b62d-469b-894e-0aa0d8ed8b67/files/default-news-{random.randint(1,6)}.jpg"
            
            time_offset = random.randint(0, 48)
            published_time = (datetime.now() - timedelta(hours=time_offset)).isoformat()
            
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