export const categories = ['all', 'combustion', 'spread', 'extinction', 'smoke'] as const;
export type Category = typeof categories[number];
export const studyCategories: Record<string, readonly Category[]> = {
  acme: ['combustion'],
  'bass-ii': ['combustion', 'spread', 'extinction'],
  'saffire-ii': ['combustion', 'smoke'],
  'same-r': ['smoke'],
  flex: ['combustion', 'extinction'],
};
export const matchesCategory = (slug: string, category: Category) => category === 'all' || studyCategories[slug]?.includes(category) === true;
