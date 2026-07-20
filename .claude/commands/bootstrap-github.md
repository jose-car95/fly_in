---
description: Crea labels, issues M0/M1, épicas M2-M6, Project v2 y protección de main (una sola vez)
---
Ejecuta `scripts/bootstrap_github.sh` paso a paso y supervisa su salida.

Reglas:
1. Antes de lanzarlo, verifica `gh auth status` y que existe remoto (`gh repo view`).
   Si no hay remoto, propón el comando `gh repo create ... --source=. --push` y espera OK.
2. Si el script falla por scope insuficiente, PARA. Muestra a Jose el comando literal
   `gh auth refresh -s <scope>` que imprime el script, espera a que complete el device
   flow y reintenta. No intentes rodear el permiso de ninguna otra forma.
3. Al terminar, copia la sección de pasos manuales de la web al chat y actualiza
   docs/PROGRESS.md (sección "GitHub"): qué automatizaciones quedaron activas, cuáles
   requieren clics en la web y qué movimientos son manuales (issue -> In Progress).
4. Recuerda a Jose la convención: una rama por issue y `Closes #N` en cada PR.
