import { resolve } from 'node:path';
import { defineConfig } from 'vitepress';

// The documentation is served below the test page: https://bennokr.github.io/linked-codebook/docs/
export default defineConfig({
  title: 'Linked Codebook',
  description: 'Read, write and check codebooks of tables whose variables are linked to concepts.',
  base: '/linked-codebook/docs/',
  outDir: resolve(import.meta.dirname, '../../site/dist/docs'),
  cleanUrls: true,
  lastUpdated: false,
  // The same anchors as on GitHub ("7.1 Language" is #71-language), so the links in the Markdown work in both places.
  markdown: {
    anchor: {
      slugify: (text: string) =>
        text
          .trim()
          .toLowerCase()
          .replace(/[^\p{L}\p{N}\s-]/gu, '')
          .replace(/\s+/g, '-'),
    },
  },
  themeConfig: {
    nav: [
      { text: 'Docs', link: '/' },
      { text: 'Test page', link: 'https://bennokr.github.io/linked-codebook/', target: '_self' },
      { text: 'GitHub', link: 'https://github.com/bennokr/linked-codebook' },
    ],
    sidebar: [
      {
        text: 'Use it',
        items: [
          { text: 'Overview', link: '/' },
          { text: 'Command line', link: '/cli' },
          { text: 'TypeScript', link: '/typescript' },
          { text: 'Python', link: '/python' },
          { text: 'Type profiling', link: '/type-profiling' },
          { text: 'Language detectors', link: '/language' },
        ],
      },
      {
        text: 'Reference',
        items: [
          { text: 'Specification', link: '/specification' },
          { text: 'Data model', link: '/data-model' },
          { text: 'Vocabulary', link: '/vocabulary' },
        ],
      },
      {
        text: 'Project',
        items: [
          { text: 'Rationale', link: '/rationale' },
          { text: 'Contributing', link: '/contributing' },
          { text: 'Quality baseline', link: '/quality-baseline' },
          { text: 'Changelog', link: '/changelog' },
        ],
      },
    ],
    socialLinks: [{ icon: 'github', link: 'https://github.com/bennokr/linked-codebook' }],
    editLink: {
      pattern: 'https://github.com/bennokr/linked-codebook/edit/main/docs/:path',
      text: 'Edit this page on GitHub',
    },
    search: { provider: 'local' },
    outline: [2, 3],
  },
});
