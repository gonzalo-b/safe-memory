'use client';
import { useEffect, useState } from 'react';
import { Icon } from '../vendor/memory-ds/react/Icon';
type Theme = 'system' | 'light' | 'dark';
export function ThemePicker() {
  const [theme, setTheme] = useState<Theme>('system');
  useEffect(() => {
    const saved = document.documentElement.dataset.theme;
    if (saved === 'light' || saved === 'dark') setTheme(saved);
  }, []);
  function choose(value: Theme) {
    setTheme(value);
    if (value === 'system') delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = value;
    try { if (value === 'system') localStorage.removeItem('m-theme'); else localStorage.setItem('m-theme', value); } catch { /* System preference remains available. */ }
  }
  return <div className="m-seg memory-theme" role="group" aria-label="Color theme">
    {(['system', 'light', 'dark'] as const).map(value => <button key={value} type="button" className="m-seg__item"
      aria-pressed={theme === value} aria-label={`${value[0].toUpperCase()}${value.slice(1)} theme`}
      title={`${value[0].toUpperCase()}${value.slice(1)} theme`} onClick={() => choose(value)}>
      <Icon name={value === 'system' ? 'monitor' : value === 'dark' ? 'moon' : 'sun'} />
    </button>)}
  </div>;
}
