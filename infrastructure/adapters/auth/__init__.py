"""Adaptadores de autenticación contra Supabase Auth (auth.users) + perfiles.

Inician sesión con email/contraseña vía Supabase Auth y resuelven el rol y los
permisos desde las tablas `usuarios`/`usuario_rol`/`roles`. También gestionan
usuarios (crear, activar/desactivar, borrar) usando la Admin API.
"""
