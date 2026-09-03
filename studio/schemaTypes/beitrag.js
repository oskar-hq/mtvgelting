import {defineField, defineType} from 'sanity'

// Die Mitgliedsbeiträge. Aus ihnen rechnet sich auch der Satz „ab … € im
// Monat“ auf der Startseite.
export const beitrag = defineType({
  name: 'beitrag',
  title: 'Mitgliedsbeitrag',
  type: 'document',
  fields: [
    defineField({
      name: 'gruppe',
      title: 'Gruppe',
      type: 'string',
      description: 'Zum Beispiel „Kinder & Jugendliche bis 18 Jahre“.',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'kurz',
      title: 'Kurzbezeichnung',
      type: 'string',
      description: 'Für die Startseite, wo wenig Platz ist — zum Beispiel „Kinder“.',
    }),
    defineField({
      name: 'monat',
      title: 'Beitrag je Monat',
      type: 'string',
      description: 'Mit Währung, zum Beispiel „7,00 €“.',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'jahr',
      title: 'Beitrag je Jahr',
      type: 'string',
      description: 'Zum Beispiel „84,00 €“.',
    }),
    defineField({
      name: 'aktiv',
      title: 'Aktive Mitgliedschaft',
      type: 'boolean',
      initialValue: true,
      description:
        'Nur aktive Mitgliedschaften zählen für den Satz „ab … € im Monat“ auf der ' +
        'Startseite. Bei passiven oder fördernden Beiträgen abwählen, damit dort kein ' +
        'irreführender Preis steht.',
    }),
    defineField({
      name: 'sortierung',
      title: 'Reihenfolge',
      type: 'number',
      initialValue: 0,
      description: 'Kleinere Zahlen stehen weiter links.',
    }),
  ],
  orderings: [
    {title: 'Reihenfolge', name: 'sortierung', by: [{field: 'sortierung', direction: 'asc'}]},
  ],
  preview: {
    select: {title: 'gruppe', monat: 'monat', aktiv: 'aktiv'},
    prepare({title, monat, aktiv}) {
      return {title, subtitle: [monat, aktiv ? null : 'passiv'].filter(Boolean).join(' · ')}
    },
  },
})
