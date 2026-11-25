import React from 'react'
import { Icon } from './icons.jsx'

// Composants partagés : balisage et classes repris des vues Blade réelles
// d'Open Admin (widgets/box, widgets/info-box, grid/table, form, grid/quick-search).
// Les classes `*-xxx` conservées servent uniquement aux ajustements LyuX.

export function Card({ title, subtitle, actions, children, className = '', padded = true }) {
  return (
    <section className={`card box-info ${className}`}>
      {(title || actions) && (
        <div className="card-header with-border">
          <div>
            {title && <h3 className="card-title">{title}</h3>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="card-tools page-actions">{actions}</div>}
        </div>
      )}
      <div className={`card-body ${padded ? '' : 'p-0'}`}>{children}</div>
    </section>
  )
}

// Les titres de page sont déjà portés par le fil d'Ariane de la barre supérieure :
// il ne reste que les actions éventuelles, alignées à droite.
export function PageActions({ children }) {
  if (!children) return null
  return <div className="page-actions-bar">{children}</div>
}

export function StatCard({ icon, label, value, hint, tone = 'brand', trend }) {
  return (
    <div className={`card info-box stat-card tone-${tone}`}>
      <div className="card-body d-flex align-items-center">
        <div className={`icon float-start stat-icon tone-${tone}`}><Icon name={icon} size={19} /></div>
        <div className="inner stat-content">
          <p className="stat-label">{label}</p>
          <h3 className="stat-value">{value}</h3>
          {hint && <span className="stat-hint">{hint}</span>}
        </div>
      </div>
      {trend && <span className={`stat-trend ${trend.startsWith('-') ? 'negative' : ''}`}>{trend}</span>}
    </div>
  )
}

export function Badge({ tone = 'neutral', dot = false, children }) {
  return (
    <span className={`badge bg-${tone} badge-${tone}`}>
      {dot && <span className="badge-dot" />}
      {children}
    </span>
  )
}

export function Button({ variant = 'secondary', icon, size = 'md', children, className = '', ...rest }) {
  return (
    <button type="button" className={`btn btn-${variant} ${size === 'sm' ? 'btn-sm' : ''} ${className}`.trim()} {...rest}>
      {icon && <Icon name={icon} size={size === 'sm' ? 14 : 16} />}
      {children}
    </button>
  )
}

export function IconButton({ icon, label, className = '', ...rest }) {
  return (
    <button type="button" className={`btn btn-light btn-sm icon-btn ${className}`.trim()} title={label} aria-label={label} {...rest}>
      <Icon name={icon} size={16} />
    </button>
  )
}

export function Toolbar({ search, onSearch, placeholder = 'Rechercher…', filters, actions, children }) {
  return (
    <div className="toolbar container-fluid card-header no-border">
      <div className="row w-100 g-2 align-items-center">
        <div className="col-auto me-auto toolbar-left">
          {onSearch && (
            <div className="input-group input-group-sm grid-quick-search">
              <input
                type="text"
                className="form-control"
                value={search ?? ''}
                onChange={(event) => onSearch(event.target.value)}
                placeholder={placeholder}
                aria-label={placeholder}
              />
              <span className="input-group-btn">
                <button type="button" className="btn btn-light" aria-label={placeholder}><Icon name="search" size={14} /></button>
              </span>
            </div>
          )}
          {filters}
        </div>
        <div className="col-auto toolbar-right">
          {actions}
          {children}
        </div>
      </div>
    </div>
  )
}

export function Select({ value, onChange, options, label, className = '' }) {
  return (
    <label className={`select-field ${className}`}>
      {label && <span className="sr-only">{label}</span>}
      <select className="form-select form-select-sm" value={value} onChange={(event) => onChange(event.target.value)} aria-label={label}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  )
}

