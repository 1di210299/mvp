import React, { useState } from 'react';
import { useForm, FieldValues, Path } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z, ZodSchema } from 'zod';
import { Button } from './button';
import { Input } from './input';
import { Card, CardContent, CardHeader, CardTitle } from './card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';
import { Plus, Edit, Trash2, Save, X, Check, AlertTriangle } from './icons';

// Tipos para los campos del formulario
interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'number' | 'password' | 'tel' | 'select' | 'textarea';
  placeholder?: string;
  required?: boolean;
  options?: Array<{ value: string; label: string }>; // Para campos select
  validation?: {
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
  };
}

interface FormProps {
  fields: FormField[];
  onSubmit: (data: any) => void;
  initialData?: any;
  isLoading?: boolean;
  submitText?: string;
  className?: string;
  title?: string;
  isEditing?: boolean;
  onCancel?: () => void;
  schema?: ZodSchema<any>;
}

interface CRUDFormProps {
  title: string;
  fields: FormField[];
  onSubmit: (data: any) => void;
  initialData?: any;
  isEditing?: boolean;
  schema?: ZodSchema<any>;
  loading?: boolean;
  onCancel?: () => void;
}

interface CRUDActionsProps {
  onEdit?: () => void;
  onDelete?: () => void;
  onSave?: () => void;
  onCancel?: () => void;
  isEditing?: boolean;
  showEdit?: boolean;
  showDelete?: boolean;
  showSave?: boolean;
  showCancel?: boolean;
  loading?: boolean;
}

interface CreateButtonProps {
  onClick: () => void;
  text?: string;
  className?: string;
  disabled?: boolean;
  icon?: React.ReactNode;
}

// Función helper para crear reglas de validación nativas de react-hook-form
const getValidationRules = (field: FormField) => {
  const rules: any = {};
  
  if (field.required) {
    rules.required = `${field.label} es requerido`;
  }
  
  if (field.type === 'email') {
    rules.pattern = {
      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      message: 'Email inválido'
    };
  }
  
  if (field.type === 'number') {
    rules.valueAsNumber = true;
    if (field.validation?.min !== undefined) {
      rules.min = {
        value: field.validation.min,
        message: `Mínimo ${field.validation.min}`
      };
    }
    if (field.validation?.max !== undefined) {
      rules.max = {
        value: field.validation.max,
        message: `Máximo ${field.validation.max}`
      };
    }
  }
  
  if (field.validation?.minLength) {
    rules.minLength = {
      value: field.validation.minLength,
      message: `Mínimo ${field.validation.minLength} caracteres`
    };
  }
  
  if (field.validation?.maxLength) {
    rules.maxLength = {
      value: field.validation.maxLength,
      message: `Máximo ${field.validation.maxLength} caracteres`
    };
  }
  
  return rules;
};

// Helper function to safely use zodResolver
const getSafeResolver = (schema?: ZodSchema<any>) => {
  if (!schema) return undefined;
  
  try {
    return zodResolver(schema as any);
  } catch (error) {
    console.warn('Failed to create zodResolver, falling back to native validation:', error);
    return undefined;
  }
};

