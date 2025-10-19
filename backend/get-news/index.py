'''
Business: Прокси для получения новостей напрямую из БД (обходит проблемы с CORS)
Args: event - dict с httpMethod, queryStringParameters (category, limit, offset, id)
      context - object с request_id
Returns: HTTP response с новостями из базы данных
'''

import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any

def escape_string(value: str) -> str:
    return value.replace("'", "''")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'GET':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    conn = None
    cursor = None
    
    try:
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Database not configured'}),
                'isBase64Encoded': False
            }
        
        params = event.get('queryStringParameters') or {}
        news_id = params.get('id')
        category = params.get('category')
        limit = int(params.get('limit', 50))
        offset = int(params.get('offset', 0))
        
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        if news_id:
            query = f"""SELECT id, title, excerpt, content, category, image_url, 
                   author, published_at, is_hot, views_count, slug,
                   meta_title, meta_description 
                   FROM t_p74494482_auto_seo_news_site.news 
                   WHERE id = {int(news_id)}"""
            cursor.execute(query)
            news_item = cursor.fetchone()
            
            if not news_item:
                cursor.close()
                conn.close()
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'News not found'}),
                    'isBase64Encoded': False
                }
            
            cursor.close()
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'news': {
                        'id': news_item['id'],
                        'title': news_item['title'],
                        'excerpt': news_item['excerpt'],
                        'content': news_item['content'],
                        'category': news_item['category'],
                        'image': news_item['image_url'],
                        'author': news_item['author'],
                        'time': news_item['published_at'].isoformat() if news_item['published_at'] else None,
                        'isHot': news_item['is_hot'],
                        'views': news_item['views_count'],
                        'slug': news_item['slug'],
                        'metaTitle': news_item['meta_title'],
                        'metaDescription': news_item['meta_description']
                    }
                }),
                'isBase64Encoded': False
            }
        
        if category and category != 'Главная':
            escaped_category = escape_string(category)
            query = f"""SELECT id, title, excerpt, content, category, image_url, 
                   author, published_at, is_hot, views_count, slug,
                   meta_title, meta_description 
                   FROM t_p74494482_auto_seo_news_site.news 
                   WHERE category = '{escaped_category}' 
                   ORDER BY published_at DESC 
                   LIMIT {limit} OFFSET {offset}"""
        else:
            query = f"""SELECT id, title, excerpt, content, category, image_url, 
                   author, published_at, is_hot, views_count, slug,
                   meta_title, meta_description 
                   FROM t_p74494482_auto_seo_news_site.news 
                   ORDER BY published_at DESC 
                   LIMIT {limit} OFFSET {offset}"""
        
        cursor.execute(query)
        news = cursor.fetchall()
        news_list = []
        
        for item in news:
            news_list.append({
                'id': item['id'],
                'title': item['title'],
                'excerpt': item['excerpt'],
                'content': item['content'],
                'category': item['category'],
                'image': item['image_url'],
                'author': item['author'],
                'time': item['published_at'].isoformat() if item['published_at'] else None,
                'isHot': item['is_hot'],
                'views': item['views_count'],
                'slug': item['slug'],
                'metaTitle': item['meta_title'],
                'metaDescription': item['meta_description']
            })
        
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache'
            },
            'body': json.dumps({'news': news_list, 'count': len(news_list)}),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e), 'type': type(e).__name__}),
            'isBase64Encoded': False
        }
