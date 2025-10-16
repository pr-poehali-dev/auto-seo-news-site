import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Генерирует динамический sitemap.xml для SEO
    Args: event - dict с httpMethod
          context - object с request_id
    Returns: XML sitemap со всеми новостями
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
            SELECT id, slug, published_at, updated_at 
            FROM news 
            ORDER BY published_at DESC
        """)
        
        news_items = cur.fetchall()
        cur.close()
        conn.close()
        
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{base_url}/</loc>\n'
        xml_content += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
        xml_content += '    <changefreq>hourly</changefreq>\n'
        xml_content += '    <priority>1.0</priority>\n'
        xml_content += '  </url>\n'
        
        for item in news_items:
            news_id, slug, published_at, updated_at = item
            
            news_url = f'{base_url}/news/{news_id}'
            if slug:
                news_url = f'{base_url}/news/{slug}'
            
            last_mod = updated_at or published_at
            if last_mod:
                last_mod_str = last_mod.strftime('%Y-%m-%d')
            else:
                last_mod_str = datetime.now().strftime('%Y-%m-%d')
            
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{news_url}</loc>\n'
            xml_content += f'    <lastmod>{last_mod_str}</lastmod>\n'
            xml_content += '    <changefreq>daily</changefreq>\n'
            xml_content += '    <priority>0.8</priority>\n'
            xml_content += '  </url>\n'
        
        xml_content += '</urlset>'
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/xml',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=3600'
            },
            'isBase64Encoded': False,
            'body': xml_content
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
