/**
 * Formatea un número a formato de moneda
 * @param {number} value - Valor a formatear
 * @param {string} locale - Configuración regional (por defecto: 'es-PE')
 * @param {string} currency - Moneda (por defecto: 'PEN')
 * @returns {string} Valor formateado como moneda
 */
export const formatCurrency = (value, locale = 'es-PE', currency = 'PEN') => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
};

/**
 * Formatea una fecha a formato legible
 * @param {string|Date} date - Fecha a formatear
 * @param {object} options - Opciones de formato
 * @returns {string} Fecha formateada
 */
export const formatDate = (date, options = {}) => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  const defaultOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  };
  
  const mergedOptions = { ...defaultOptions, ...options };
  
  return dateObj.toLocaleDateString('es-PE', mergedOptions);
};

/**
 * Trunca un texto si excede la longitud máxima
 * @param {string} text - Texto a truncar
 * @param {number} maxLength - Longitud máxima (por defecto: 50)
 * @returns {string} Texto truncado
 */
export const truncateText = (text, maxLength = 50) => {
  if (text && text.length > maxLength) {
    return `${text.substring(0, maxLength)}...`;
  }
  return text;
};

/**
 * Formatea un número de teléfono
 * @param {string} phone - Número de teléfono
 * @returns {string} Número de teléfono formateado
 */
export const formatPhone = (phone) => {
  if (!phone) return '';
  
  // Eliminar todo lo que no sea dígito
  const cleaned = phone.replace(/\D/g, '');
  
  // Asegurarse que es un número peruano
  if (cleaned.startsWith('51') && cleaned.length >= 11) {
    return `+${cleaned.substring(0, 2)} ${cleaned.substring(2, 5)} ${cleaned.substring(5, 8)} ${cleaned.substring(8)}`;
  }
  
  // Si no empieza con código de país, asumir formato local
  if (cleaned.length >= 9) {
    return `${cleaned.substring(0, 3)} ${cleaned.substring(3, 6)} ${cleaned.substring(6)}`;
  }
  
  return phone;
};

/**
 * Formatea un estado a un texto legible
 * @param {string} status - Estado a formatear
 * @returns {string} Estado formateado
 */
export const formatStatus = (status) => {
  const statusMap = {
    'pending': 'Pendiente',
    'processing': 'Procesando',
    'completed': 'Completado',
    'cancelled': 'Cancelado',
    'failed': 'Fallido'
  };
  
  return statusMap[status] || status;
};