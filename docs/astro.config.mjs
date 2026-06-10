import mdx from "@astrojs/mdx";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "astro/config";

export default defineConfig({
  integrations: [mdx()],
  output: "static",
  vite: {
    plugins: [tailwindcss()]
  }
});
