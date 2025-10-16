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
        openai_key = os.environ.get('OPENAI_API_KEY')
        if not openai_key:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'OPENAI_API_KEY not configured'})
            }
        
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'DATABASE_URL not configured'})
            }
        
        import openai
        openai.api_key = openai_key
        
        categories = ['Политика', 'Экономика', 'Технологии', 'Спорт', 'Культура', 'Мир', 'Общество']
        
        body_data = json.loads(event.get('body', '{}'))
        count = body_data.get('count', 3)
        category = body_data.get('category', random.choice(categories))
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        news_created = 0
        
        for i in range(count):
            prompt = f"""Создай новость для категории "{category}". 
Формат ответа строго JSON:
{{
  "title": "Заголовок новости (максимум 100 символов)",
  "excerpt": "Краткое описание новости (2-3 предложения, максимум 200 символов)",
  "content": "Полный текст новости (3-5 абзацев, максимум 1000 символов)",
  "category": "{category}"
}}

Новость должна быть актуальной, интересной и реалистичной. Пиши на русском языке."""

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты опытный журналист, создающий качественные новости."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            news_data = json.loads(response.choices[0].message.content)
            
            title = news_data.get('title', 'Новость')
            excerpt = news_data.get('excerpt', '')
            content = news_data.get('content', '')
            news_category = news_data.get('category', category)
            
            image = f"https://cdn.poehali.dev/projects/7ba64612-b62d-469b-894e-0aa0d8ed8b67/files/default-news-{random.randint(1,6)}.jpg"
            
            time_offset = random.randint(0, 48)
            published_time = (datetime.now() - timedelta(hours=time_offset)).isoformat()
            
            is_hot = random.choice([True, False, False])
            
            insert_query = """
                INSERT INTO news (title, excerpt, content, category, image, time, "isHot")
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(insert_query, (title, excerpt, content, news_category, image, published_time, is_hot))
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
