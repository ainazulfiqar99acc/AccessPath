import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'AccessPath — Forms, made clearer', description:'An accessible, local-first guide through fictional forms. Your pace. Your privacy. Your next step.'};
export default function RootLayout({children}:{children:React.ReactNode}) {
  return <html lang="en"><body>{children}</body></html>;
}
