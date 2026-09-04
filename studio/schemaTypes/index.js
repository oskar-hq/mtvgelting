import {aktion} from './aktion.js'
import {angebot} from './angebot.js'
import {beitrag} from './beitrag.js'
import {dokument} from './dokument.js'
import {kategorie} from './kategorie.js'
import {news} from './news.js'
import {spielplan} from './spielplan.js'
import {sponsor} from './sponsor.js'
import {termin} from './termin.js'
import {texte} from './texte.js'
import {verein} from './verein.js'
import {vorstandsmitglied} from './vorstandsmitglied.js'
import {zielgruppe} from './zielgruppe.js'

export const schemaTypes = [
  // Einzelstücke
  verein,
  texte,
  // Inhalte
  angebot,
  termin,
  aktion,
  news,
  vorstandsmitglied,
  beitrag,
  dokument,
  sponsor,
  spielplan,
  // Gliederung
  kategorie,
  zielgruppe,
]
