---
description: Contrasta el estado real del proyecto con la rúbrica (EVALUATION.md)
---
Auditoría de rúbrica. No modifiques código; solo lee, ejecuta comprobaciones y reporta.

1. Lee docs/EVALUATION.md y docs/PROGRESS.md.
2. Verifica con evidencia fresca lo verificable ahora mismo: `make lint`, `make test`,
   estructura de ficheros, secciones del README, ausencia de librerías prohibidas
   (busca imports de networkx/graphlib), presencia del Makefile con las reglas del
   subject (install/run/debug/clean/lint).
3. Para cada ítem de la matriz, reevalúa su estado (NOT_STARTED / IN_PROGRESS /
   EVIDENCED / BLOCKED) según lo que realmente existe, no según lo planeado.
4. Reporta: (a) ítems en riesgo de flag de la rúbrica (crash, norma, ficheros de más
   en el repo, leaks de recursos, no poder explicar código), (b) ítems marcados mejor
   de lo que la evidencia soporta, (c) los 3 siguientes ítems más baratos de evidenciar.
5. Propón las actualizaciones a docs/EVALUATION.md y aplícalas solo tras OK de Jose.
