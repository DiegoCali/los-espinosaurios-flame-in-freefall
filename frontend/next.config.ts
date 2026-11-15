import type { NextConfig } from 'next';

const isGhPages = process.env.GITHUB_PAGES === 'true';

const config: NextConfig = {
  ...(isGhPages ? { output: 'export' as const } : {}),
  trailingSlash: true,
  basePath: isGhPages ? '/los-espinosaurios-flame-in-freefall' : '',
  images: { unoptimized: true },
  env: { NEXT_PUBLIC_BASE_PATH: isGhPages ? '/los-espinosaurios-flame-in-freefall' : '' },
};
export default config;
