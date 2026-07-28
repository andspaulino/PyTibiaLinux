# Fixtures — Loot Highlighting

Fixtures compactas derivadas de capturas reais realizadas em 27 de julho de 2026 com `temp_capture_loot_highlighting.py`.

Cada `.npz` contém somente sequências grayscale de slots `64×64` revisados, sem screenshots completas:

- `before`: `(slots, 12, 64, 64)` antes da ação/controle;
- `after`: `(slots, 12, 64, 64)` depois da ação/controle;
- `slots`: coordenadas `(coluna, linha)` na grade `15×11`;
- `sample`: nome da amostra temporária de origem.

Casos:

- `multiple_looted.npz`: três corpses de espécies/paletas distintas e uma animação ambiental;
- `control_without_loot.npz`: quatro corpses mantidos sem executar Quick Loot e uma animação ambiental;
- `control_without_corpses.npz`: duas tochas, sem corpse lootável;
- `stacked_looted.npz`: Goblin isolado, Goblin + Ghost empilhados e uma animação ambiental.

As fixtures são dados de teste permanentes e independem de `temp_loot_samples/` e de `PyTibia/`.
