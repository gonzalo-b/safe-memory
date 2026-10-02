import type { Metadata } from 'next';
import { IconSprite } from '../vendor/memory-ds/react/IconSprite';
import './product.css';
export const metadata: Metadata = { title: 'Memory', description: 'Your private Photos memory.' };
const themeBootstrap = `(function(){try{var t=localStorage.getItem('m-theme');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t;}catch(e){}})();`;
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" suppressHydrationWarning><head>
    <meta name="color-scheme" content="dark light" />
    <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
    <link rel="stylesheet" href="/memory-ds/memory.css" />
  </head><body><IconSprite />{children}</body></html>;
}
