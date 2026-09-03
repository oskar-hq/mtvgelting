import {defineConfig} from 'sanity'
import {structureTool} from 'sanity/structure'
import {visionTool} from '@sanity/vision'

import {schemaTypes} from './schemaTypes/index.js'
import {struktur} from './struktur.js'

// Von diesen beiden Arten gibt es je genau ein Dokument. Sie tauchen deshalb
// als einzelner Menüpunkt auf und lassen sich nicht versehentlich doppelt
// anlegen oder löschen.
const EINZELSTUECKE = ['verein', 'texte']

export default defineConfig({
  name: 'default',
  title: 'MTV Gelting 08',

  projectId: 'tonxqosy',
  dataset: 'production',

  plugins: [
    structureTool({structure: struktur}),
    // Werkzeug zum Ausprobieren von Abfragen — nur für die Technik interessant.
    visionTool({defaultApiVersion: '2024-10-01'}),
  ],

  schema: {
    types: schemaTypes,
    // „Verein“ und „Texte“ nicht im Anlegen-Menü anbieten.
    templates: (vorlagen) => vorlagen.filter((v) => !EINZELSTUECKE.includes(v.schemaType)),
  },

  document: {
    // Bei den Einzelstücken das Löschen und Vervielfältigen ausblenden.
    actions: (aktionen, {schemaType}) =>
      EINZELSTUECKE.includes(schemaType)
        ? aktionen.filter(({action}) => !['unpublish', 'delete', 'duplicate'].includes(action))
        : aktionen,
  },
})
