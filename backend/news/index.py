'''
Business: API для управления новостями - получение списка, добавление, обновление и удаление
Args: event - dict с httpMethod, body, queryStringParameters, pathParams
      context - object с атрибутами request_id, function_name
Returns: HTTP response dict с новостями или статусом операции
'''

import json
import os
from typing import Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def create_slug(title: str) -> str:
    slug = title.lower()
    slug = ''.join(c if c.isalnum() or c.isspace() else '' for c in slug)
    slug = '-'.join(slug.split())
    return slug[:100]

def escape_string(value: str) -> str:
    return value.replace("'", "''")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if method == 'GET':
            params = event.get('queryStringParameters') or {}
            news_id = params.get('id')
            category = params.get('category')
            limit = int(params.get('limit', 50))
            offset = int(params.get('offset', 0))
            
            if news_id:
                query = f"""SELECT id, title, excerpt, content, category, image_url, 
                       author, published_at, is_hot, views_count, slug,
                       meta_title, meta_description 
                       FROM t_p74494482_auto_seo_news_site.news 
                       WHERE id = {int(news_id)}"""
                cursor.execute(query)
                news_item = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if not news_item:
                    return {
                        'statusCode': 404,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'error': 'News not found'}),
                        'isBase64Encoded': False
                    }
                
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
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'news': news_list, 'count': len(news_list)}),
                'isBase64Encoded': False
            }
        
        elif method == 'POST':
            body_data = json.loads(event.get('body', '{}'))
            
            title = body_data.get('title')
            excerpt = body_data.get('excerpt', '')
            content = body_data.get('content', '')
            category = body_data.get('category')
            image_url = body_data.get('image_url', '')
            author = body_data.get('author', 'Редакция')
            is_hot = body_data.get('is_hot', False)
            meta_title = body_data.get('meta_title') or title
            meta_description = body_data.get('meta_description') or excerpt
            meta_keywords = body_data.get('meta_keywords', '')
            
            if not title or not category:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Title and category are required'}),
                    'isBase64Encoded': False
                }
            
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
            
            escaped_title = escape_string(title)
            escaped_excerpt = escape_string(excerpt)
            escaped_content = escape_string(content)
            escaped_category = escape_string(category)
            escaped_image = escape_string(image_url)
            escaped_author = escape_string(author)
            escaped_slug = escape_string(slug_unique)
            escaped_meta_title = escape_string(meta_title)
            escaped_meta_desc = escape_string(meta_description)
            escaped_meta_keys = escape_string(meta_keywords)
            
            query = f"""INSERT INTO t_p74494482_auto_seo_news_site.news 
                   (title, excerpt, content, category, image_url, author, is_hot, slug,
                    meta_title, meta_description, meta_keywords)
                   VALUES ('{escaped_title}', '{escaped_excerpt}', '{escaped_content}', 
                           '{escaped_category}', '{escaped_image}', '{escaped_author}', 
                           {is_hot}, '{escaped_slug}', '{escaped_meta_title}', 
                           '{escaped_meta_desc}', '{escaped_meta_keys}')
                   RETURNING id, slug"""
            
            cursor.execute(query)
            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True, 
                    'id': result['id'],
                    'slug': result['slug']
                }),
                'isBase64Encoded': False
            }
        
        elif method == 'PUT':
            body_data = json.loads(event.get('body', '{}'))
            news_id = body_data.get('id')
            
            if not news_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'News ID is required'}),
                    'isBase64Encoded': False
                }
            
            update_fields = []
            
            for field in ['title', 'excerpt', 'content', 'category', 'image_url', 
                         'author', 'meta_title', 'meta_description', 'meta_keywords']:
                if field in body_data:
                    escaped_value = escape_string(str(body_data[field]))
                    update_fields.append(f"{field} = '{escaped_value}'")
            
            if 'is_hot' in body_data:
                update_fields.append(f"is_hot = {body_data['is_hot']}")
            
            if 'title' in body_data:
                slug = create_slug(body_data['title'])
                escaped_slug = escape_string(slug)
                update_fields.append(f"slug = '{escaped_slug}'")
            
            update_fields.append(f"updated_at = '{datetime.now().isoformat()}'")
            
            query = f"""UPDATE t_p74494482_auto_seo_news_site.news 
                       SET {', '.join(update_fields)}
                       WHERE id = {int(news_id)}"""
            
            cursor.execute(query)
            conn.commit()
            
            if cursor.rowcount == 0:
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
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif method == 'DELETE':
            params = event.get('queryStringParameters') or {}
            news_id = params.get('id')
            
            if not news_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'News ID is required'}),
                    'isBase64Encoded': False
                }
            
            query = f"DELETE FROM t_p74494482_auto_seo_news_site.news WHERE id = {int(news_id)}"
            cursor.execute(query)
            conn.commit()
            
            if cursor.rowcount == 0:
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
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'}),
                'isBase64Encoded': False
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
