import { useEffect, useState, useRef } from 'react';

const AUTO_NEWS_URL = 'https://functions.poehali.dev/110a45c8-d0f9-42fd-93e3-ffc41cad489b';
const INTERVAL_MS = 2 * 60 * 1000;

interface AutoNewsGeneratorProps {
  onNewsCreated: () => void;
}

const AutoNewsGenerator = ({ onNewsCreated }: AutoNewsGeneratorProps) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [initialCheckDone, setInitialCheckDone] = useState(false);
  const silentMode = useRef(false);

  const generateNews = async (bulkCreate = false) => {
    if (isGenerating) return;
    
    setIsGenerating(true);
    
    try {
      const response = await fetch(AUTO_NEWS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bulk_create: bulkCreate })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && !silentMode.current) {
        onNewsCreated();
      }
    } catch (error) {
      console.error('Ошибка генерации новости:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const checkAndGenerateInitial = async () => {
    try {
      const response = await fetch('https://functions.poehali.dev/f9026a29-c4a5-479e-9712-5966f2b1a425');
      const data = await response.json();
      
      if (!data.news || data.news.length === 0) {
        await generateNews(true);
      } else {
        await generateNews(false);
      }
      
      setInitialCheckDone(true);
    } catch (error) {
      console.error('Ошибка проверки:', error);
      setInitialCheckDone(true);
    }
  };

  useEffect(() => {
    checkAndGenerateInitial();
    
    const interval = setInterval(() => {
      silentMode.current = true;
      generateNews();
    }, INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  return null;
};

export default AutoNewsGenerator;