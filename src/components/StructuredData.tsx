import { useEffect } from 'react';

interface NewsArticleData {
  headline: string;
  description: string;
  image: string;
  datePublished: string;
  dateModified?: string;
  author: string;
  publisher: {
    name: string;
    logo: string;
  };
  url: string;
}

interface StructuredDataProps {
  type: 'NewsArticle' | 'WebSite';
  data: NewsArticleData | any;
}

export default function StructuredData({ type, data }: StructuredDataProps) {
  
  useEffect(() => {
    const scriptId = `structured-data-${type}`;
    let script = document.getElementById(scriptId) as HTMLScriptElement;
    
    if (!script) {
      script = document.createElement('script');
      script.id = scriptId;
      script.type = 'application/ld+json';
      document.head.appendChild(script);
    }
    
    let structuredData: any = {
      '@context': 'https://schema.org'
    };
    
    if (type === 'NewsArticle') {
      const newsData = data as NewsArticleData;
      structuredData = {
        ...structuredData,
        '@type': 'NewsArticle',
        headline: newsData.headline,
        description: newsData.description,
        image: newsData.image,
        datePublished: newsData.datePublished,
        dateModified: newsData.dateModified || newsData.datePublished,
        author: {
          '@type': 'Person',
          name: newsData.author
        },
        publisher: {
          '@type': 'Organization',
          name: newsData.publisher.name,
          logo: {
            '@type': 'ImageObject',
            url: newsData.publisher.logo
          }
        },
        url: newsData.url,
        mainEntityOfPage: {
          '@type': 'WebPage',
          '@id': newsData.url
        }
      };
    } else if (type === 'WebSite') {
      structuredData = {
        ...structuredData,
        '@type': 'WebSite',
        name: data.name,
        url: data.url,
        description: data.description,
        potentialAction: {
          '@type': 'SearchAction',
          target: `${data.url}/search?q={search_term_string}`,
          'query-input': 'required name=search_term_string'
        }
      };
    }
    
    script.textContent = JSON.stringify(structuredData);
    
    return () => {
      const oldScript = document.getElementById(scriptId);
      if (oldScript) {
        oldScript.remove();
      }
    };
  }, [type, data]);
  
  return null;
}
