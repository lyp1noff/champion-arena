import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["uk-UA", "en-GB"],
  defaultLocale: "uk-UA",
  localeDetection: false,
  localePrefix: {
    mode: "always",
    prefixes: {
      "en-GB": "/en",
      "uk-UA": "/ua",
    },
  },
});
