import {defineField, defineType} from 'sanity'

// Die Bereiche, nach denen sich das Sportangebot filtern lässt.
export const kategorie = defineType({
  name: 'kategorie',
  title: 'Bereich',
  type: 'document',
  fields: [
    defineField({
      name: 'name',
      title: 'Name',
      type: 'string',
      description: 'Zum Beispiel „Ballsport“ oder „Sport für Kinder“.',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'kennung',
      title: 'Kürzel für die Adresszeile',
      type: 'slug',
      options: {source: 'name', maxLength: 40},
      description:
        'Wird automatisch aus dem Namen gebildet. Es steht im Link, mit dem eine ' +
        'Abteilung direkt auf ihren Bereich verweisen kann — ändert man es später, ' +
        'funktionieren alte Links nicht mehr.',
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