// Componente Form principal
export const Form: React.FC<FormProps> = ({
  fields,
  onSubmit,
  initialData = {},
  isLoading = false,
  submitText = 'Guardar',
  className = '',
  title,
  isEditing = false,
  onCancel,
  schema
}) => {
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Preparar valores por defecto
  const defaultValues = fields.reduce((acc, field) => {
    if (initialData[field.name] !== undefined) {
      acc[field.name] = initialData[field.name];
    } else if (field.type === 'number') {
      acc[field.name] = 0;
    } else {
      acc[field.name] = '';
    }
    return acc;
  }, {} as any);

  const formConfig: any = {
    defaultValues,
    mode: 'onChange'
  };

  // Use the safe resolver helper function
  const resolver = getSafeResolver(schema);
  if (resolver) {
    formConfig.resolver = resolver;
  }

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    setValue,
    watch
  } = useForm(formConfig);

  // Establecer valores iniciales cuando cambie initialData
  React.useEffect(() => {
    if (initialData && Object.keys(initialData).length > 0) {
      Object.keys(initialData).forEach((key) => {
        setValue(key, initialData[key]);
      });
    }
  }, [initialData, setValue]);

  const handleFormSubmit = async (data: any) => {
    try {
      await onSubmit(data);
      setSuccessMessage('Datos guardados exitosamente');
      
      // Limpiar mensaje después de 3 segundos
      setTimeout(() => {
        setSuccessMessage(null);
      }, 3000);
      
      if (!isEditing) {
        reset();
      }
    } catch (error) {
      console.error('Error submitting form:', error);
    }
  };

  const renderField = (field: FormField) => {
    const fieldError = errors[field.name];
    const hasError = !!fieldError;
    
    switch (field.type) {
      case 'select':
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={field.name} className="text-sm font-medium text-gray-700 mb-2 block">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <Select 
              value={watch(field.name) || ''} 
              onValueChange={(value) => setValue(field.name, value)}
            >
              <SelectTrigger className={hasError ? 'border-red-500' : ''}>
                <SelectValue placeholder={field.placeholder || `Seleccionar ${field.label.toLowerCase()}`} />
              </SelectTrigger>
              <SelectContent>
                {field.options?.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {/* Register the field for validation */}
            <input
              type="hidden"
              {...register(field.name, getValidationRules(field))}
            />
            {hasError && (
              <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                {fieldError.message as string}
              </p>
            )}
          </div>
        );
        
      case 'textarea':
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={field.name} className="text-sm font-medium text-gray-700 mb-2 block">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <textarea
              id={field.name}
              placeholder={field.placeholder}
              {...register(field.name, getValidationRules(field))}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none h-20 ${
                hasError ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {hasError && (
              <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                {fieldError.message as string}
              </p>
            )}
          </div>
        );
        
      default:
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={field.name} className="text-sm font-medium text-gray-700 mb-2 block">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <Input
              id={field.name}
              type={field.type}
              placeholder={field.placeholder}
              {...register(field.name, getValidationRules(field))}
              className={hasError ? 'border-red-500' : ''}
            />
            {hasError && (
              <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                {fieldError.message as string}
              </p>
            )}
          </div>
        );
    }
  };

  return (
    <div className={`animate-fade-in ${className}`}>
      {title && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">{title}</h2>
        </div>
      )}
      
      {successMessage && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md flex items-center gap-2 text-green-800">
          <Check className="h-4 w-4" />
          {successMessage}
        </div>
      )}

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        {/* Organizar campos en grid si hay más de 2 */}
        <div className={fields.length > 2 ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'}>
          {fields.map(renderField)}
        </div>
        
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting || isLoading}
            >
              <X className="w-4 h-4 mr-2" />
              Cancelar
            </Button>
          )}
          <Button
            type="submit"
            disabled={isSubmitting || isLoading}
            className="hover-lift"
          >
            {isSubmitting || isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Guardando...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {submitText}
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
};

// Componente CRUDForm con estilo de card
export const CRUDForm: React.FC<CRUDFormProps> = ({
  title,
  fields,
  onSubmit,
  initialData = {},
  isEditing = false,
  schema,
  loading = false,
  onCancel
}) => {
  return (
    <Card className="hover-lift">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {isEditing ? (
            <>
              <Edit className="h-5 w-5" />
              Editar {title}
            </>
          ) : (
            <>
              <Plus className="h-5 w-5" />
              Crear {title}
            </>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form
          fields={fields}
          onSubmit={onSubmit}
          initialData={initialData}
          isLoading={loading}
          isEditing={isEditing}
          onCancel={onCancel}
          schema={schema}
          submitText={isEditing ? 'Actualizar' : 'Crear'}
        />
      </CardContent>
    </Card>
  );
};

// Componente CRUDActions para botones de acción
export const CRUDActions: React.FC<CRUDActionsProps> = ({
  onEdit,
  onDelete,
  onSave,
  onCancel,
  isEditing = false,
  showEdit = true,
  showDelete = true,
  showSave = true,
  showCancel = true,
  loading = false
}) => {
  return (
    <div className="flex items-center gap-2">
      {!isEditing ? (
        <>
          {showEdit && onEdit && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onEdit}
              disabled={loading}
              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
            >
              <Edit className="w-4 h-4 mr-1" />
              Editar
            </Button>
          )}
          {showDelete && onDelete && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDelete}
              disabled={loading}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Eliminar
            </Button>
          )}
        </>
      ) : (
        <>
          {showSave && onSave && (
            <Button
              size="sm"
              onClick={onSave}
              disabled={loading}
              className="bg-green-600 hover:bg-green-700"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1"></div>
              ) : (
                <Save className="w-4 h-4 mr-1" />
              )}
              Guardar
            </Button>
          )}
          {showCancel && onCancel && (
            <Button
              variant="outline"
              size="sm"
              onClick={onCancel}
              disabled={loading}
            >
              <X className="w-4 h-4 mr-1" />
              Cancelar
            </Button>
          )}
        </>
      )}
    </div>
  );
};

// Componente CreateButton
export const CreateButton: React.FC<CreateButtonProps> = ({
  onClick,
  text = 'Crear Nuevo',
  className = '',
  disabled = false,
  icon
}) => {
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      className={`bg-blue-600 hover:bg-blue-700 text-white hover-lift ${className}`}
    >
      {icon || <Plus className="w-4 h-4 mr-2" />}
      {text}
    </Button>
  );
};