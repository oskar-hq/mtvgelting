import {defineField, defineType} from 'sanity'

// Hervorgehobene Aktionen auf der Startseite — Birklauf, Flohmarkt,
// Herbstcamp und was sonst noch dazukommt. Über „Auf der Startseite zeigen“
// lässt sich jede einzeln an- und abschalten, ohne sie löschen zu müssen:
// nach der Veranstaltung einfach den Haken entfernen, im nächsten Jahr das
// Datum und den Anmeldelink erneuern und wieder anhaken.
export const aktion = defineType({
  name: 'aktion',
  title: 'Aktion',
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
      name: 'aktiv',
      title: 'Auf der Startseite zeigen',
      type: 'boolean',
      initialValue: true,
      description:
        'Abwählen blendet die Aktion aus, ohne sie zu löschen — Texte und Angaben ' +
        'bleiben für das nächste Mal erhalten.',
    }),
    defineField({
      name: 'kurz',
      title: 'Überschrift darüber',
      type: 'string',
      description: 'Wenige Worte, zum Beispiel „Volkslauf rund um Gelting“.',
    }),
    defineField({
      name: 'datum',
      title: 'Datum',
      type: 'date',
      options: {dateFormat: 'DD.MM.YYYY'},
      description: 'Leer lassen, solange der Termin noch nicht feststeht.',
    }),
    defineField({
      name: 'zeit',
      title: 'Uhrzeit',
      type: 'string',
      description: 'Freier Text, zum Beispiel „ab 15:45 Uhr“.',
    }),
    defineField({name: 'ort', title: 'Ort', type: 'string'}),
    defineField({
      name: 'text',
      title: 'Kurzer Text',
      type: 'text',
      rows: 3,
      description: 'Ein bis zwei Sätze. Für mehr ist auf der Startseite kein Platz.',
    }),
    defineField({
      name: 'anmeldelink',
      title: 'Anmeldelink',
      type: 'url',
      description:
        'Die Adresse des aktuellen Anmeldeformulars. Solange hier nichts steht, ' +
        'erscheint statt des Knopfes der Hinweis „Anmeldung folgt“.',
    }),
    defineField({
      name: 'anmeldetext',
      title: 'Beschriftung des Knopfes',
      type: 'string',
      description: 'Zum Beispiel „Zur Anmeldung“ oder „Stand anmelden“.',
      initialValue: 'Zur Anmeldung',
    }),
    defineField({
      name: 'sortierung',
      title: 'Reihenfolge',
      type: 'number',
      initialValue: 0,
      description: 'Kleinere Zahlen stehen weiter oben.',
    }),
  ],
  orderings: [
    {title: 'Reihenfolge', name: 'sortierung', by: [{field: 'sortierung', direction: 'asc'}]},
  ],
  preview: {
    select: {title: 'titel', kurz: 'kurz', aktiv: 'aktiv', link: 'anmeldelink', datum: 'datum'},
    prepare({title, kurz, aktiv, link, datum}) {
      const teile = [
        aktiv ? 'sichtbar' : 'ausgeblendet',
        datum ? new Date(datum).toLocaleDateString('de-DE') : null,
        link ? 'Anmeldung offen' : 'noch ohne Link',
      ]
      return {title, subtitle: [kurz, teile.filter(Boolean).join(' · ')].filter(Boolean).join(' — ')}
    },
  },
})
