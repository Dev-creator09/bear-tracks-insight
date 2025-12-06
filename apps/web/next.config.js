/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  transpilePackages: ['@bear-tracks/types'],
  eslint: {
    dirs: ['src'],
  },
};

module.exports = nextConfig;
