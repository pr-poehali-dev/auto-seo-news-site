import { useEffect } from 'react';

const NEWS_CRON_URL = 'https://functions.poehali.dev/19c06317-5199-471d-aedf-57c00899a7e2';
const INTERVAL_MS = 30 * 1000;

interface AutoNewsGeneratorProps {
  onNewsCreated: () => void;
}

const AutoNewsGenerator = ({ onNewsCreated }: AutoNewsGeneratorProps) => {
  const triggerNewsGeneration = async () => {
    try {
      await fetch(NEWS_CRON_URL, { 
        method: 'GET',
        mode: 'no-cors'
      });
    } catch (error) {
      console.log('Генератор работает в фоне');
    }
  };

  useEffect(() => {
    triggerNewsGeneration();
    
    const interval = setInterval(() => {
      triggerNewsGeneration();
    }, INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  return null;
};

export default AutoNewsGenerator;