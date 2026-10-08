# Search discovery and publication

Updated 2026-10-08. These steps improve discoverability; they do not promise first place, indexing, or inclusion in AI answers.

The useful content is the code-review workflow, task cards, starter example, evaluations, and limits. Keep versions, examples, results, and installation claims consistent with the source. An illustrative prompt is not a trial.

## Publish and verify

1. Review the exact source and PR diff. Preserve recorded failed checks and host limits.
2. Confirm the repository remains public. Git history is included. This documentation change does not alter the skill core or its recorded evidence.
3. Publish the reviewed `docs/` folder with GitHub Pages from the default branch. Confirm the live homepage returns HTTP 200 without authentication and matches the reviewed HTML.
4. Set the repository's description, relevant topics, and homepage to the actual live site.
5. Verify the canonical URL, page title, description, visible content, and sitemap after publication. Keep sitemap dates tied to page content changes.
6. Check important links without depending on login or private repositories.

GitHub Pages project sites share a host. A `robots.txt` inside this project's subdirectory does not control the host-root crawler rules. This project does not add such a file.

## Owner webmaster checks

Use an owner-controlled Google Search Console URL-prefix property for the published project URL and a verified Bing Webmaster Tools property. Follow each provider's ownership-verification options; do not invent credentials or access.

Submit the project's `sitemap.xml` through the verified property and inspect the homepage. Check crawl access, indexing status, canonical selection, and reported queries. Track brand queries separately from “AI code review and verification” intent; search spelling, location, and personalization can produce different results. Check the provider's current AI-search eligibility settings where available.

A successful HTTP fetch or sitemap submission does not prove indexing or ranking. IndexNow is optional after an owner-controlled verification mechanism exists; this source change does not submit URLs or create a key.

## Practical guidance

Google and Bing both emphasize helpful, clear, public, crawlable content. No special AI text file is added here. Avoid hidden instructions for AI crawlers, keyword stuffing, fabricated reviews, and artificial mentions. Structured metadata must describe visible content.

- [Google technical requirements](https://developers.google.com/search/docs/essentials/technical)
- [Google AI-search guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- [Google robots.txt scope](https://developers.google.com/search/docs/crawling-indexing/robots/intro)
- [Bing Webmaster Guidelines](https://www.bing.com/webmasters/help/bing-webmaster-guidelines-30fba23a)
- [GitHub repository topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)
