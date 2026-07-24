# Roadmap — PyTibia Linux

Este documento acompanha a adaptação do PyTibia para Linux. Ele deve ser atualizado à medida que decisões técnicas forem tomadas, marcos forem concluídos e novas etapas forem planejadas.

## Princípios

- preservar a arquitetura, os contratos e o comportamento observável do projeto original;
- manter a implementação Linux totalmente independente de `PyTibia/` em runtime;
- realizar todo desenvolvimento permanente dentro de `PyTibia-Linux/`;
- analisar e comparar alternativas Linux antes de substituir dependências exclusivas do Windows;
- limitar divergências ao menor escopo tecnicamente necessário;
- documentar decisões, diferenças e limitações de plataforma.

## Legenda

- ⬜ Planejado
- 🔎 Em análise
- 🚧 Em andamento
- ✅ Concluído
- ⛔ Bloqueado

## Marcos

### 1. Captura de tela e escala de cinza

**Estado:** ✅ Concluído

**Objetivo:** replicar no Linux a abordagem de captura de tela de baixa latência realizada pelo `dxcam` e preservar a saída em escala de cinza consumida pelo pipeline de visão computacional.

#### Comportamento que deve ser preservado

- manter uma instância de captura reutilizável, sem recriá-la a cada frame;
- capturar frames com baixa latência e overhead adequado ao loop em tempo real;
- receber a imagem em um formato conhecido, preferencialmente BGRA ou BGR;
- converter o frame para uma matriz NumPy bidimensional em escala de cinza;
- preservar o último screenshot válido;
- quando a captura não produzir um frame novo, retornar o último frame válido, mantendo o contrato original;
- fornecer uma função equivalente a `getScreenshot()` para os demais módulos;
- manter a captura desacoplada das regras de gameplay;
- evitar cópias de memória desnecessárias quando o backend permitir;
- permitir testes sem depender de uma sessão gráfica real.

#### Etapa 1.1 — Identificar o ambiente gráfico

Antes de escolher a tecnologia, registrar:

- distribuição Linux alvo;
- sessão X11 ou Wayland;
- compositor/desktop utilizado;
- GPU e driver;
- quantidade e disposição dos monitores;
- resolução, escala fracionária e DPI;
- necessidade de capturar a tela inteira, um monitor ou somente a janela do Tibia.

#### Ambiente alvo identificado

Levantamento realizado em 24 de julho de 2026:

- distribuição: Ubuntu 24.04.4 LTS;
- sessão: X11 (`ubuntu-xorg`);
- desktop/compositor: GNOME/Ubuntu;
- display: `:0`;
- GPU: AMD Radeon RX 7800 XT (Navi 32);
- driver: `amdgpu`;
- monitores: um monitor ativo em `DisplayPort-1`;
- resolução: 1920 × 1080;
- frequência ativa: 144 Hz;
- escala de interface/texto: 100% (`1.0`);
- PipeWire: 1.0.5 instalado;
- portais: `xdg-desktop-portal` e backend GNOME instalados;
- FFmpeg: não instalado;
- Poetry: 2.4.1;
- Python disponível no sistema: 3.12.3;
- Python requerido para a aplicação: 3.11.7, ainda não disponível.

Para preservar o comportamento original, o primeiro escopo será a captura do monitor inteiro em 1920 × 1080. Captura de janela/região poderá ser avaliada posteriormente sem alterar o contrato de `getScreenshot()`.

#### Etapa 1.2 — Comparar alternativas ao `dxcam`

Nenhuma biblioteca será escolhida antes de uma comparação técnica. A análise deverá incluir, no mínimo, quando aplicáveis:

- `mss`;
- PipeWire com `xdg-desktop-portal`;
- APIs nativas de X11, como XShm/XCB;
- APIs ou bibliotecas específicas do compositor;
- captura pela GPU ou por ferramentas como FFmpeg/PipeWire, caso atendam à latência necessária.

Para cada opção, documentar:

- suporte a X11 e Wayland;
- necessidade de portal ou confirmação do usuário;
- capacidade de selecionar monitor, região ou janela;
- formato de pixel entregue;
- custo de conversão para NumPy/OpenCV;
- latência, throughput e estabilidade;
- consumo de CPU/GPU e cópias de memória;
- manutenção do projeto e disponibilidade nas distribuições;
- facilidade de instalação, testes e empacotamento;
- diferenças em relação ao contrato do `dxcam`;
- vantagens, desvantagens e limitações.

##### Comparação inicial

