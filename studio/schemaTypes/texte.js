import {defineField, defineType} from 'sanity'

// Ebenfalls ein Einzelstück: die längeren Texte und die Bilder, die nicht zu
// einem einzelnen Eintrag gehören, sondern zu einer Seite.
export const texte = defineType({
  name: 'texte',
  title: 'Texte & Bilder der Seiten',
  type: 'document',
  groups: [
    {name: 'start', title: 'Startseite', default: true},
    {name: 'verein', title: 'Vereinsseite'},
    {name: 'recht', title: 'Impressum & Datenschutz'},
    {name: 'technik', title: 'Sichtbarkeit'},
  ],
  fields: [
    defineField({
      name: 'startTitel',
      title: 'Überschrift der Startseite',
      type: 'string',
      group: 'start',
      description: 'Erste Zeile, zum Beispiel „Sport für alle.“',
    }),
    defineField({
      name: 'startTitelAkzent',
      title: 'Zweite Zeile der Überschrift',
      type: 'string',
      group: 'start',
      description: 'Wird farbig hervorgehoben, zum Beispiel „In Gelting.“',
    }),
    defineField({
      name: 'startSeitentitel',
      title: 'Titel im Browser-Tab',
      type: 'string',
      group: 'start',
      description: 'Was oben im Reiter des Browsers und bei Google steht.',
    }),
    defineField({
      name: 'startBild',
      title: 'Großes Bild auf der Startseite',
      type: 'image',
      group: 'start',
      options: {hotspot: true},
      description: 'Ohne Bild erscheint ein grauer Platzhalter.',
    }),
    defineField({
      name: 'trainingBild',
      title: 'Bild beim Hinweis auf den Wochenplan',
      type: 'image',
      group: 'start',
      options: {hotspot: true},
    }),
    defineField({
      name: 'sprachrohrText',
      title: 'Sprachrohr: Einleitung',
      type: 'text',
      rows: 3,
      group: 'verein',
    }),
    defineField({
      name: 'sprachrohrBild',
      title: 'Sprachrohr: Titelbild',
      type: 'image',
      group: 'verein',
      options: {hotspot: true},
    }),
    defineField({
      name: 'jugendschutzText',
      title: 'Kinder- & Jugendschutz',
      type: 'text',
      rows: 8,
      group: 'verein',
      description:
        'Schutzkonzept und Ansprechpersonen. Eine Leerzeile beginnt einen neuen Absatz.',
    }),
    defineField({
      name: 'quelle',
      title: 'Quelle der Trainingszeiten',
      type: 'text',
      rows: 2,
      group: 'verein',
      description:
        'Wird unter dem Wochenplan genannt, zum Beispiel „Hallenbelegungsplan, ' +
        'gültig ab Juni 2026“. Leer lassen, um den Hinweis auszublenden.',
    }),
    defineField({
      name: 'impressumHinweis',
      title: 'Hinweis unter dem Impressum',
      type: 'text',
      rows: 3,
      group: 'recht',
    }),
    defineField({
      name: 'datenschutzText',
      title: 'Datenschutzerklärung',
      type: 'text',
      rows: 15,
      group: 'recht',
      description:
        'Leer lassen, um den mitgelieferten Standardtext zu verwenden. ' +
        'Eine Leerzeile beginnt einen neuen Absatz.',
    }),
    defineField({
      name: 'datenschutzHinweis',
      title: 'Hinweis unter der Datenschutzerklärung',
      type: 'text',
      rows: 3,
      group: 'recht',
    }),
    defineField({
      name: 'hinweisbanner',
      title: 'Hinweisstreifen ganz oben',
      type: 'text',
      rows: 2,
      group: 'technik',
      description:
        'Erscheint als schmaler Streifen über der Seite. Leer lassen, um ihn ' +
        'auszublenden. Der Teil vor dem ersten „·“ wird fett gesetzt.',
    }),
    defineField({
      name: 'suchmaschinenSperren',
      title: 'Für Suchmaschinen sperren',
      type: 'boolean',
      group: 'technik',
      initialValue: true,
      description:
        'Solange die Seite ein Entwurf ist, sollte das angehakt bleiben. ' +
        'Vor dem Livegang abwählen, damit die Seite bei Google gefunden wird.',
    }),
  ],
  preview: {
    prepare: () => ({title: 'Texte & Bilder der Seiten'}),
  },
})
