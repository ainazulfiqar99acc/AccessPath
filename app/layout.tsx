import type { Metadata } from 'next';
import './midnight.css';
export const metadata: Metadata = {title:'AccessPath — Forms, made clearer', description:'Accessible guidance through fictional forms. Read the source, take one step at a time, and review before confirming.'};
export default function RootLayout({children}:{children:React.ReactNode}) {
  return <html lang="en"><body>{children}</body></html>;
}
