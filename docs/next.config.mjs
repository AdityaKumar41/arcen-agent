import createMDX from "@next/mdx";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const withMDX = createMDX({
  extension: /\.mdx?$/
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  pageExtensions: ["js", "jsx", "md", "mdx", "ts", "tsx"],
  outputFileTracingRoot: __dirname,
  reactStrictMode: true,
  poweredByHeader: false
};

export default withMDX(nextConfig);