| Alternativa | X11 | Wayland | Formato/integração | Vantagens | Desvantagens |
|---|---:|---:|---|---|---|
| `mss` | Sim | Não de forma nativa e geral | Buffer BGRA diretamente convertível para NumPy/OpenCV | API Python pequena e semelhante ao `grab()`; instância reutilizável; sem dependências Python adicionais; projeto estável e mantido; suporta Python 3.11; monitor/região; implementação simples e testável | Em Linux usa captura X11 baseada em Xlib/XGetImage, com cópia CPU; não aproveita a GPU como DXGI/DXCam; não atende uma futura sessão Wayland sem outro backend |
| XCB/XShm direto | Sim | Não | Buffer nativo via memória compartilhada, exigindo binding e tratamento explícito do formato | Melhor potencial de latência/throughput em X11; controle de memória, região e sincronização; aproxima-se mais do objetivo de alto desempenho do DXCam | Implementação e manutenção muito mais complexas; risco de erros de stride, endianess e lifecycle; bindings/sistema adicionais; testes mais difíceis; específico de X11 |
| PipeWire + `xdg-desktop-portal` | Sim, via portal | Sim | Stream assíncrono PipeWire; integração usual por GStreamer/PyGObject ou binding nativo | Solução padrão e segura para Wayland; captura de monitor ou janela; pode persistir permissão com restore token; boa base para compatibilidade futura | Fluxo assíncrono bem diferente de `grab()`; normalmente abre diálogo de seleção/permissão; maior complexidade; negociação de buffers/formato; integração Python e testes mais pesados; desnecessário para a sessão X11 atual |
| GStreamer `ximagesrc` | Sim | Não | Stream RGB bruto recebido por appsink/PyGObject | Pode capturar tela, região ou XID de janela; usa XDamage; pipeline maduro e configurável | Dependências GStreamer/PyGObject; lifecycle e thread de pipeline; frames assíncronos; padrão de 25 FPS precisa ser alterado; mais camadas e overhead que `mss`; específico de X11 |
| FFmpeg (`x11grab`/PipeWire) | Sim | Dependente da entrada/portal disponível | Processo ou bibliotecas FFmpeg produzindo vídeo bruto | Ferramenta madura, configurável e útil para diagnóstico/benchmark | FFmpeg não está instalado; subprocesso adiciona cópia, buffering, parsing e shutdown complexo; API pouco semelhante ao original; inadequado como primeira escolha para chamadas síncronas por frame |

##### Recomendação técnica

Para o ambiente atual, a recomendação é **`mss` como primeiro backend**, mantendo um adaptador de captura que preserve o contrato do original. É a alternativa com menor divergência de API: uma instância persistente realiza `grab`, entrega BGRA, e OpenCV converte com `cv2.COLOR_BGRA2GRAY`.

Diferença inevitável: ao contrário do DXCam/DXGI, `mss` no X11 não é uma captura GPU-first e tende a envolver cópia pela CPU. Essa diferença deve ser medida, não presumida aceitável. O marco deve incluir benchmark de `mss`; se não sustentar a latência necessária, a segunda opção recomendada é um backend XCB/XShm otimizado atrás do mesmo contrato.

PipeWire/portal é a recomendação para uma futura meta Wayland, mas não para o primeiro backend no X11 atual, porque introduz seleção/permissão e um stream assíncrono que divergem significativamente do contrato original.

**Decisão aprovada em 24 de julho de 2026:** utilizar `mss` como primeiro backend X11, condicionado aos testes e ao benchmark de desempenho. Se os resultados não forem adequados ao loop em tempo real, avaliar XCB/XShm atrás do mesmo contrato.

#### Implementação inicial

Implementado em `src/utils/core.py`:

- substituição de `dxcam` por `mss`;
- criação lazy e reutilização de uma única instância de captura;
- captura do monitor primário por `monitors[1]`;
- conversão explícita do screenshot MSS para `numpy.ndarray`;
- conversão BGRA → grayscale com `cv2.COLOR_BGRA2GRAY`;
- preservação de `latestScreenshot`;
- retorno do último frame válido quando `grab()` retorna `None`;
- preservação do retorno `None` quando ainda não existe frame válido.

Foram copiados fisicamente apenas os arquivos necessários da arquitetura original para `PyTibia-Linux/`, sem dependência de runtime em `PyTibia/`.

Testes unitários foram adicionados para conversão, monitor primário, fallback e reutilização da instância.

