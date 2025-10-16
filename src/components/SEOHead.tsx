import { useEffect } from 'react';

interface SEOHeadProps {
  title?: string;
  description?: string;
  keywords?: string;
  ogImage?: string;
  ogType?: 'website' | 'article';
  publishedTime?: string;
  author?: string;
  canonicalUrl?: string;
}

export default function SEOHead({
  title = 'Новости России - Последние новости дня',
  description = 'Актуальные новости России и мира. Политика, экономика, спорт, технологии, культура. Свежие новости каждый день.',
  keywords = 'новости, россия, политика, экономика, спорт, технологии, культура, последние новости',
  ogImage = '/og-image.jpg',
  ogType = 'website',
  publishedTime,
  author = 'Редакция новостей',
  canonicalUrl
}: SEOHeadProps) {
  
  useEffect(() => {
    document.title = title;
    
    const metaTags = [
      { name: 'description', content: description },
      { name: 'keywords', content: keywords },
      { name: 'author', content: author },
      { property: 'og:title', content: title },
      { property: 'og:description', content: description },
      { property: 'og:image', content: ogImage },
      { property: 'og:type', content: ogType },
      { property: 'og:site_name', content: 'Новости России' },
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: title },
      { name: 'twitter:description', content: description },
      { name: 'twitter:image', content: ogImage },
      { name: 'robots', content: 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1' },
      { name: 'googlebot', content: 'index, follow' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' }
    ];
    
    if (publishedTime) {
      metaTags.push({ property: 'article:published_time', content: publishedTime });
    }
    
    metaTags.forEach(({ name, property, content }) => {
      const selector = name ? `meta[name="${name}"]` : `meta[property="${property}"]`;
      let meta = document.querySelector(selector) as HTMLMetaElement;
      
      if (!meta) {
        meta = document.createElement('meta');
        if (name) meta.name = name;
        if (property) meta.setAttribute('property', property);
        document.head.appendChild(meta);
      }
      
      meta.content = content;
    });
    
    if (canonicalUrl) {
      let link = document.querySelector('link[rel="canonical"]') as HTMLLinkElement;
      if (!link) {
        link = document.createElement('link');
        link.rel = 'canonical';
        document.head.appendChild(link);
      }
      link.href = canonicalUrl;
    }
    
  }, [title, description, keywords, ogImage, ogType, publishedTime, author, canonicalUrl]);
  
  return null;
}
