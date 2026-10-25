import type { NextConfig } from 'next';
const staticExport=process.env.ACCESSPATH_STATIC_EXPORT==='true';
const config: NextConfig = {
  poweredByHeader: false,
  devIndicators: false,
  distDir: process.env.ACCESSPATH_BUILD_DIR || '.next',
  ...(staticExport ? {output: 'export' as const} : {}),
  logging: { incomingRequests: false, browserToTerminal: false },
  experimental: { proxyTimeout: 270000 },
  ...(!staticExport ? {async headers() {
    return [{source:'/:path*',headers:[
      {key:'Referrer-Policy',value:'no-referrer'},
      {key:'X-Content-Type-Options',value:'nosniff'},
      {key:'X-Frame-Options',value:'DENY'},
    ]}];
  },
  async rewrites() {
    const portal = process.env.PORTAL_URL || 'http://127.0.0.1:9314';
    return [
      { source: '/api/:path*', destination: `${process.env.API_URL || 'http://127.0.0.1:9313'}/api/:path*` },
      { source: '/forms/:path*', destination: `${portal}/forms/:path*` },
      { source: '/portal.css', destination: `${portal}/portal.css` },
      { source: '/portal.js', destination: `${portal}/portal.js` },
    ];
  }} : {}),
};
export default config;
