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
    
    toast({
      title: "🚀 Генерация началась",
      description: "Создаю 28 актуальных новостей с изображениями. Это займет 2-3 минуты...",
    });
    
    try {
      const response = await fetch(AUTO_NEWS_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          count: 28
        })
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "✅ Готово!",
          description: `Добавлено ${data.created} новостей с уникальными картинками`,
        });
        
        if (onNewsCreated) {
          setTimeout(onNewsCreated, 500);
        }
      } else {
        toast({
          title: "❌ Ошибка",
          description: data.error || "Не удалось создать новости",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "❌ Ошибка",
        description: "Не удалось подключиться к серверу",
        variant: "destructive"
      });
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