O Python 3.11.7 foi disponibilizado pelo usuário via `uv`, e o Poetry criou um ambiente virtual usando exatamente essa versão. A classe pública `mss.MSS` é usada para evitar a API `mss.mss`, depreciada na versão 10.2.0.

#### Etapa 1.3 — Definir o contrato de captura

Preservar uma API compatível com o restante da arquitetura, isolando diferenças de plataforma atrás de um adaptador.

Contrato mínimo esperado:

```python
latestScreenshot = None


def getScreenshot():
    """Retorna o frame mais recente como ndarray 2D em escala de cinza."""
```

Propriedades esperadas da saída:

- tipo: `numpy.ndarray`;
- dimensões: `(altura, largura)`;
- canais: um canal;
- dtype esperado: `uint8`;
- faixa esperada: `0..255`;
- memória contígua quando necessária pelos consumidores;
- ordem e orientação espacial idênticas à imagem capturada.

#### Etapa 1.4 — Implementar conversão para grayscale

A conversão deve respeitar o formato real entregue pelo backend:

- BGRA → grayscale: `cv2.COLOR_BGRA2GRAY`;
- BGR → grayscale: `cv2.COLOR_BGR2GRAY`;
- RGB/RGBA: usar o código de conversão correspondente, sem assumir ordem de canais;
- frame já monocromático: validar dtype e dimensões antes de reutilizar.

A implementação não deve converter com uma constante incorreta apenas para manter a mesma linha de código do Windows. O comportamento final — uma matriz grayscale equivalente — é o contrato que precisa ser preservado.

#### Etapa 1.5 — Testes e benchmark

Criar validações para:

- formato, dtype e dimensões da saída;
- conversão correta de pixels conhecidos para grayscale;
- fallback para o último frame válido;
- comportamento antes de existir um primeiro frame válido;
- frames nulos, inválidos ou com dimensões inesperadas;
- sequência de múltiplas capturas;
- seleção correta de monitor/região;
- funcionamento no ambiente gráfico suportado.

Medir e registrar:

- tempo médio, mediana, p95 e p99 por captura;
- frames por segundo sustentados;
- custo separado da captura e da conversão grayscale;
- consumo aproximado de CPU e memória;
- ocorrência de frames repetidos, nulos ou corrompidos.

##### Resultados da validação inicial

Ambiente: X11, monitor primário 1920 × 1080 a 144 Hz, 200 frames consecutivos.

| Medição | Média | Mediana | p95 | p99 |
|---|---:|---:|---:|---:|
| Captura MSS | 6,874 ms | 7,446 ms | 10,421 ms | 11,153 ms |
| Conversão grayscale | 0,150 ms | 0,138 ms | 0,174 ms | 0,295 ms |
| Total | 7,024 ms | 7,583 ms | 10,556 ms | 11,448 ms |

Throughput calculado: **142,4 FPS**.

O resultado é adequado ao loop original, cujo período alvo é aproximadamente 45 ms (~22 ciclos/s). A captura de integração retornou `numpy.ndarray` 2D, shape `(1080, 1920)`, dtype `uint8`, memória C-contígua e valores válidos na faixa grayscale.

Os quatro testes unitários passaram. Há sete avisos de depreciação originados no `nptyping 2.5.0` ao usar aliases antigos do NumPy; eles já decorrem das versões preservadas do projeto original e não afetam a captura.

#### Critérios de conclusão

- [x] ambiente Linux alvo documentado;
- [x] alternativas ao `dxcam` apresentadas com prós e contras;
- [x] backend aprovado pelo usuário;
- [x] decisão técnica documentada em `PyTibia-Linux/`;
- [x] adaptador implementado sem dependência de runtime em `PyTibia/`;
- [x] `getScreenshot()` implementado para retornar `ndarray` grayscale compatível;
- [x] fallback do último frame válido preservado;
- [x] testes unitários da conversão e do fallback aprovados;
- [x] teste de integração no ambiente gráfico alvo aprovado;
- [x] benchmark registrado e adequado ao loop em tempo real;
- [x] diferenças inevitáveis em relação ao `dxcam` documentadas.

## Backlog futuro

Os próximos marcos serão definidos incrementalmente após a estabilização da captura de tela.

| Ordem | Marco | Estado | Observação |
|---:|---|---|---|
| 1 | Captura de tela e escala de cinza | ✅ | MSS validado em X11: 4 testes aprovados e 142,4 FPS no benchmark inicial |
| 2 | A definir | ⬜ | Será detalhado posteriormente |
