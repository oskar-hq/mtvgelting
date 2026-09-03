import {defineField, defineType} from 'sanity'

// Kurze Meldungen. Die vier neuesten erscheinen auf der Startseite.
export const news = defineType({
  name: 'news',
  title: 'Meldung',
  type: 'document',
  fields: [
    defineField({
      name: 'titel',
      title: 'Überschrift',
      type: 'string',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'datum',
      title: 'Datum',
      type: 'date',
      options: {dateFormat: 'DD.MM.YYYY'},
      initialValue: () => new Date().toISOString().slice(0, 10),
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'kategorie',
      title: 'Rubrik',
      type: 'string',
      description: 'Ein Wort, zum Beispiel „Verein“ oder „Kinder“.',
    }),
    defineField({
      name: 'text',
      title: 'Text',
      type: 'text',
      rows: 6,
      validation: (regel) => regel.required(),
    }),
  ],
  orderings: [
    {title: 'Neueste zuerst', name: 'neu', by: [{field: 'datum', direction: 'desc'}]},
  ],
  preview: {
    select: {title: 'titel', datum: 'datum', kategorie: 'kategorie'},
    prepare({title, datum, kategorie}) {
      return {
        title,
        subtitle: [datum ? new Date(datum).toLocaleDateString('de-DE') : null, kategorie]
          .filter(Boolean)
          .join(' · '),
      }
    },
  },
})
