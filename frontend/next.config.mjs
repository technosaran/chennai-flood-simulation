/** @type {import('next').NextConfig} */
const nextConfig = {
  // Keep production builds from replacing the running development server's files.
  distDir: process.env.NODE_ENV === 'development' ? '.next-dev' : '.next',
  // React-Leaflet 4 initializes its map in a ref callback. StrictMode's
  // development double mount can initialize the same DOM container twice.
  reactStrictMode: false,
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${process.env.BACKEND_API_URL || 'http://127.0.0.1:8000'}/api/:path*` }];
  },
};

export default nextConfig;
