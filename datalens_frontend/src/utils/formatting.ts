/**
 * Formatear moneda en formato peruano
 */
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('es-PE', {
    style: 'currency',
    currency: 'PEN',
    minimumFractionDigits: 2
  }).format(amount);
};

/**
 * Formatear fecha en formato legible
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('es-PE', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

/**
 * Formatear fecha corta
 */
export const formatShortDate = (dateString: string): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('es-PE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(date);
};

/**
 * Formatear número con separadores de miles
 */
export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('es-PE').format(num);
};

/**
 * Formatear porcentaje
 */
export const formatPercentage = (num: number): string => {
  return new Intl.NumberFormat('es-PE', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(num / 100);
};

/**
 * Formatear tiempo relativo (hace X tiempo)
 */
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.round(diffMs / 60000);
  const diffHours = Math.round(diffMs / 3600000);
  const diffDays = Math.round(diffMs / 86400000);

  if (diffMins < 60) {
    return `hace ${diffMins} minutos`;
  } else if (diffHours < 24) {
    return `hace ${diffHours} horas`;
  } else if (diffDays < 7) {
    return `hace ${diffDays} días`;
  } else {
    return formatShortDate(dateString);
  }
};

/**
 * Formatear tamaño de archivo
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Formatear duración en formato legible
 */
export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${remainingSeconds}s`;
  }
};

/**
 * Capitalizar primera letra
 */
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

/**
 * Truncar texto con elipsis
 */
export const truncate = (str: string, maxLength: number): string => {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength) + '...';
};

/**
 * Formatear stock status
 */
export const formatStockStatus = (current: number, min: number, max: number): {
  status: 'high' | 'medium' | 'low' | 'critical';
  message: string;
  color: string;
} => {
  const percentage = (current / max) * 100;
  
  if (current <= 0) {
    return {
      status: 'critical',
      message: 'Sin stock',
      color: 'text-red-600'
    };
  } else if (current <= min) {
    return {
      status: 'low',
      message: 'Stock bajo',
      color: 'text-orange-600'
    };
  } else if (percentage < 50) {
    return {
      status: 'medium',
      message: 'Stock medio',
      color: 'text-yellow-600'
    };
  } else {
    return {
      status: 'high',
      message: 'Stock alto',
      color: 'text-green-600'
    };
  }
};

/**
 * Formatear cambio porcentual con indicador
 */
export const formatChangePercentage = (current: number, previous: number): {
  percentage: number;
  formatted: string;
  trend: 'up' | 'down' | 'stable';
  color: string;
} => {
  if (previous === 0) {
    return {
      percentage: 0,
      formatted: '0%',
      trend: 'stable',
      color: 'text-gray-600'
    };
  }

  const percentage = ((current - previous) / previous) * 100;
  const trend = percentage > 0 ? 'up' : percentage < 0 ? 'down' : 'stable';
  const color = trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600';
  const sign = percentage > 0 ? '+' : '';
  
  return {
    percentage,
    formatted: `${sign}${percentage.toFixed(1)}%`,
    trend,
    color
  };
}; 