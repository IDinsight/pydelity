import { defineConfig } from "astro/config";
import starlight from "./versioning.mjs";

export default defineConfig({
  site: "https://idinsight.github.io",
  base: "/pydelity",
  integrations: [
    starlight({
      title: "pydelity",
      description:
        "Survey any PDF with Anthropic or OpenAI models: page numbers, rotation, writing direction and repeated lines, as JSON with a list of things to review.",
      favicon: "/favicon.svg",
      social: [
        {
          icon: "github",
          label: "GitHub repository",
          href: "https://github.com/IDinsight/pydelity",
        },
      ],
      // Inter is served from the site itself, so pages load no outside fonts.
      customCss: ["@fontsource-variable/inter", "./src/styles/custom.css"],
      components: {
        Sidebar: "./src/components/Sidebar.astro",
        SiteTitle: "./src/components/SiteTitle.astro",
      },
      sidebar: [
        {
          label: "Overview",
          slug: "index",
        },
        {
          label: "Reference",
          items: [{ autogenerate: { directory: "reference" } }],
        },
      ],
    }),
  ],
});
