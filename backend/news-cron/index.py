'''
Business: Планировщик автогенерации новостей каждые 30 секунд
Args: event - dict с httpMethod (любой вызов запускает генерацию)
      context - object с request_id
Returns: HTTP response со статусом запуска генератора
'''

import json
import os
import requests
from typing import Dict, Any

AUTO_NEWS_URL = 'https://functions.poehali.dev/110a45c8-d0f9-42fd-93e3-ffc41cad489b'

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
        response = requests.get(AUTO_NEWS_URL, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'Генератор новостей запущен',
                    'generator_response': data
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
                    'message': f'Генератор вернул статус {response.status_code}',
                    'error': response.text
                }),
                'isBase64Encoded': False
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'type': type(e).__name__
            }),
            'isBase64Encoded': False
        }