export function DataTable({ columns, rows, emptyLabel = 'Aucun résultat pour cette recherche.', onRowClick, dense = false, footer = true }) {
  const visibleRows = rows || []
  return (
    <div className="table-wrap table-responsive" autoComplete="off">
      <table className={`table grid-table table-sm table-hover select-table data-table ${dense ? 'dense' : ''} ${onRowClick ? 'clickable' : ''}`}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" style={{ width: column.width, textAlign: column.align || 'left' }}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {visibleRows.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>
                <EmptyState icon="search" title="Aucune donnée" description={emptyLabel} compact />
              </td>
            </tr>
          ) : (
            visibleRows.map((row, index) => (
              <tr
                key={row.id ?? index}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={row._className || ''}
              >
                {columns.map((column) => (
                  <td key={column.key} style={{ textAlign: column.align || 'left' }}>
                    {column.render ? column.render(row) : row[column.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
      {footer && (
        <div className="table-footer">
          <span>
            Affichage de <strong>{visibleRows.length}</strong> élément{visibleRows.length > 1 ? 's' : ''} sur{' '}
            <strong>{visibleRows.length}</strong>
          </span>
          <div className="pagination" aria-label="Pagination">
            <IconButton icon="chevronLeft" label="Page précédente" disabled />
            <button type="button" className="btn btn-light page-number active">1</button>
            <IconButton icon="chevronRight" label="Page suivante" disabled />
          </div>
        </div>
      )}
    </div>
  )
}

export function EmptyState({ icon = 'info', title, description, compact = false }) {
  return (
    <div className={`empty-state ${compact ? 'compact' : ''}`}>
      <div className="empty-icon"><Icon name={icon} size={compact ? 20 : 26} /></div>
      <strong>{title}</strong>
      {description && <p>{description}</p>}
    </div>
  )
}

export function Modal({ open, title, subtitle, onClose, children, footer, width = '520px' }) {
  if (!open) return null
  return (
    <div className="modal-overlay" onMouseDown={onClose}>
      <div
        className="lyux-modal card"
        style={{ maxWidth: width }}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <h3 className="card-title">{title}</h3>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <IconButton icon="close" label="Fermer" onClick={onClose} />
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}

export function Toggle({ checked, onChange, label, disabled = false }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      className={`toggle ${checked ? 'on' : ''}`}
      onClick={() => onChange(!checked)}
    >
      <span className="toggle-knob" />
    </button>
  )
}

export function Tabs({ tabs, active, onChange, className = '' }) {
  return (
    <div className={`nav nav-tabs tabs ${className}`} role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={active === tab.id}
          className={`nav-link tab ${active === tab.id ? 'active' : ''}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.icon && <Icon name={tab.icon} size={15} />}
          {tab.label}
          {tab.count != null && <span className="badge bg-light tab-count">{tab.count}</span>}
        </button>
      ))}
    </div>
  )
}

export function KeyValue({ label, value, mono = false }) {
  return (
    <div className="key-value">
      <span className="key-label">{label}</span>
      <span className={`key-value-text ${mono ? 'mono' : ''}`}>{value}</span>
    </div>
  )
}

export function ProgressBar({ value, tone = 'brand' }) {
  return (
    <div className="progress" role="progressbar" aria-valuenow={value} aria-valuemin="0" aria-valuemax="100">
      <div className={`progress-bar progress-fill tone-${tone}`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  )
}

export function Avatar({ name, tone = 'brand' }) {
  const initials = name
    .split(/[\s.-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
  return <span className={`avatar badge bg-${tone} tone-${tone}`}>{initials}</span>
}

export function FormField({ label, hint, children, className = '' }) {
  return (
    <label className={`form-field ${className}`}>
      <span className="form-label">{label}</span>
      {children}
      {hint && <span className="form-hint">{hint}</span>}
    </label>
  )
}

export function SettingRow({ icon, title, description, control }) {
  return (
    <div className="setting-row">
      <div className="setting-icon"><Icon name={icon} size={18} /></div>
      <div className="setting-copy">
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
      <div className="setting-control">{control}</div>
    </div>
  )
}

export function Timeline({ items }) {
  return (
    <ul className="timeline">
      {items.map((item) => (
        <li key={item.id}>
          <span className={`timeline-icon tone-${item.tone || 'brand'}`}><Icon name={item.icon || 'info'} size={14} /></span>
          <div>
            <div className="timeline-head">
              <strong>{item.title}</strong>
              <time>{item.time}</time>
            </div>
            <p>{item.detail}</p>
          </div>
        </li>
      ))}
    </ul>
  )
}
