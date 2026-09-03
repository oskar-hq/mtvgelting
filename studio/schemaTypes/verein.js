import {defineField, defineType} from 'sanity'

// Von dieser Art gibt es genau ein Dokument. Die Angaben erscheinen im Footer
// jeder Seite, auf der Vereinsseite und im Impressum — sie stehen also nur
// hier und nicht dreimal.
export const verein = defineType({
  name: 'verein',
  title: 'Stammdaten des Vereins',
  type: 'document',
  groups: [
    {name: 'allgemein', title: 'Allgemein', default: true},
    {name: 'kontakt', title: 'Kontakt'},
    {name: 'netz', title: 'Im Netz'},
  ],
  fields: [
    defineField({
      name: 'name',
      title: 'Vollständiger Vereinsname',
      type: 'string',
      group: 'allgemein',
      description: 'Wie er im Impressum und im Vereinsregister steht.',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'kurzname',
      title: 'Kurzname',
      type: 'string',
      group: 'allgemein',
      description: 'Erscheint im Seitentitel und groß unten im Footer.',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'gegruendet',
      title: 'Gegründet',
      type: 'number',
      group: 'allgemein',
      description: 'Jahreszahl, erscheint als „seit …“ im Kopf der Seite.',
    }),
    defineField({
      name: 'claim',
      title: 'Ein Satz über den Verein',
      type: 'text',
      rows: 2,
      group: 'allgemein',
      description: 'Steht auf der Startseite und oben auf der Vereinsseite.',
    }),
    defineField({
      name: 'adresse',
      title: 'Anschrift',
      type: 'object',
      group: 'kontakt',
      options: {columns: 2},
      fields: [
        defineField({name: 'strasse', title: 'Straße und Hausnummer', type: 'string'}),
        defineField({name: 'plz', title: 'Postleitzahl', type: 'string'}),
        defineField({name: 'ort', title: 'Ort', type: 'string'}),
      ],
    }),
    defineField({
      name: 'telefon',
      title: 'Telefon',
      type: 'string',
      group: 'kontakt',
      description: 'So, wie es auf der Seite stehen soll — zum Beispiel 04643 1316.',
    }),
    defineField({
      name: 'telefonLink',
      title: 'Telefonnummer für Anruf-Links',
      type: 'string',
      group: 'kontakt',
      description:
        'Leer lassen — sie wird dann automatisch aus der Telefonnummer gebildet ' +
        '(04643 1316 wird zu +4946431316). Nur ausfüllen, wenn das einmal nicht passt.',
    }),
    defineField({name: 'telefax', title: 'Telefax', type: 'string', group: 'kontakt'}),
    defineField({
      name: 'email',
      title: 'E-Mail-Adresse',
      type: 'string',
      group: 'kontakt',
      validation: (regel) => regel.required().email(),
    }),
    defineField({
      name: 'oeffnungszeiten',
      title: 'Öffnungszeiten der Geschäftsstelle',
      type: 'text',
      rows: 3,
      group: 'kontakt',
      description: 'Leer lassen, solange es keine festen Zeiten gibt.',
    }),
    defineField({
      name: 'register',
      title: 'Registereintrag',
      type: 'string',
      group: 'kontakt',
      description: 'Zum Beispiel: VR 1033 FL, Amtsgericht Flensburg. Erscheint im Impressum.',
    }),
    defineField({
      name: 'beitragHinweis',
      title: 'Hinweis unter den Mitgliedsbeiträgen',
      type: 'text',
      rows: 3,
      group: 'allgemein',
      description: 'Zum Beispiel, wann und wie der Beitrag eingezogen wird.',
    }),
    defineField({name: 'shop', title: 'Vereinsshop', type: 'url', group: 'netz'}),
    defineField({name: 'facebook', title: 'Facebook', type: 'url', group: 'netz'}),
    defineField({name: 'instagram', title: 'Instagram', type: 'url', group: 'netz'}),
  ],
  preview: {
    select: {title: 'kurzname', subtitle: 'name'},
  },
})
