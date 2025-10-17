import { useEffect, useState } from 'react';
import { toast } from 'sonner';

const AUTO_NEWS_URL = 'https://functions.poehali.dev/110a45c8-d0f9-42fd-93e3-ffc41cad489b';
const INTERVAL_MS = 2 * 60 * 1000;

interface AutoNewsGeneratorProps {
  onNewsCreated: () => void;
}

const AutoNewsGenerator = ({ onNewsCreated }: AutoNewsGeneratorProps) => {
  const [isGenerating, setIsGenerating] = useState(false);

  const generateNews = async () => {
    if (isGenerating) return;
    
    setIsGenerating(true);
    
    try {
      const response = await fetch(AUTO_NEWS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        onNewsCreated();
      }
    } catch (error) {
      console.error('Ошибка генерации новости:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    generateNews();
    
    const interval = setInterval(() => {
      generateNews();
    }, INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  return null;
};

export default AutoNewsGenerator;