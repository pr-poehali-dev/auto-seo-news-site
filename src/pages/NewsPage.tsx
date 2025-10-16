import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';

const API_URL = 'https://functions.poehali.dev/f9026a29-c4a5-479e-9712-5966f2b1a425';

const formatTime = (isoDate: string) => {
  if (!isoDate) return 'Недавно';
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  
  if (diffHours < 1) return 'Только что';
  if (diffHours < 24) return `${diffHours} ${diffHours === 1 ? 'час' : diffHours < 5 ? 'часа' : 'часов'} назад`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} ${diffDays === 1 ? 'день' : diffDays < 5 ? 'дня' : 'дней'} назад`;
};

const NewsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [news, setNews] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [relatedNews, setRelatedNews] = useState<any[]>([]);

  useEffect(() => {
    fetchNews();
  }, [id]);

  const fetchNews = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}?id=${id}`);
      if (!response.ok) throw new Error('News not found');
      const data = await response.json();
      setNews(data.news);
      
      if (data.news?.category) {
        const relatedResponse = await fetch(`${API_URL}?category=${encodeURIComponent(data.news.category)}&limit=3`);
        const relatedData = await relatedResponse.json();
        setRelatedNews(relatedData.news.filter((n: any) => n.id !== parseInt(id || '0')));
      }
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Icon name="Loader2" size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  if (!news) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">Новость не найдена</h1>
          <Button onClick={() => navigate('/')}>
            <Icon name="ArrowLeft" size={16} className="mr-2" />
            Вернуться на главную
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>{news.title || 'Новость'} | НОВОСТИ 24</title>
        <meta name="description" content={news.excerpt || ''} />
        <meta name="keywords" content={`${news.category?.toLowerCase() || 'новости'}, новости, россия, ${news.title || ''}`} />
        
        <meta property="og:type" content="article" />
        <meta property="og:title" content={news.title || 'Новость'} />
        <meta property="og:description" content={news.excerpt || ''} />
        <meta property="og:image" content={news.image || ''} />
        <meta property="article:published_time" content={news.time || ''} />
        <meta property="article:section" content={news.category || ''} />
        
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={news.title || 'Новость'} />
        <meta name="twitter:description" content={news.excerpt || ''} />
        <meta name="twitter:image" content={news.image || ''} />
        
        <link rel="canonical" href={window.location.href} />
        
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": news.title,
            "description": news.excerpt,
            "image": news.image,
            "datePublished": news.time,
            "author": {
              "@type": "Organization",
              "name": "НОВОСТИ 24"
            },
            "publisher": {
              "@type": "Organization",
              "name": "НОВОСТИ 24"
            },
            "articleSection": news.category,
            "articleBody": news.content
          })}
        </script>
      </Helmet>

      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border shadow-sm">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <button 
              onClick={() => navigate('/')}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity"
            >
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Icon name="Newspaper" className="text-white" size={24} />
              </div>
              <h1 className="text-2xl font-bold text-foreground">НОВОСТИ 24</h1>
            </button>

            <Button variant="ghost" onClick={() => navigate('/')}>
              <Icon name="ArrowLeft" size={16} className="mr-2" />
              На главную
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <article className="animate-fade-in">
          <div className="mb-6">
            <Badge className="mb-4">{news.category}</Badge>
            <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight">
              {news.title}
            </h1>
            <div className="flex items-center gap-4 text-muted-foreground">
              <div className="flex items-center gap-2">
                <Icon name="Clock" size={16} />
                {formatTime(news.time)}
              </div>
              {news.isHot && (
                <Badge variant="secondary" className="gap-1">
                  <Icon name="Flame" size={14} />
                  Горячее
                </Badge>
              )}
            </div>
          </div>

          {news.image && (
            <div className="mb-8 rounded-xl overflow-hidden">
              <img 
                src={news.image} 
                alt={news.title}
                className="w-full h-auto object-cover"
              />
            </div>
          )}

          <div className="prose prose-lg max-w-none mb-8">
            <p className="text-xl text-muted-foreground leading-relaxed mb-6">
              {news.excerpt}
            </p>
            {news.content && (
              <div className="text-foreground leading-relaxed whitespace-pre-line">
                {news.content}
              </div>
            )}
          </div>

          <div className="flex gap-2 py-6 border-y border-border">
            <Button variant="outline" size="sm">
              <Icon name="Share2" size={16} className="mr-2" />
              Поделиться
            </Button>
            <Button variant="outline" size="sm">
              <Icon name="Bookmark" size={16} className="mr-2" />
              Сохранить
            </Button>
          </div>
        </article>

        {relatedNews.length > 0 && (
          <section className="mt-12">
            <h2 className="text-2xl font-bold mb-6">Похожие новости</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {relatedNews.map((item) => (
                <div 
                  key={item.id}
                  onClick={() => navigate(`/news/${item.id}`)}
                  className="group cursor-pointer"
                >
                  <div className="relative overflow-hidden rounded-lg mb-3">
                    <img 
                      src={item.image} 
                      alt={item.title}
                      className="w-full h-40 object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  </div>
                  <h3 className="font-bold group-hover:text-primary transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {formatTime(item.time)}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-border mt-12 py-8">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>© 2024 НОВОСТИ 24. Все права защищены.</p>
        </div>
      </footer>
    </div>
  );
};

export default NewsPage;