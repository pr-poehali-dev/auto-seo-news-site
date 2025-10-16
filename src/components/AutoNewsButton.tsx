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
    try {
      const response = await fetch(AUTO_NEWS_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          count: 3
        })
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "✅ Новости созданы!",
          description: `Добавлено ${data.created} новых новостей в категории ${data.category}`,
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
          Создаю новости...
        </>
      ) : (
        <>
          <Icon name="Sparkles" size={16} />
          Добавить новости
        </>
      )}
    </Button>
  );
};

export default AutoNewsButton;
