import type { SVGProps } from 'react';
import type { IconName } from '../icon-names';
import { cx } from './cx';

export type IconSize = 14 | 16 | 18 | 20 | 24;
export interface IconProps extends Omit<SVGProps<SVGSVGElement>, 'name'> { name: IconName; size?: IconSize; }

/** Resolves against <IconSprite />, which must be rendered once near the top of <body>. */
export function Icon({ name, size = 16, className, ...rest }: IconProps) {
  return (
    <svg className={cx('m-icon', size !== 16 && `m-icon--${size}`, className)} aria-hidden="true" focusable="false" {...rest}>
      <use href={`#m-i-${name}`} />
    </svg>
  );
}
