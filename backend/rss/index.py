import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime
import html

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Генерирует RSS-ленту для новостного агрегатора
    Args: event - dict с httpMethod
          context - object с request_id
    Returns: RSS XML feed со всеми новостями
    '''
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
            'body': ''
        }
    
    if method != 'GET':
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
        
        base_url = event.get('headers', {}).get('host', 'poehali.dev')
        if not base_url.startswith('http'):
            base_url = f'https://{base_url}'
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, title, excerpt, content, category, image_url, published_at, slug
            FROM news 
            ORDER BY published_at DESC
            LIMIT 50
        """)
        
        news_items = cur.fetchall()
        cur.close()
        conn.close()
        
        rss_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        rss_content += '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        rss_content += '  <channel>\n'
        rss_content += '    <title>НОВОСТИ 24 - Актуальные новости России и мира</title>\n'
        rss_content += f'    <link>{base_url}</link>\n'
        rss_content += '    <description>Последние новости дня: политика, экономика, технологии, спорт, культура. Оперативные новости России и мира 24/7</description>\n'
        rss_content += '    <language>ru</language>\n'
        rss_content += f'    <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>\n'
        rss_content += f'    <atom:link href="{base_url}/rss.xml" rel="self" type="application/rss+xml"/>\n'
        
        for item in news_items:
            news_id, title, excerpt, content, category, image_url, published_at, slug = item
            
            news_url = f'{base_url}/news/{news_id}'
            if slug:
                news_url = f'{base_url}/news/{slug}'
            
            pub_date = published_at.strftime('%a, %d %b %Y %H:%M:%S +0000') if published_at else datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            rss_content += '    <item>\n'
            rss_content += f'      <title>{html.escape(title or "Новость")}</title>\n'
            rss_content += f'      <link>{news_url}</link>\n'
            rss_content += f'      <description>{html.escape(excerpt or "")}</description>\n'
            rss_content += f'      <category>{html.escape(category or "Общество")}</category>\n'
            rss_content += f'      <pubDate>{pub_date}</pubDate>\n'
            rss_content += f'      <guid isPermaLink="true">{news_url}</guid>\n'
            rss_content += f'      <dc:creator>Редакция НОВОСТИ 24</dc:creator>\n'
            
            if image_url:
                rss_content += f'      <enclosure url="{html.escape(image_url)}" type="image/jpeg"/>\n'
            
            rss_content += '    </item>\n'
        
        rss_content += '  </channel>\n'
        rss_content += '</rss>'
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/rss+xml; charset=utf-8',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=1800'
            },
            'isBase64Encoded': False,
            'body': rss_content
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
