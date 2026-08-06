import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const summaryRow = z.object({
  problem: z.string(),
  cause: z.string(),
  fix: z.string(),
});

const articles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    publishedAt: z.coerce.date(),
    updatedAt: z.coerce.date().optional(),
    lastVerified: z.coerce.date().optional(),
    confidence: z.enum(['high', 'medium', 'kb']).default('high'),
    niche: z.string(),
    keywords: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    summary: z.array(summaryRow).default([]),
    sources: z.array(z.string()).default([]),
    related: z.array(z.string()).default([]),
    trendingScore: z.number().default(0),
  }),
});

export const collections = { articles };
