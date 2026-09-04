// Aufbau der linken Navigation. Ohne diese Datei würde Sanity einfach alle
// Dokumentarten alphabetisch auflisten; hier stehen sie in der Reihenfolge,
// in der sie im Vereinsalltag gebraucht werden.

export const struktur = (S) =>
  S.list()
    .title('Inhalte')
    .items([
      S.listItem()
        .title('Sportangebote')
        .child(S.documentTypeList('angebot').title('Sportangebote')),
      S.listItem()
        .title('Termine')
        .child(S.documentTypeList('termin').title('Termine')),
      S.listItem()
        .title('Aktionen (Startseite)')
        .child(S.documentTypeList('aktion').title('Aktionen')),
      S.listItem()
        .title('Aktuelles')
        .child(S.documentTypeList('news').title('Aktuelles')),

      S.divider(),

      S.listItem()
        .title('Vorstand')
        .child(S.documentTypeList('vorstandsmitglied').title('Vorstand')),
      S.listItem()
        .title('Beiträge')
        .child(S.documentTypeList('beitrag').title('Mitgliedsbeiträge')),
      S.listItem()
        .title('Dokumente & PDFs')
        .child(S.documentTypeList('dokument').title('Dokumente & PDFs')),
      S.listItem()
        .title('Sponsoren')
        .child(S.documentTypeList('sponsor').title('Sponsoren')),
      S.listItem()
        .title('Spielpläne')
        .child(S.documentTypeList('spielplan').title('Spielpläne')),

      S.divider(),

      // Einzelstücke: fester Dokumentschlüssel, damit nie zwei entstehen.
      S.listItem()
        .title('Stammdaten des Vereins')
        .child(S.document().schemaType('verein').documentId('verein').title('Stammdaten')),
      S.listItem()
        .title('Texte & Bilder der Seiten')
        .child(S.document().schemaType('texte').documentId('texte').title('Texte & Bilder')),

      S.divider(),

      S.listItem()
        .title('Bereiche')
        .child(S.documentTypeList('kategorie').title('Bereiche')),
      S.listItem()
        .title('Zielgruppen')
        .child(S.documentTypeList('zielgruppe').title('Zielgruppen')),
    ])
