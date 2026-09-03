import {defineField, defineType} from 'sanity'

// Das Raster auf der Startseite richtet sich von allein nach der Anzahl:
// weniger Sponsoren ergeben weniger Spalten, mehr ergeben weitere Zeilen.
export const sponsor = defineType({
  name: 'sponsor',
  title: 'Sponsor',
  type: 'document',
  fields: [
    defineField({
      name: 'name',
      title: 'Name',
      type: 'string',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'logo',
      title: 'Logo',
      type: 'image',
      description:
        'Ohne Logo erscheint der Name als Text. Am besten mit freigestelltem ' +
        'oder weißem Hintergrund.',
    }),
    defineField({
      name: 'url',
      title: 'Website',
      type: 'url',
      description: 'Optional. Das Logo wird dann verlinkt.',
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
    {title: 'Name', name: 'name', by: [{field: 'name', direction: 'asc'}]},
  ],
  preview: {select: {title: 'name', media: 'logo', subtitle: 'url'}},
})
