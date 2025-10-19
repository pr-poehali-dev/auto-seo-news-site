import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';

const NEWS_CRON_URL = 'https://functions.poehali.dev/19c06317-5199-471d-aedf-57c00899a7e2';
const INTERVAL_MS = 30 * 1000;

interface AutoNewsGeneratorProps {
  onNewsCreated: () => void;
}

const AutoNewsGenerator = ({ onNewsCreated }: AutoNewsGeneratorProps) => {
  const [status, setStatus] = useState<string>('⏳ Запуск генератора...');
  const [lastGeneration, setLastGeneration] = useState<Date | null>(null);

  const triggerNewsGeneration = async () => {
    try {
      setStatus('🔄 Генерация новости...');
      
      const response = await fetch(NEWS_CRON_URL, { 
        method: 'GET',
        mode: 'cors'
      });

      if (response.ok) {
        setStatus('✅ Новость создана');
        setLastGeneration(new Date());
        setTimeout(() => onNewsCreated(), 1000);
      } else {
        setStatus('⚠️ Генератор недоступен');
      }
    } catch (error) {
      setStatus('❌ Ошибка генератора');
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

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <Badge variant="secondary" className="shadow-lg">
        {status}
        {lastGeneration && (
          <span className="ml-2 text-xs opacity-60">
            {new Date().getTime() - lastGeneration.getTime() < 60000 
              ? 'только что' 
              : `${Math.floor((new Date().getTime() - lastGeneration.getTime()) / 1000 / 60)} мин назад`}
          </span>
        )}
      </Badge>
    </div>
  );
};

export default AutoNewsGenerator;