import {defineField, defineType} from 'sanity'

// Satzung, Ordnungen, Aufnahmeantrag und die Ausgaben des Sprachrohrs.
// Der Bereich bestimmt, wo das Dokument auf der Website auftaucht.
export const dokument = defineType({
  name: 'dokument',
  title: 'Dokument',
  type: 'document',
  fields: [
    defineField({
      name: 'bereich',
      title: 'Wo erscheint es?',
      type: 'string',
      options: {
        list: [
          {title: 'Satzungen & Ordnungen (Vereinsseite)', value: 'satzung'},
          {title: 'Sprachrohr (Vereinsseite)', value: 'sprachrohr'},
          {title: 'Aufnahmeantrag (Mitglied werden)', value: 'antrag'},
        ],
        layout: 'radio',
      },
      initialValue: 'satzung',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'titel',
      title: 'Titel',
      type: 'string',
      description: 'Zum Beispiel „Satzung“ oder „Sprachrohr 2026“.',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'datei',
      title: 'PDF',
      type: 'file',
      options: {accept: '.pdf'},
      description: 'Zum Austauschen einfach eine neue Datei hochladen.',
    }),
    defineField({
      name: 'url',
      title: 'Alternativer Link',
      type: 'url',
      description: 'Falls das Dokument woanders liegt, statt es hochzuladen.',
    }),
    defineField({
      name: 'beschreibung',
      title: 'Beschreibung',
      type: 'string',
      description:
        'Beschriftung des Links. Ohne Datei und ohne Link erscheint dieser Text als Hinweis ' +
        '— zum Beispiel „wird vom Verein bereitgestellt“.',
    }),
    defineField({
      name: 'sortierung',
      title: 'Reihenfolge',
      type: 'number',
      initialValue: 0,
    }),
  ],
  orderings: [
    {title: 'Bereich', name: 'bereich', by: [
      {field: 'bereich', direction: 'asc'},
      {field: 'sortierung', direction: 'asc'},
    ]},
  ],
  preview: {
    select: {title: 'titel', bereich: 'bereich', datei: 'datei.asset'},
    prepare({title, bereich, datei}) {
      const wo = {
        satzung: 'Satzungen & Ordnungen',
        sprachrohr: 'Sprachrohr',
        antrag: 'Aufnahmeantrag',
      }[bereich] || bereich
      return {title, subtitle: [wo, datei ? 'PDF vorhanden' : 'noch ohne PDF'].join(' · ')}
    },
  },
})
