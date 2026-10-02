import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from 'react';
import type { MemoryModule } from '../tokens';
import type { IconName } from '../icon-names';
import { Icon } from './Icon';
import { cx } from './cx';

export type ButtonVariant = 'primary' | 'tonal' | 'neutral' | 'ghost' | 'danger' | 'danger-solid';
export type ButtonSize = 'xs' | 'sm' | 'lg' | 'cta';
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant; size?: ButtonSize; block?: boolean; loading?: boolean; icon?: IconName; trailingIcon?: IconName;
}
const iconSizeFor = { xs: 14, sm: 14, lg: 16, cta: 18 } as const;

export function Button({ variant = 'neutral', size = 'sm', block, loading, icon, trailingIcon, className, children, disabled, type = 'button', ...rest }: ButtonProps) {
  return (
    <button type={type} disabled={disabled || loading} aria-busy={loading || undefined}
      className={cx('m-btn', `m-btn--${variant}`, size !== 'sm' && `m-btn--${size}`, block && 'm-btn--block', className)} {...rest}>
      {loading ? <span className="m-spinner" /> : icon ? <Icon name={icon} size={iconSizeFor[size]} /> : null}
      {children}
      {trailingIcon ? <Icon name={trailingIcon} size={iconSizeFor[size]} /> : null}
    </button>
  );
}

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: IconName; /** Required. Icon-only controls always carry a label. */ label: string;
  variant?: 'ghost' | 'fill' | 'primary'; size?: 'xs' | 'sm' | 'lg' | 'tap'; pressed?: boolean;
}
export function IconButton({ icon, label, variant = 'ghost', size = 'sm', pressed, className, type = 'button', ...rest }: IconButtonProps) {
  const px = size === 'xs' ? 14 : size === 'lg' ? 18 : size === 'tap' ? 20 : 16;
  return (
    <button type={type} aria-label={label} title={label} aria-pressed={pressed}
      className={cx('m-iconbtn', variant !== 'ghost' && `m-iconbtn--${variant}`, size !== 'sm' && `m-iconbtn--${size}`, className)} {...rest}>
      <Icon name={icon} size={px} />
    </button>
  );
}

export interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> { selected?: boolean; module?: MemoryModule; icon?: IconName; }
export function Chip({ selected, module, icon, className, children, type = 'button', ...rest }: ChipProps) {
  return (
    <button type={type} aria-pressed={!!selected} data-module={module} className={cx('m-chip', module && 'm-chip--module', className)} {...rest}>
      {icon ? <Icon name={icon} size={14} /> : null}{children}
    </button>
  );
}

export type BadgeTone = 'neutral' | 'ok' | 'bad' | 'warn' | 'accent' | 'module';
export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> { tone?: BadgeTone; module?: MemoryModule; }
export function Badge({ tone = 'neutral', module, className, ...rest }: BadgeProps) {
  return <span data-module={module} className={cx('m-badge', tone !== 'neutral' && `m-badge--${tone}`, className)} {...rest} />;
}

export interface DeltaBadgeProps { value: string; direction: 'up' | 'down' | 'flat'; look?: 'solid' | 'tint' | 'text'; }
/** A signed change. The value string carries its own sign: "+184", "-12%". */
export function DeltaBadge({ value, direction, look = 'solid' }: DeltaBadgeProps) {
  return <span className={cx('m-delta', 'm-num', direction !== 'flat' && `m-delta--${direction}`, look !== 'solid' && `m-delta--${look}`)}>{value}</span>;
}

export const Counter = ({ children }: { children: ReactNode }) => <span className="m-counter">{children}</span>;
export const Tag = ({ mono, children }: { mono?: boolean; children: ReactNode }) => <span className={cx('m-tag', mono && 'm-tag--mono')}>{children}</span>;
export const Kbd = ({ children }: { children: ReactNode }) => <kbd className="m-kbd">{children}</kbd>;

export interface AvatarProps { initials?: string; src?: string; alt?: string; size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; primary?: boolean; }
export function Avatar({ initials, src, alt = '', size = 'md', primary }: AvatarProps) {
  return <span className={cx('m-avatar', size !== 'md' && `m-avatar--${size}`, primary && 'm-avatar--primary')}>{src ? <img src={src} alt={alt} /> : initials}</span>;
}

export type DotTone = 'idle' | 'ok' | 'warn' | 'bad' | 'accent';
export const Dot = ({ tone = 'idle', live }: { tone?: DotTone; live?: boolean }) => <span className={cx('m-dot', tone !== 'idle' && `m-dot--${tone}`, live && 'm-dot--live')} />;

export const moduleIcon: Record<MemoryModule, IconName> = { purchase: 'bag', watch: 'tv', listen: 'headphones', photo: 'image', place: 'map-pin', health: 'heart-pulse' };
export const moduleLabel: Record<MemoryModule, string> = { purchase: 'Purchases', watch: 'Watching', listen: 'Listening', photo: 'Photos', place: 'Places', health: 'Health' };

export interface ModuleTileProps { module?: MemoryModule; icon?: IconName; size?: 'sm' | 'md' | 'lg'; accent?: boolean; }
/** The colour carrier of the system. Give it a module and it picks the hue and the icon. */
export function ModuleTile({ module, icon, size = 'md', accent }: ModuleTileProps) {
  const name = icon ?? (module ? moduleIcon[module] : 'block');
  return <span data-module={module} className={cx('m-mod', size !== 'md' && `m-mod--${size}`, accent && 'm-mod--accent')}><Icon name={name} size={size === 'sm' ? 14 : size === 'lg' ? 24 : 18} /></span>;
}

export const Spinner = () => <span className="m-spinner" role="status" aria-label="Loading" />;
