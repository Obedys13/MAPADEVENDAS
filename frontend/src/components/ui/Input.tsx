import { forwardRef, InputHTMLAttributes, SelectHTMLAttributes } from 'react'
import { cn } from '../../utils/cn'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-xs font-medium text-gray-700 dark:text-gray-300">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'h-7 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800',
            'px-2 text-xs text-gray-900 dark:text-gray-100 placeholder-gray-400',
            'focus:outline-none focus:ring-1 focus:ring-brand-800 dark:focus:ring-accent-500 focus:border-brand-800 dark:focus:border-accent-500',
            'transition-colors',
            error && 'border-red-500 focus:ring-red-500',
            className
          )}
          {...props}
        />
        {error && <p className="text-2xs text-red-600">{error}</p>}
      </div>
    )
  }
)
Input.displayName = 'Input'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  options: { value: string; label: string }[]
  placeholder?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, id, options, placeholder, ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={selectId} className="text-xs font-medium text-gray-700 dark:text-gray-300">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={cn(
            'h-7 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800',
            'px-2 text-xs text-gray-900 dark:text-gray-100',
            'focus:outline-none focus:ring-1 focus:ring-brand-800 dark:focus:ring-accent-500 focus:border-brand-800',
            'transition-colors',
            error && 'border-red-500',
            className
          )}
          {...props}
        >
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        {error && <p className="text-2xs text-red-600">{error}</p>}
      </div>
    )
  }
)
Select.displayName = 'Select'
