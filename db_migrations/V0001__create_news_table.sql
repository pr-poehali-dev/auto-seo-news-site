CREATE TABLE IF NOT EXISTS t_p74494482_auto_seo_news_site.news (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    excerpt TEXT,
    content TEXT,
    category VARCHAR(100) NOT NULL,
    image_url TEXT,
    source_url TEXT,
    author VARCHAR(200),
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_hot BOOLEAN DEFAULT FALSE,
    views_count INTEGER DEFAULT 0,
    slug VARCHAR(500) UNIQUE,
    meta_title VARCHAR(200),
    meta_description TEXT,
    meta_keywords TEXT
);

CREATE INDEX idx_news_category ON t_p74494482_auto_seo_news_site.news(category);
CREATE INDEX idx_news_published_at ON t_p74494482_auto_seo_news_site.news(published_at DESC);
CREATE INDEX idx_news_slug ON t_p74494482_auto_seo_news_site.news(slug);
CREATE INDEX idx_news_is_hot ON t_p74494482_auto_seo_news_site.news(is_hot);