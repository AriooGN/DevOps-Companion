/** @type {import('next').NextConfig} */
const flaskBackend =
  process.env.FLASK_BACKEND_URL || 'http://127.0.0.1:5000';

const nextConfig = {
  // reactStrictMode: false,
  async rewrites() {
    return [
      {
        source: '/flask/:path*',
        destination: `${flaskBackend.replace(/\/$/, '')}/:path*`,
      },
    ];
  },
  images: {
    
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'utfs.io',
        port: ''
      },
      {
        protocol: 'https',
        hostname: 'api.slingacademy.com',
        port: ''
      }
    ]
  },
  transpilePackages: ['geist']
};

module.exports = nextConfig;