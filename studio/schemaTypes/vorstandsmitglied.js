import {defineField, defineType} from 'sanity'

export const vorstandsmitglied = defineType({
  name: 'vorstandsmitglied',
  title: 'Vorstandsmitglied',
  type: 'document',
  fields: [
    defineField({
      name: 'name',
      title: 'Name',
      type: 'string',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'rolle',
      title: 'Funktion',
      type: 'string',
      description: 'Zum Beispiel „1. Vorsitzender“ oder „Kassenwartin“.',
    }),
    defineField({
      name: 'email',
      title: 'E-Mail',
      type: 'string',
      description: 'Erscheint als Link auf der Vereinsseite. Leer lassen, wenn nicht gewünscht.',
      validation: (regel) => regel.email(),
    }),
    defineField({
      name: 'paragraf26',
      title: 'Vertritt den Verein nach § 26 BGB',
      type: 'boolean',
      initialValue: false,
      description:
        'Diese Personen werden zusätzlich im Impressum unter „Vertreten durch“ genannt.',
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
  preview: {
    select: {title: 'name', subtitle: 'rolle', p26: 'paragraf26'},
    prepare({title, subtitle, p26}) {
      return {title, subtitle: [subtitle, p26 ? '§ 26 BGB' : null].filter(Boolean).join(' · ')}
    },
  },
})
