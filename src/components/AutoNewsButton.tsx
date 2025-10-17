import { useState } from 'react';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

const AUTO_NEWS_URL = 'https://functions.poehali.dev/110a45c8-d0f9-42fd-93e3-ffc41cad489b';

interface AutoNewsButtonProps {
  onNewsCreated?: () => void;
}

const AutoNewsButton = ({ onNewsCreated }: AutoNewsButtonProps) => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const generateNews = async () => {
    setLoading(true);
    
    const { dismiss } = toast({
      title: "🚀 Генерация новостей",
      description: "Создаю 28 актуальных новостей с изображениями... Пожалуйста, подождите 2-3 минуты.",
      duration: Infinity,
    });
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 180000);
      
      const response = await fetch(AUTO_NEWS_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          count: 28
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      const data = await response.json();

      if (response.ok) {
        dismiss();
        toast({
          title: "✅ Готово!",
          description: `Добавлено ${data.created} новостей с картинками`,
          duration: 5000,
        });
        
        if (onNewsCreated) {
          setTimeout(onNewsCreated, 500);
        }
      } else {
        dismiss();
        toast({
          title: "❌ Ошибка",
          description: data.error || "Не удалось создать новости",
          variant: "destructive",
          duration: 5000,
        });
      }
    } catch (error) {
      dismiss();
      if (error instanceof Error && error.name === 'AbortError') {
        toast({
          title: "⏱️ Превышено время ожидания",
          description: "Генерация заняла слишком много времени. Попробуйте снова.",
          variant: "destructive",
          duration: 5000,
        });
      } else {
        toast({
          title: "❌ Ошибка",
          description: "Не удалось подключиться к серверу",
          variant: "destructive",
          duration: 5000,
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button 
      onClick={generateNews} 
      disabled={loading}
      className="gap-2"
    >
      {loading ? (
        <>
          <Icon name="Loader2" size={16} className="animate-spin" />
          Генерирую 28 новостей...
        </>
      ) : (
        <>
          <Icon name="Sparkles" size={16} />
          Создать 28 новостей
        </>
      )}
    </Button>
  );
};

export default AutoNewsButton;