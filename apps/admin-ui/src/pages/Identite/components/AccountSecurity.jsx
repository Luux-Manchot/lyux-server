import React from 'react'
import { Card, SettingRow, Toggle } from '../../../components.jsx'

export default function AccountSecurity({ twoFactor, onTwoFactorChange }) {
  return (
    <Card title="Sécurité des comptes" subtitle="Options globales d'authentification">
      <SettingRow
        icon="key"
        title="Authentification à deux facteurs"
        description="Demande un second facteur lors de la connexion des comptes administrateurs."
        control={<Toggle checked={twoFactor} onChange={onTwoFactorChange} label="Authentification à deux facteurs" />}
      />
    </Card>
  )
}
