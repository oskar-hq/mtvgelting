import {defineArrayMember, defineField, defineType} from 'sanity'

export const WOCHENTAGE = [
  'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag',
]

// Eine einzelne Trainingseinheit. Sie erscheint in der Karte des Angebots und
// zugleich im Wochenplan auf der Termineseite — eingetragen wird sie nur hier.
const trainingszeit = defineArrayMember({
  name: 'trainingszeit',
  title: 'Trainingszeit',
  type: 'object',
  fields: [
    defineField({
      name: 'tag',
      title: 'Wochentag',
      type: 'string',
      options: {list: WOCHENTAGE},
      initialValue: 'Montag',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'von',
      title: 'von',
      type: 'string',
      description: 'Uhrzeit als 24-Stunden-Angabe, zum Beispiel 17:15.',
      validation: (regel) =>
        regel.regex(/^([01]\d|2[0-3]):[0-5]\d$/, {name: 'Uhrzeit'})
          .warning('Bitte als Uhrzeit schreiben, zum Beispiel 17:15.'),
    }),
    defineField({
      name: 'bis',
      title: 'bis',
      type: 'string',
      description: 'Leer lassen, wenn das Ende offen ist — dann steht „ab 17:15“.',
      validation: (regel) =>
        regel.regex(/^([01]\d|2[0-3]):[0-5]\d$/, {name: 'Uhrzeit'})
          .warning('Bitte als Uhrzeit schreiben, zum Beispiel 18:30.'),
    }),
    defineField({
      name: 'gruppe',
      title: 'Gruppe',
      type: 'string',
      description: 'Zum Beispiel „E-Jugend“ oder „Anfänger“.',
    }),
    defineField({
      name: 'ort',
      title: 'Ort',
      type: 'string',
      description: 'Nur ausfüllen, wenn es vom üblichen Ort des Angebots abweicht.',
    }),
    defineField({name: 'leitung', title: 'Übungsleitung', type: 'string'}),
    defineField({
      name: 'hinweis',
      title: 'Hinweis',
      type: 'string',
      description: 'Zum Beispiel „nicht in den Ferien“.',
    }),
  ],
  preview: {
    select: {tag: 'tag', von: 'von', bis: 'bis', gruppe: 'gruppe', leitung: 'leitung'},
    prepare({tag, von, bis, gruppe, leitung}) {
      const zeit = von && bis ? `${von}–${bis}` : von ? `ab ${von}` : 'nach Absprache'
      return {
        title: `${tag || '—'} ${zeit}`,
        subtitle: [gruppe, leitung].filter(Boolean).join(' · '),
      }
    },
  },
})

export const angebot = defineType({
  name: 'angebot',
  title: 'Sportangebot',
  type: 'document',
  groups: [
    {name: 'allgemein', title: 'Angebot', default: true},
    {name: 'zeiten', title: 'Trainingszeiten'},
    {name: 'kontakt', title: 'Ansprechpartner'},
  ],
  fields: [
    defineField({
      name: 'name',
      title: 'Name des Angebots',
      type: 'string',
      group: 'allgemein',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'slug',
      title: 'Kürzel für die Adresszeile',
      type: 'slug',
      group: 'allgemein',
      options: {source: 'name', maxLength: 60},
      description:
        'Wird aus dem Namen gebildet. Damit lässt sich direkt auf dieses Angebot ' +
        'verlinken. Ändern macht alte Links unbrauchbar.',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'kategorie',
      title: 'Bereich',
      type: 'reference',
      to: [{type: 'kategorie'}],
      group: 'allgemein',
      description: 'Bestimmt, unter welchem Filter das Angebot erscheint.',
      validation: (regel) => regel.required(),
    }),
    defineField({
      name: 'zielgruppen',
      title: 'Für wen ist das Angebot?',
      type: 'array',
      group: 'allgemein',
      of: [defineArrayMember({type: 'reference', to: [{type: 'zielgruppe'}]})],
      description: 'Mehrfachauswahl möglich.',
    }),
    defineField({
      name: 'kurz',
      title: 'Kurzbeschreibung',
      type: 'string',
      group: 'allgemein',
      description: 'Ein Satz. Steht in der Übersicht direkt unter dem Namen.',
    }),
    defineField({
      name: 'text',
      title: 'Ausführliche Beschreibung',
      type: 'text',
      rows: 6,
      group: 'allgemein',
      description:
        'Erscheint, wenn jemand die Karte aufklappt. Eine Leerzeile beginnt einen ' +
        'neuen Absatz.',
    }),
    defineField({
      name: 'ort',
      title: 'Üblicher Ort',
      type: 'string',
      group: 'allgemein',
      description: 'Gilt für alle Trainingszeiten, bei denen kein eigener Ort steht.',
    }),
    defineField({
      name: 'zeiten',
      title: 'Trainingszeiten',
      type: 'array',
      group: 'zeiten',
      of: [trainingszeit],
      description:
        'Jeder Eintrag ist eine Trainingseinheit. Sie erscheinen zugleich im ' +
        'Wochenplan. Ohne Eintrag steht beim Angebot „Zeit auf Anfrage“.',
    }),
    defineField({
      name: 'leitung',
      title: 'Ansprechpartner',
      type: 'string',
      group: 'kontakt',
      description: 'Wer die Abteilung leitet und Fragen beantwortet.',
    }),
    defineField({
      name: 'kontaktEmail',
      title: 'E-Mail',
      type: 'string',
      group: 'kontakt',
      validation: (regel) => regel.email(),
    }),
    defineField({name: 'kontaktTelefon', title: 'Telefon', type: 'string', group: 'kontakt'}),
    defineField({
      name: 'sortierung',
      title: 'Reihenfolge',
      type: 'number',
      group: 'allgemein',
      initialValue: 0,
      description: 'Kleinere Zahlen stehen weiter vorn in der Übersicht.',
    }),
  ],
  orderings: [
    {title: 'Reihenfolge', name: 'sortierung', by: [{field: 'sortierung', direction: 'asc'}]},
    {title: 'Name', name: 'name', by: [{field: 'name', direction: 'asc'}]},
  ],
  preview: {
    select: {title: 'name', kategorie: 'kategorie.name', zeiten: 'zeiten'},
    prepare({title, kategorie, zeiten}) {
      const anzahl = (zeiten || []).length
      return {
        title,
        subtitle: [kategorie, anzahl ? `${anzahl} Trainingszeiten` : 'Zeit auf Anfrage']
          .filter(Boolean)
          .join(' · '),
      }
    },
  },
})
