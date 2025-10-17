import { useState } from 'react';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';
import { Progress } from '@/components/ui/progress';

const AUTO_NEWS_URL = 'https://functions.poehali.dev/110a45c8-d0f9-42fd-93e3-ffc41cad489b';

interface AutoNewsButtonProps {
  onNewsCreated?: () => void;
}

const AutoNewsButton = ({ onNewsCreated }: AutoNewsButtonProps) => {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { toast } = useToast();

  const generateNews = async () => {
    setLoading(true);
    setProgress(0);
    
    const { dismiss } = toast({
      title: "🚀 Генерация новостей",
      description: (
        <div className="space-y-2">
          <p>Создаю 28 актуальных новостей...</p>
          <Progress value={0} className="w-full" id="news-progress" />
          <p className="text-sm text-muted-foreground">0 из 28</p>
        </div>
      ),
      duration: Infinity,
    });
    
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const newProgress = Math.min(prev + (100 / 28), 95);
        const progressElement = document.querySelector('#news-progress');
        if (progressElement) {
          progressElement.setAttribute('value', String(newProgress));
        }
        const currentCount = Math.floor((newProgress / 100) * 28);
        const textElement = document.querySelector('#news-progress')?.parentElement?.querySelector('.text-sm');
        if (textElement) {
          textElement.textContent = `${currentCount} из 28`;
        }
        return newProgress;
      });
    }, 4500);
    
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
      clearInterval(progressInterval);
      
      const data = await response.json();

      if (response.ok) {
        setProgress(100);
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
        clearInterval(progressInterval);
        dismiss();
        toast({
          title: "❌ Ошибка",
          description: data.error || "Не удалось создать новости",
          variant: "destructive",
          duration: 5000,
        });
      }
    } catch (error) {
      clearInterval(progressInterval);
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
      setProgress(0);
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
          Генерирую {Math.floor((progress / 100) * 28)}/28...
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
