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
        PageTitle: "./src/components/PageTitle.astro",
        Sidebar: "./src/components/Sidebar.astro",
        SiteTitle: "./src/components/SiteTitle.astro",
      },
      sidebar: [
        {
          label: "Overview",
          slug: "index",
        },
        {
          label: "Start here",
          items: ["start/install", "start/first-survey"],
        },
        {
          label: "FAQ",
          slug: "faq",
        },
        {
          label: "Need Help?",
          slug: "need-help",
        },
        {
          label: "Guides",
          items: [
            "guides/configuration",
            "guides/command-line",
            "guides/python",
            "guides/models-and-providers",
            "guides/costs",
            "guides/reruns",
            "guides/outputs",
          ],
        },
        {
          label: "Reference",
          items: [{ autogenerate: { directory: "reference" } }],
        },
        {
          label: "Contributing",
          items: [
            "contributing/development",
            "contributing/docs-site",
            "contributing/releases",
          ],
        },
      ],
    }),
  ],
});
