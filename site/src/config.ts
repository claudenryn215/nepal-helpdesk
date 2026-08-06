export const SITE = {
  name: 'NepalHelpDesk.np',
  shortName: 'NepalHelpDesk',
  description:
    'Step-by-step solutions for Nepal\'s most common tech problems: WorldLink & Vianet router setup, Nagarik App errors, eSewa/Khalti issues, .com.np domains, Daraz seller guides and more.',
  url: 'https://nepalhelpdesk.pages.dev',
  language: 'en',
  locale: 'en_NP',
};

export const CATEGORIES = [
  {
    slug: 'isp',
    label: 'Internet & ISP',
    blurb:
      'Router setup, WiFi troubleshooting, DNS and billing fixes for WorldLink, Vianet, Subisu and NT Fiber.',
  },
  {
    slug: 'e-gov',
    label: 'e-Governance',
    blurb:
      'Fixes for Nagarik App, NID, passport, driving license and NOC application errors.',
  },
  {
    slug: 'fintech',
    label: 'FinTech & Payments',
    blurb:
      'eSewa and Khalti wallet errors, merchant integration, and free .com.np domain registration.',
  },
  {
    slug: 'ecommerce',
    label: 'E-commerce & Selling',
    blurb:
      'Daraz seller dashboard, listing and payout guides for micro-merchants in Nepal.',
  },
  {
    slug: 'general',
    label: 'General Tech',
    blurb:
      'Phone, laptop and connectivity problems trending in Nepali online communities.',
  },
];

export const categoryLabel = (slug: string): string => {
  const found = CATEGORIES.find((c) => c.slug === slug);
  return found ? found.label : 'Guides';
};
