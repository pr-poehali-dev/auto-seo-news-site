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
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'DATABASE_URL not configured'})
            }
        
        categories = ['Политика', 'Экономика', 'Технологии', 'Спорт', 'Культура', 'Мир', 'Общество']
        
        body_data = json.loads(event.get('body', '{}'))
        count = body_data.get('count', 3)
        category = body_data.get('category', random.choice(categories))
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        news_created = 0
        
        templates = {
            'Политика': [
                {'title': 'Новые законопроекты обсудят в Госдуме', 'excerpt': 'Депутаты подготовили пакет важных инициатив для рассмотрения'},
                {'title': 'Политические эксперты прогнозируют важные изменения', 'excerpt': 'Аналитики оценивают возможные реформы в ближайшие месяцы'},
                {'title': 'Международная встреча лидеров завершилась соглашением', 'excerpt': 'Главы государств достигли консенсуса по ключевым вопросам'}
            ],
            'Экономика': [
                {'title': 'Экономисты прогнозируют рост ВВП в следующем квартале', 'excerpt': 'Позитивные показатели могут указывать на улучшение ситуации'},
                {'title': 'Центробанк объявил о новых мерах поддержки бизнеса', 'excerpt': 'Программа направлена на помощь малому и среднему предпринимательству'},
                {'title': 'Инвестиции в технологии достигли рекордных значений', 'excerpt': 'Венчурные фонды активно вкладывают в стартапы и инновации'}
            ],
            'Технологии': [
                {'title': 'Новый AI-помощник представлен российской компанией', 'excerpt': 'Разработка обещает революцию в сфере автоматизации бизнеса'},
                {'title': 'Квантовые компьютеры приближаются к массовому рынку', 'excerpt': 'Ученые сообщают о прорыве в области квантовых вычислений'},
                {'title': 'Российские программисты создали защищенный мессенджер', 'excerpt': 'Новое приложение гарантирует полную конфиденциальность переписки'}
            ],
            'Спорт': [
                {'title': 'Российские спортсмены готовятся к международным соревнованиям', 'excerpt': 'Сборная проводит интенсивные тренировки перед стартом чемпионата'},
                {'title': 'Футбольный клуб объявил о трансфере нового игрока', 'excerpt': 'Подписание контракта усилит состав команды на важные матчи'},
                {'title': 'Олимпийский чемпион поделился планами на новый сезон', 'excerpt': 'Спортсмен нацелен побить собственный рекорд в ближайших стартах'}
            ],
            'Культура': [
                {'title': 'Премьера нового российского фильма собрала полные залы', 'excerpt': 'Зрители высоко оценили работу режиссера и актерского состава'},
                {'title': 'Музей открывает выставку современного искусства', 'excerpt': 'Экспозиция представит работы талантливых российских художников'},
                {'title': 'Известный писатель анонсировал выход новой книги', 'excerpt': 'Роман обещает стать литературным событием года'}
            ],
            'Мир': [
                {'title': 'Международная организация приняла важную резолюцию', 'excerpt': 'Решение направлено на улучшение глобального сотрудничества'},
                {'title': 'Ученые обнаружили новый вид животных в тропиках', 'excerpt': 'Открытие поможет лучше понять биоразнообразие планеты'},
                {'title': 'Космическое агентство планирует запуск новой миссии', 'excerpt': 'Экспедиция займется исследованием дальних планет'}
            ],
            'Общество': [
                {'title': 'Социологи провели опрос о качестве жизни населения', 'excerpt': 'Исследование показало положительную динамику по ключевым показателям'},
                {'title': 'Благотворительный фонд запустил программу помощи', 'excerpt': 'Инициатива направлена на поддержку нуждающихся семей'},
                {'title': 'Волонтеры организовали масштабную акцию в городском парке', 'excerpt': 'Мероприятие объединило жителей разных возрастов'}
            ]
        }
        
        for i in range(count):
            category_templates = templates.get(category, templates['Общество'])
            template = random.choice(category_templates)
            
            title = template['title']
            excerpt = template['excerpt']
            
            content_paragraphs = [
                f"Сегодня стало известно о важном событии в сфере '{category}'. {excerpt}",
                f"По информации источников, это может стать значимым шагом для дальнейшего развития отрасли. Эксперты отмечают высокую актуальность данной темы.",
                f"Аналитики прогнозируют, что последствия этого события будут ощутимы в ближайшее время. Многие специалисты уже начали обсуждение возможных сценариев развития.",
                f"В заключение стоит отметить, что данная новость привлекла внимание широкой аудитории. Подробности будут известны в ближайшие дни."
            ]
            content = '\n\n'.join(content_paragraphs)
            
            news_data = {
                'title': title,
                'excerpt': excerpt,
                'content': content,
                'category': category,
                'meta_title': title,
                'meta_description': excerpt,
                'meta_keywords': f'{category}, новости, россия',
                'slug': title.lower().replace(' ', '-').replace(',', '').replace('.', '')[:100]
            }
            
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