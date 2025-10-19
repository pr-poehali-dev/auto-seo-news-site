import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import AutoNewsGenerator from '@/components/AutoNewsGenerator';
import SEOHead from '@/components/SEOHead';
import StructuredData from '@/components/StructuredData';
import { newsData } from '@/data/newsData';
import NotificationStack from '@/components/NotificationStack';

const categories = [
  { name: 'Главная', icon: 'Home' },
  { name: 'IT', icon: 'Code' },
  { name: 'Игры', icon: 'Gamepad2' },
  { name: 'Криптовалюта', icon: 'Bitcoin' },
  { name: 'Экономика', icon: 'TrendingUp' },
  { name: 'Технологии', icon: 'Cpu' },
  { name: 'Спорт', icon: 'Trophy' },
  { name: 'Культура', icon: 'Palette' },
  { name: 'Мир', icon: 'Globe' }
];

const API_URL = 'https://functions.poehali.dev/d4635673-3760-41d9-9a96-ec32f8a0294c';

const formatTime = (isoDate: string) => {
  if (!isoDate) return 'Недавно';
  
  try {
    const date = new Date(isoDate);
    if (isNaN(date.getTime())) return 'Недавно';
    
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffMinutes < 1) return 'Только что';
    if (diffMinutes < 60) return `${diffMinutes} ${diffMinutes === 1 ? 'минуту' : diffMinutes < 5 ? 'минуты' : 'минут'} назад`;
    if (diffHours < 24) return `${diffHours} ${diffHours === 1 ? 'час' : diffHours < 5 ? 'часа' : 'часов'} назад`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} ${diffDays === 1 ? 'день' : diffDays < 5 ? 'дня' : 'дней'} назад`;
  } catch {
    return 'Недавно';
  }
};

const Index = () => {
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState('Главная');
  const [menuOpen, setMenuOpen] = useState(false);
  const [news, setNews] = useState<any[]>(newsData);
  const [loading, setLoading] = useState(false);
  const [expandedNewsId, setExpandedNewsId] = useState<number | null>(null);
  const [totalNewsCount, setTotalNewsCount] = useState(newsData.length);
  const [serverStatus, setServerStatus] = useState<string>('Новости загружены из кэша');
  const [apiAttempts, setApiAttempts] = useState(0);
  const [notifications, setNotifications] = useState<Array<{id: string, message: string, type: 'info' | 'success' | 'warning' | 'error', timestamp: Date}>>([]);

  const addNotification = (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
    const id = Date.now().toString();
    setNotifications(prev => [...prev, { id, message, type, timestamp: new Date() }]);
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  useEffect(() => {
    fetchNews();
    
    const pollInterval = setInterval(() => {
      fetchNewsSilently();
    }, 30000);
    
    return () => clearInterval(pollInterval);
  }, [activeCategory]);

  useEffect(() => {
    const filtered = activeCategory === 'Главная' 
      ? newsData 
      : newsData.filter(n => n.category === activeCategory);
    setNews(filtered);
  }, [activeCategory]);

  const fetchNews = async () => {
    setLoading(true);
    setApiAttempts(prev => prev + 1);
    try {
      const url = activeCategory === 'Главная' 
        ? API_URL 
        : `${API_URL}?category=${encodeURIComponent(activeCategory)}`;
      
      setServerStatus(`Попытка ${apiAttempts + 1}: Подключение к серверу...`);
      addNotification(`Подключение к серверу (попытка ${apiAttempts + 1})...`, 'info');
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        setServerStatus(`❌ Сервер недоступен (${response.status}). Показаны кэшированные новости`);
        addNotification(`Сервер недоступен (статус ${response.status}). Показаны кэшированные новости`, 'warning');
        const filtered = activeCategory === 'Главная' 
          ? newsData 
          : newsData.filter(n => n.category === activeCategory);
        setNews(filtered);
        setLoading(false);
        return;
      }
      
      const data = await response.json();
      
      if (data && Array.isArray(data.news)) {
        setNews(data.news);
        setTotalNewsCount(data.count || data.news.length);
        setServerStatus(`✅ Загружено ${data.news.length} новостей с сервера`);
        addNotification(`Успешно загружено ${data.news.length} новостей с сервера`, 'success');
      } else {
        const filtered = activeCategory === 'Главная' 
          ? newsData 
          : newsData.filter(n => n.category === activeCategory);
        setNews(filtered);
        setServerStatus('⚠️ Некорректный ответ сервера. Показаны кэшированные новости');
      }
    } catch (error) {
      console.error('Ошибка загрузки новостей:', error);
      setServerStatus(`❌ Ошибка подключения (попытка ${apiAttempts + 1}). Показаны кэшированные новости`);
      addNotification(`Ошибка подключения к серверу. Показаны кэшированные новости`, 'error');
      const filtered = activeCategory === 'Главная' 
        ? newsData 
        : newsData.filter(n => n.category === activeCategory);
      setNews(filtered);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchNewsSilently = async () => {
    try {
      const url = activeCategory === 'Главная' 
        ? API_URL 
        : `${API_URL}?category=${encodeURIComponent(activeCategory)}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        setServerStatus('🔄 Фоновое обновление: сервер недоступен');
        return;
      }
      
      const data = await response.json();
      
      if (data && Array.isArray(data.news)) {
        setNews(data.news);
        setTotalNewsCount(data.count || data.news.length);
        setServerStatus(`🔄 Обновлено: ${data.news.length} новостей`);
      }
    } catch (error) {
      console.log('Фоновое обновление пропущено');
    }
  };

  const filteredNews = news;

  const pageTitle = activeCategory === 'Главная' 
    ? 'НОВОСТИ 24 - Актуальные новости России и мира'
    : `${activeCategory} - Новости | НОВОСТИ 24`;
  
  const pageDescription = activeCategory === 'Главная'
    ? 'Последние новости дня: политика, экономика, технологии, спорт, культура. Оперативные новости России и мира 24/7'
    : `Актуальные новости категории ${activeCategory}. Свежие материалы, аналитика и репортажи 24/7`;

  const currentUrl = window.location.href;
  
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <AutoNewsGenerator onNewsCreated={fetchNews} />
      <NotificationStack notifications={notifications} onDismiss={dismissNotification} />
      <SEOHead 
        title={pageTitle}
        description={pageDescription}
        keywords={`новости, ${activeCategory.toLowerCase()}, россия, мир, онлайн, сегодня, свежие новости, последние новости`}
        ogType="website"
        canonicalUrl={currentUrl}
      />
      
      <StructuredData 
        type="WebSite"
        data={{
          name: 'НОВОСТИ 24',
          url: currentUrl.split('?')[0],
          description: 'Актуальные новости России и мира. Политика, экономика, спорт, технологии, культура. Свежие новости каждый день.'
        }}
      />
      <header className="sticky top-0 z-50 bg-white border-b border-border shadow-sm">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Icon name="Newspaper" className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">НОВОСТИ 24</h1>
                <p className="text-xs text-muted-foreground">{serverStatus}</p>
              </div>
            </div>

            <button 
              className="lg:hidden p-2"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Меню"
            >
              <Icon name={menuOpen ? "X" : "Menu"} size={24} />
            </button>

            <nav className="hidden lg:flex items-center gap-2">
              {categories.map((cat) => (
                <Button
                  key={cat.name}
                  variant={activeCategory === cat.name ? "default" : "ghost"}
                  onClick={() => setActiveCategory(cat.name)}
                  className="gap-2"
                >
                  <Icon name={cat.icon} size={16} />
                  {cat.name}
                </Button>
              ))}
            </nav>

            <div className="hidden lg:flex items-center gap-2">
              <Button variant="ghost" size="icon">
                <Icon name="Search" size={20} />
              </Button>
              <Button variant="ghost" size="icon">
                <Icon name="Bell" size={20} />
              </Button>
            </div>
          </div>

          {menuOpen && (
            <nav className="lg:hidden py-4 animate-fade-in">
              <div className="flex flex-col gap-2">
                {categories.map((cat) => (
                  <Button
                    key={cat.name}
                    variant={activeCategory === cat.name ? "default" : "ghost"}
                    onClick={() => {
                      setActiveCategory(cat.name);
                      setMenuOpen(false);
                    }}
                    className="gap-2 justify-start"
                  >
                    <Icon name={cat.icon} size={16} />
                    {cat.name}
                  </Button>
                ))}
              </div>
            </nav>
          )}
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 flex-1">
        <div className="mb-8 animate-slide-up">
          <h2 className="text-sm uppercase tracking-wider text-muted-foreground mb-4 font-semibold">
            {activeCategory === 'Главная' ? 'Последние новости' : activeCategory}
          </h2>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Icon name="Loader2" size={48} className="animate-spin text-primary" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredNews.map((newsItem, index) => (
              <Card 
                key={newsItem.id} 
                className="group overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer border-0 animate-slide-in-up"
                style={{ animationDelay: `${index * 50}ms` }}
                onClick={() => navigate(`/news/${newsItem.id}`)}
              >
                <div className="relative overflow-hidden bg-muted">
                  {newsItem.image ? (
                    <img 
                      src={newsItem.image} 
                      alt={newsItem.title}
                      className="w-full h-56 object-cover group-hover:scale-105 transition-transform duration-500"
                      onError={(e) => {
                        e.currentTarget.src = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800';
                      }}
                    />
                  ) : (
                    <div className="w-full h-56 flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5">
                      <Icon name="Image" size={48} className="text-muted-foreground" />
                    </div>
                  )}
                  {newsItem.isHot && (
                    <Badge className="absolute top-4 left-4 bg-primary text-white gap-1">
                      <Icon name="Flame" size={14} />
                      Горячее
                    </Badge>
                  )}
                  <div className="absolute top-4 right-4">
                    <Badge variant="secondary" className="bg-white/90 text-foreground backdrop-blur-sm">
                      {newsItem.category}
                    </Badge>
                  </div>
                </div>
                <CardContent className="p-6">
                  <script type="application/ld+json">
                    {JSON.stringify({
                      "@context": "https://schema.org",
                      "@type": "NewsArticle",
                      "headline": newsItem.title,
                      "description": newsItem.excerpt,
                      "image": newsItem.image,
                      "datePublished": newsItem.time,
                      "author": {
                        "@type": "Organization",
                        "name": "НОВОСТИ 24"
                      },
                      "publisher": {
                        "@type": "Organization",
                        "name": "НОВОСТИ 24"
                      },
                      "articleSection": newsItem.category
                    })}
                  </script>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                    <Icon name="Clock" size={14} />
                    {formatTime(newsItem.time)}
                  </div>
                  <h3 className="text-xl font-bold mb-3 group-hover:text-primary transition-colors leading-tight">
                    {newsItem.title}
                  </h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {newsItem.excerpt}
                  </p>
                  <div 
                    className="mt-4 p-0 h-auto font-semibold text-primary hover:bg-transparent group/btn inline-flex items-center cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/news/${newsItem.id}`);
                    }}
                  >
                    Читать далее
                    <Icon 
                      name="ArrowRight" 
                      size={16} 
                      className="ml-2 group-hover/btn:translate-x-1 transition-transform" 
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
        {!loading && filteredNews.length === 0 && (
          <div className="text-center py-20">
            <Icon name="FileX" size={64} className="mx-auto text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">Новостей не найдено</h3>
            <p className="text-muted-foreground">В этой категории пока нет публикаций</p>
          </div>
        )}
      </main>

      <footer className="bg-secondary text-secondary-foreground mt-auto">
        <div className="container mx-auto px-4 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                  <Icon name="Newspaper" className="text-white" size={24} />
                </div>
                <h3 className="text-xl font-bold">НОВОСТИ 24</h3>
              </div>
              <p className="text-sm opacity-80">
                Ваш главный источник актуальных новостей и аналитики
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Разделы</h4>
              <ul className="space-y-2 text-sm opacity-80">
                <li><a href="#" className="hover:opacity-100 transition-opacity">Политика</a></li>
                <li><a href="#" className="hover:opacity-100 transition-opacity">Экономика</a></li>
                <li><a href="#" className="hover:opacity-100 transition-opacity">Технологии</a></li>
                <li><a href="#" className="hover:opacity-100 transition-opacity">Спорт</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">О нас</h4>
              <ul className="space-y-2 text-sm opacity-80">
                <li><a href="#" className="hover:opacity-100 transition-opacity">Редакция</a></li>
                <li><a href="#" className="hover:opacity-100 transition-opacity">Контакты</a></li>
                <li><a href="#" className="hover:opacity-100 transition-opacity">Реклама</a></li>
                <li><a href="#" className="hover:opacity-100 transition-opacity">Вакансии</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Подписка</h4>
              <p className="text-sm opacity-80 mb-4">
                Получайте главные новости на почту
              </p>
              <div className="flex gap-2">
                <Button variant="secondary" size="icon" className="bg-white/10 hover:bg-white/20">
                  <Icon name="Mail" size={18} />
                </Button>
                <Button variant="secondary" size="icon" className="bg-white/10 hover:bg-white/20">
                  <Icon name="Rss" size={18} />
                </Button>
              </div>
            </div>
          </div>
          
          <div className="border-t border-white/10 mt-8 pt-8 text-center text-sm opacity-60">
            © 2024 НОВОСТИ 24. Все права защищены.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;