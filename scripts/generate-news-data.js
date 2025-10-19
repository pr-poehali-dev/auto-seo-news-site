// Временный скрипт для генерации newsData.ts из SQL результата
// Данные взяты из perform_sql_query

const fs = require('fs');
const path = require('path');

const sqlData = [
{"id":102,"title":"Цифровой рубль к 2025 году: как изменится финансовая система России","excerpt":"К 2025 году цифровой рубль станет полноценной частью финансовой системы России. Банк России завершает пилотные проекты и готовится к массовому внедрению. Эксперты прогнозируют рост прозрачности операций и снижение издержек для бизнеса. Однако остаются вопросы по защите данных и адаптации населения.","content":"В октябре 2025 года Россия делает очередной шаг в сторону цифровизации экономики...","category":"Экономика","author":"Редакция","published_at":"2025-10-17T12:24:29.758313","is_hot":false,"views_count":0,"slug":"tsifrovoy-rubl-k-2025-kak-izmenitsya-finansovaya-sistema-rossii","meta_title":"Цифровой рубль в России: изменения финансовой системы к 2025","meta_description":"К 2025 году цифровой рубль станет частью финансовой системы России. Узнайте, какие изменения ждут бизнес и население."}
];

const newsData = sqlData.map(item => ({
  id: item.id,
  title: item.title,
  excerpt: item.excerpt,
  content: item.content,
  category: item.category,
  image: `https://picsum.photos/seed/${item.id}/800/400`,
  author: item.author,
  time: item.published_at,
  isHot: item.is_hot,
  views: item.views_count,
  slug: item.slug,
  metaTitle: item.meta_title,
  metaDescription: item.meta_description
}));

const tsContent = `export const newsData = ${JSON.stringify(newsData, null, 2)};
`;

const outputPath = path.join(__dirname, '..', 'src', 'data', 'newsData.ts');
fs.writeFileSync(outputPath, tsContent, 'utf-8');

console.log(`Generated ${newsData.length} news items to ${outputPath}`);
