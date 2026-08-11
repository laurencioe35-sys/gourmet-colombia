Publicar en GitHub — Instrucciones

1) Con GitHub CLI (`gh`) (recomendado si estás autenticado):

```powershell
# Crea el repo y empuja el código (reemplaza USERNAME)
gh repo create USERNAME/gourmet-pos --public --source . --remote origin --push
```

2) Manual (HTTPS):

```powershell
# Crea el repo en GitHub (vía web) y luego en tu máquina:
git remote add origin https://github.com/USERNAME/gourmet-pos.git
git branch -M main
git push -u origin main
```

3) SSH (si tienes clave configurada):

```powershell
git remote add origin git@github.com:USERNAME/gourmet-pos.git
git branch -M main
git push -u origin main
```

Notas:
- Si `gh` no está instalado, instala desde https://github.com/cli/cli
- Para SSH, asegúrate de agregar tu clave pública en https://github.com/settings/keys
- Si deseas, puedo ejecutar los comandos ahora (necesitas estar autenticado en `gh` o tener las credenciales adecuadas).