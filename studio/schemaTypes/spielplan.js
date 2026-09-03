import {defineField, defineType} from 'sanity'

// Verweise auf die Ansetzungen der Verbände, unten auf der Termineseite.
export const spielplan = defineType({
  name: 'spielplan',
  title: 'Spielplan',
  type: 'document',
  fields: [
    defineField({
      name: 'name',
      title: 'Sportart',
      type: 'string',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'quelle',
      title: 'Verband',
      type: 'string',
      description: 'Zum Beispiel „Handballverband Schleswig-Holstein“.',
    }),
    defineField({
      name: 'url',
      title: 'Link',
      type: 'url',
      description: 'Ohne Link wird nur der Verband genannt.',
    }),
    defineField({
      name: 'sortierung',
      title: 'Reihenfolge',
      type: 'number',
      initialValue: 0,
    }),
  ],
  orderings: [
    {title: 'Reihenfolge', name: 'sortierung', by: [{field: 'sortierung', direction: 'asc'}]},
  ],
  preview: {select: {title: 'name', subtitle: 'quelle'}},
})
