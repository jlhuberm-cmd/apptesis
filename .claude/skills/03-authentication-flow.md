# 03 · Flujo de autenticación

- Bloqueo tras **3** intentos fallidos de login.
- Códigos de **6 dígitos** hasheados, expiración **15 min**, **3** intentos.
- Propósitos: EMAIL_VERIFICATION, PASSWORD_RESET, ACCOUNT_UNLOCK.
- Contraseñas con **bcrypt rounds=12**.
- Estados de cuenta: PENDING_VERIFICATION, ACTIVE, LOCKED, INACTIVE.
