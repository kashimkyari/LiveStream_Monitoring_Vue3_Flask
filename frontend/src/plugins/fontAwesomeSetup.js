// src/plugins/fontAwesomeSetup.js

import { library } from '@fortawesome/fontawesome-svg-core'
import { faSync, faEdit, faTrash, faBell, faPlus, faCheck, faExclamationTriangle, faUser, faStream, faCog } from '@fortawesome/free-solid-svg-icons'

export default function setupFontAwesome() {
  library.add(
    faSync, 
    faEdit, 
    faTrash, 
    faBell, 
    faPlus, 
    faCheck, 
    faExclamationTriangle, 
    faUser, 
    faStream, 
    faCog
  )
}