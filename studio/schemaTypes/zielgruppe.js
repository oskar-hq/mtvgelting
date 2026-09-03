import {defineField, defineType} from 'sanity'

// Für wen ein Angebot gedacht ist — Kinder, Jugend, Erwachsene, Senioren.
export const zielgruppe = defineType({
  name: 'zielgruppe',
  title: 'Zielgruppe',
  type: 'document',
  fields: [
    defineField({
      name: 'name',
      title: 'Name',
      type: 'string',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'kennung',
      title: 'Kürzel für die Adresszeile',
      type: 'slug',
      options: {source: 'name', maxLength: 40},
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'sortierung',
      title: 'Reihenfolge',
      type: 'number',
      initialValue: 0,
      description: 'Kleinere Zahlen stehen weiter vorn.',
    }),
  ],
  orderings: [
    {title: 'Reihenfolge', name: 'sortierung', by: [{field: 'sortierung', direction: 'asc'}]},
  ],
  preview: {select: {title: 'name', subtitle: 'kennung.current'}},
})
