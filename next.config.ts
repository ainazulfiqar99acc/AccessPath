import type { NextConfig } from 'next';
const config: NextConfig = {
  poweredByHeader: false,
  devIndicators: false,
  distDir: process.env.ACCESSPATH_BUILD_DIR || '.next',
  logging: { incomingRequests: false, browserToTerminal: false },
  async headers() {
    return [{source:'/:path*',headers:[
      {key:'Referrer-Policy',value:'no-referrer'},
      {key:'X-Content-Type-Options',value:'nosniff'},
      {key:'X-Frame-Options',value:'DENY'},
    ]}];
  },
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${process.env.API_URL || 'http://127.0.0.1:9313'}/api/:path*` }];
  },
};
export default config;
