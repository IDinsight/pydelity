import starlight from "@astrojs/starlight";

// Every build, of the current tree or of a release, gets the version selector, the
// notice on older versions and the search-engine rule from the current checkout.
export default function versionedStarlight(options) {
  return starlight({
    ...options,
    components: {
      ...options.components,
      Banner: "./src/components/VersionBanner.astro",
      Head: "./src/components/VersionHead.astro",
      SocialIcons: "./src/components/VersionSocialIcons.astro",
    },
  });
}
