import {defineField, defineType} from 'sanity'

// Feste Termine im Vereinsjahr — Turniere, Versammlungen, Feste.
export const termin = defineType({
  name: 'termin',
  title: 'Termin',
  type: 'document',
  fields: [
    defineField({
      name: 'titel',
      title: 'Titel',
      type: 'string',
      description: 'Zum Beispiel „26. Birklauf“.',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'datum',
      title: 'Datum',
      type: 'date',
      options: {dateFormat: 'DD.MM.YYYY'},
      description:
        'Leer lassen, wenn der Termin kein festes Datum hat — dann steht an ' +
        'dieser Stelle die Uhrzeit-Angabe (etwa „jeden ersten Sonntag“).',
    }),
    defineField({
      name: 'zeit',
      title: 'Uhrzeit',
      type: 'string',
      description: 'Freier Text, zum Beispiel „ab 15:45 Uhr“.',
    }),
    defineField({name: 'ort', title: 'Ort', type: 'string'}),
    defineField({name: 'text', title: 'Beschreibung', type: 'text', rows: 4}),
    defineField({
      name: 'sortierung',
      title: 'Reihenfolge',
      type: 'number',
      initialValue: 0,
      description:
        'Nur nötig, wenn mehrere Termine ohne Datum in eine bestimmte Reihenfolge sollen. ' +
        'Datierte Termine ordnen sich von selbst.',
    }),
  ],
  orderings: [
    {title: 'Datum', name: 'datum', by: [{field: 'datum', direction: 'asc'}]},
    {title: 'Reihenfolge', name: 'sortierung', by: [{field: 'sortierung', direction: 'asc'}]},
  ],
  preview: {
    select: {title: 'titel', datum: 'datum', ort: 'ort', zeit: 'zeit'},
    prepare({title, datum, ort, zeit}) {
      const wann = datum ? new Date(datum).toLocaleDateString('de-DE') : zeit || 'ohne Datum'
      return {title, subtitle: [wann, ort].filter(Boolean).join(' · ')}
    },
  },
})
