import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

interface Notification {
  id: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: Date;
}

interface NotificationStackProps {
  notifications: Notification[];
  onDismiss: (id: string) => void;
}

const NotificationStack = ({ notifications, onDismiss }: NotificationStackProps) => {
  useEffect(() => {
    const timers = notifications.map(notification => {
      return setTimeout(() => {
        onDismiss(notification.id);
      }, 10000);
    });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [notifications, onDismiss]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'success': return 'CheckCircle2';
      case 'error': return 'XCircle';
      case 'warning': return 'AlertCircle';
      default: return 'Info';
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'success': return 'bg-green-50 border-green-200 text-green-800';
      case 'error': return 'bg-red-50 border-red-200 text-red-800';
      case 'warning': return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      default: return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      {notifications.map((notification) => (
        <Card 
          key={notification.id} 
          className={`p-3 ${getColor(notification.type)} animate-fade-in shadow-lg cursor-pointer hover:shadow-xl transition-shadow`}
          onClick={() => onDismiss(notification.id)}
        >
          <div className="flex items-start gap-3">
            <Icon name={getIcon(notification.type)} size={20} className="mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium break-words">{notification.message}</p>
              <p className="text-xs opacity-60 mt-1">
                {notification.timestamp.toLocaleTimeString('ru-RU')}
              </p>
            </div>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                onDismiss(notification.id);
              }}
              className="flex-shrink-0 hover:opacity-70"
            >
              <Icon name="X" size={16} />
            </button>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default NotificationStack;
