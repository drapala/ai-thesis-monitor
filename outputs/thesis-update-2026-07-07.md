# Thesis update — 2026-07-07

> Refresh após snapshot 2026-05-02 (>2 meses stale). Disparado por revisão de 2 vídeos de comentário
> (Theo/local-models, Henri Jick/AI-bubble) — mas **nenhum vídeo entra como evidência**; eles inspiraram
> as queries adjacent-possible. Toda claim abaixo tem URL fresca via WebSearch (protocolo: paramétrico BANIDO).

## Current regime
- **Previous lean:** citadel (per README exec-summary; snapshot 2026-05-02 já mostrava compressão de headcount = pressão citrini)
- **New lean:** **citadel ainda lidera no LABOR, mas a ação migrou pra INTERMEDIATION (citrini-confirming) e — o achado central — DUAS teses emergentes que nenhum dos lados modela dominam o sinal.**
- **Confidence shift:** citadel confirmado no canal labor (fricção real); citrini ganha forte só em intermediation; o peso do sinal saiu do frame citadel/citrini pras emergentes (open-source deflation + AI-financing-fragility).

## Bradford verification
- Confirming (citadel): 3 queries (25%) — white-collar resilience, enterprise ROI friction, India IT
- Challenging (citrini): 4 queries (33%) — layoffs, consumer demand, SaaS pricing, credit/housing
- Adjacent-possible: 5 queries (42%) — China deflation, token-price index, power bottleneck, circular financing, capex
- **Bradford satisfeito: sim** (≥25% challenging, ≥20% adjacent).

## Metric updates (mapeados aos módulos)
| Módulo | Métrica / sinal | Valor | Fonte |
|---|---|---|---|
| diffusion | Trabalhadores que bypassaram AI tool nos últimos 30d | **54%** (+33% nunca usaram = ~80%) | [Fortune/WalkMe-SAP](https://fortune.com/2026/04/09/ai-backlash-quiet-quitting-fobo-obsolete-white-collar-rebellion/) |
| productivity | Pilots com ZERO impacto mensurável em P&L | **95%** (MIT); só 21% da S&P500 cita benefício | [Terminal-X/MIT](https://www.terminal-x.ai/research/ai-roi-in-2026-why-most-enterprise-ai-fails-and-what-actually-works) |
| labor | Empregos white-collar em máx-de-década baixa; AI reduz ~**16k empregos/mês** (Goldman); 55k layoffs AI-attributed 2025 | ↑ citrini (mas "AI washing" superestima) | [MindStudio](https://www.mindstudio.ai/blog/ai-job-displacement-white-collar-employment-data), [Fortune](https://fortune.com/2026/04/29/ai-agentic-entry-level-jobs-disappearing-yale-celi-sonnenfeld/) |
| demand | Consumer spending **1.6%** annualized H1 2026 (vs 3.6% H2'24); pullback discricionário; K-shaped (top10% = 50% do gasto) | ↑ citrini emergente | [McKinsey](https://www.mckinsey.com/industries/consumer-packaged-goods/our-insights/the-state-of-the-us-consumer), [MorganStanley] |
| intermediation | **"SaaSpocalypse": −$1T em software Fev'26; múltiplos SaaS −60% desde 2021; 35% já trocaram um SaaS por build próprio (Retool), 78% planejam mais; per-seat quebrando** | **↑↑ citrini (sinal mais forte)** | [CIO](https://www.cio.com/article/4173257/the-saas-reckoning-why-ai-is-about-to-reprice-enterprise-software.html), [Retool via digitalapplied](https://www.digitalapplied.com/blog/build-vs-buy-ai-custom-tools-vs-branded-saas-2026) |
| credit_housing | Delinquência agregada **4.8%** (máx desde 2017Q3, era 3.6% YoY); serious mortgage 1.09%; foreclosures +30.6% — MAS bifurcado (FHA 11.5% vs conv 1.8%) | ↑ citrini, não-sistêmico ainda | [NY Fed](https://www.newyorkfed.org/newsevents/news/research/2026/20260512), [VantageScore](https://vantagescore.com/resources/knowledge-center/press_releases/vantagescore-creditgauge-january-2026-mortgage-delinquencies-rise-as-early-stage-credit-stress-broadens-across-borrowers) |
| diffusion (proxy India IT) | HCL guia **"AI deflation" −3 a −5%** de receita futura; Infosys prevê deflation virar fator; crescimento CC só 2.8% | deflation **atingindo o proxy** | [The Register](https://www.theregister.com/software/2026/04/28/ai-deflation-comes-to-indias-tech-services-giants/) |

## Emergent thesis candidates (o achado central — não dobrar em citadel/citrini)

### Candidate 1: `open_source_deflation` — GRADUOU de candidato pra FORÇA PRIMÁRIA
- **Mecanismo:** modelos open chinos (GLM/DeepSeek/Qwen/Kimi/MiniMax) via distillation + MoE derrubam o preço por token 60-90% a ~90% da capacidade frontier, comoditizando o valor mais rápido que o capex pode ser recuperado. Ataca intermediation E a tese de lucro trilionário dos EUA — não é "produtividade vs labor".
- **Evidência dura (nova):** share de tokens de empresas US em modelos chineses no OpenRouter **>30% toda semana desde 8-fev, chegando a 46%** (média dos 12 meses anteriores: 11%; era 4.5% em H1'25). Labs chineses cortaram preço **6x em H1'26** (3 permanentes). GLM-5.2 a **1 ponto** do Opus 4.8 num bench agentic por **~1/5 do custo**; adoção mais rápida que a Vercel já trackeou (27x volume diário, 80x clientes em 1 semana). "Price is doing the work — quando a task não precisa do melhor, roteia pro mais barato que serve." — OpenRouter.
- **Fontes:** [CNBC 2026-07-07](https://www.cnbc.com/2026/07/07/chinese-ai-models-costs-us-openai-anthropic.html), [Epoch AI inference trends](https://epoch.ai/data-insights/llm-inference-price-trends)
- **Proposta:** promover a MÓDULO próprio (`deflation`) ou métrica `chinese_model_token_share_openrouter` + `frontier_token_price_index`. A skill já listava "open-source LLM deflation curve" como candidato em mai/2026 — **agora está confirmado com dado**, não mais especulativo.

### Candidate 2: `power_bottleneck` — confirmado, structural
- **Mecanismo:** eletricidade (não chips) é a restrição vinculante; capex vira ativo de longa-duração contra premissa de curta-duração (risco de bolha).
- **Evidência:** **30-50%** dos data centers grandes de 2026 atrasados/cancelados; 11 GW anunciados sem construção; filas de interconexão **4-7 anos**; "7 GW gap" (12-16 planejado vs ~5 em construção); utilities questionando publicamente se o pipeline de demanda é real. [Spheron/Sightline](https://www.spheron.network/blog/ai-data-center-power-constraints-2026/)
- **Proposta:** métrica `datacenter_capacity_delay_pct` (infrastructure module — já mencionado no seed).

### Candidate 3: `ai_financing_fragility` — NOVO (nenhum lado modela a ESTRUTURA de financiamento)
- **Mecanismo:** financiamento circular Nvidia→neocloud→hyperscaler infla demanda aparente; GPU-collateralized debt cujo custo depende de quem assina o off-take; distress num nó propaga.
- **Evidência:** Nvidia com stake de 7% na CoreWeave + $6.3B de compra + funding Nscale/Nebius; loans GPU-colateral: CoreWeave $7.5B, Fluidstack $10B; OpenAI comprometeu **$300B Oracle + $38B Amazon + $22B CoreWeave**; neocloud revenue lag capex **2:1**; SemiAnalysis: backstop da Nvidia → mercado de **$7T de dívida AI**. CoreWeave unsecured 10% vs Meta-backed 5.9% (o spread É o risco de execução precificado). [Quinn Emanuel](https://www.quinnemanuel.com/the-firm/publications/client-alert-emerging-litigation-risks-in-financing-ai-data-centers-boom/), [io-fund](https://io-fund.com/ai-stocks/nvidia-coreweave-nebius-circular-financing-gpu-boom)
- **Proposta:** módulo `credit` estendido ou novo `infrastructure_financing`; métrica `neocloud_revenue_capex_ratio`, `gpu_collateral_debt_outstanding`.

## Bubble-timing signals (o frame do vídeo Jick, checado)
- **Capex NÃO puxou pra trás ainda:** hyperscaler capex **$725B em 2026, +77% YoY** (Amazon $200B, MSFT $190B, Alphabet $175-185B, Meta $125-145B). [Tom's Hardware](https://www.tomshardware.com/tech-industry/big-tech/big-techs-ai-spending-plans-reach-725-billion)
- **MAS a paciência do investidor rachou:** **Meta −9.25%** no dia do guide de capex ("primeira rebelião real"); Google/Amazon/MSFT venderam pós-earnings; FCF da Amazon virando negativo. O sinal que a skill/vídeo procuram (1ª hyperscaler premiada por cortar) ainda não veio — mas o oposto (punida por gastar) já apareceu.

## Confirming evidence (citadel — fricção limita dano)
- 80% dos trabalhadores bypassam/rejeitam AI tools; 51 dias/ano perdidos em fricção (+42%); ganho Goldman (40-60min/dia) quase cancela.
- 95% dos pilots sem P&L; 80% do trabalho pilot→prod é data/governance/integração; Gartner 40% dos agentic cancelados até 2027.
- Goldman: displacement mild (~0.5% desemprego, 2.5% risco); headcount cresce MAIS nas empresas mais expostas (job expander no leading edge).

## Challenging evidence (contra citadel)
- Intermediation é onde citrini ganha forte: SaaSpocalypse −$1T, build-vs-buy 35%/78%, vertical-AI upstarts +400% a 80% do ACV.
- Labor softening real (openings máx-de-década baixa, entry-level, −16k/mês Goldman) — temperado por "AI washing".
- Demand cooling (1.6% vs 3.6%) e credit rising (4.8% delinq) — ambos emergentes, ainda bifurcados/não-sistêmicos.

## Veredito honesto (a leitura)
Nenhuma bolha "estourou", e a evidência NÃO confirma a versão apocalíptica do vídeo. O que confirma:
1. **A tese de deflação (China/open-source) saiu de especulação pra fato mensurável** — é o desenvolvimento mais forte desde o último snapshot e o que mais reframe o debate (>30% dos tokens US em modelos chineses; "AI deflation" já no proxy India IT). Ataca a premissa de lucro trilionário mais que a de labor.
2. **Citadel segue certo no near-term labor** (fricção institucional é real e cara), então o "colapso de emprego" não está nos dados — é hiring-freeze + entry-level + K-shaped, não terminações em massa.
3. **O risco sistêmico real não está em citadel nem citrini** — está no financiamento circular (Nvidia/neocloud/$7T debt) + power bottleneck (30-50% dos DCs atrasados). Aí mora o gatilho de bolha, não no "capex parar".

## Round 2 — pesquisa mais funda (6 queries) + módulos implementados

**Módulos NOVOS no código** (`metric_definitions.py`): `deflation` (6 métricas), `financing_fragility` (2), + `power_bottleneck` estendendo `infrastructure` (2). Cada um score em **linha própria** (não dobrado em citadel/citrini).

### open_source_deflation — é DURÁVEL, não só loss-leader (falsificação feita)
- **A deflação é estrutural, não subsídio temporário:** MoE é o piso — GLM-5.2 ativa **40B de 744B params** → custo de servir = modelo denso de 40B (redução de custo de inferência **90-97%**). DeepSeek tornou o desconto do V4-Pro **permanente**; Z.ai até **AUMENTOU** preço (escolheu sustentável). Subsídio existe (free tiers, luz -50% Gansu/Guizhou, Xiaomi cross-subsidy $8.7B, Xiaomi cortou 99%) mas é camada, não a explicação toda.
- **Chegou aos PROVEDORES US:** Anthropic **cortou preço 30/jun** (Sonnet 5 $2/$10 vs Opus $5/$25); OpenAI avaliando (Altman: "costs a huge issue"). "Enquanto a China ficar open-source, o piso do preço cai rumo a zero — recuperar margem é um problema de matemática sem solução limpa."
- **Capability convergiu:** Stanford AI Index — gap US-China **2.7%** (Arena); Artificial Analysis — Opus 4.8 55.7 vs GLM-5.2 51 = ~4.7, encolhendo.
- **O CONTRA real (Jevons — implementei como falsifier):** consumo pago **~24.000B tokens/mês (mai'26), ~19x** desde fim-2024, mesmo com preço $1.90→$0.65/M. Deflação pode **expandir** o mercado, não matar. Isto impede o read apocalíptico.
- **Fonte:** [CNBC](https://www.cnbc.com/2026/07/07/chinese-ai-models-costs-us-openai-anthropic.html), [Rest of World](https://restofworld.org/2026/when-americans-choose-chinese-ai/), [USCC report](https://www.uscc.gov/sites/default/files/2026-03/Two_Loops--How_Chinas_Open_AI_Strategy_Reinforces_Its_Industrial_Dominance.pdf), [Stanford AI Index](https://thenextweb.com/news/stanford-ai-index-2026-china-us-performance-gap), [WSJ via cryptobriefing](https://cryptobriefing.com/openai-anthropic-pricing-pressure-chinese-ai/)

### power_bottleneck — quantificado
IEA: DC global 415→945 TWh (2024→2030), 2x+; US = 45% do global, +130% até 2030; DC = 4.4%→6.7-12% da eletricidade US. **~20% dos projetos em risco de atraso** (IEA); PJM queue **2.600 GW pendentes, espera >5 anos**; linhas de transmissão até 8 anos. [IEA](https://www.iea.org/reports/energy-and-ai/executive-summary), [Latitude/IEA](https://www.latitudemedia.com/news/report-global-grid-congestion-puts-20-of-data-center-projects-at-risk/)

### ai_financing_fragility — quantificado
DC global pode chegar a **$7T até 2030** (McKinsey). Dívida AI-DC >$200bn (2025) → IG issuance pode passar **$2T em 2026**. CoreWeave: 3 loans GPU-backed **$12.4bn** + $8.5bn IG. OpenAI comprometeu **$1.09T** (Oracle $300B/AMD $90B/AWS $38B), reset pra ~$600B/2030, vs **$13.1B receita** = ~46x; CFO teme "$1.5T can't be paid". Fed: 25% dos loans banco→NBFI vão a private credit; 4 senadores + BIS + Treasury alertaram. Paralelo: fibra-ótica 2000 destruiu $2T. [Goldman](https://www.goldmansachs.com/insights/articles/tracking-trillions-the-assumptions-shaping-scale-of-the-ai-build-out), [SemiAnalysis](https://newsletter.semianalysis.com/p/nvidia-gpu-debt-backstop-unleashes), [ZeroHedge/CFO](https://www.zerohedge.com/markets/openai-misses-revenue-user-targets-cfo-fears-15-trillion-commitments-cant-be-paid)

### O bull case (falsificação da bolha) — real também
MSFT: AI run-rate **$37B (+123%)**, RPO **$627B (+99%)**, Azure **+40%** — MAS ex-OpenAI o RPO cresceu só **~26%** (OpenAI = 45% do RPO do Azure = concentração), Copilot **<5%** de penetração. Margens Mag-7 >25% (≠ 1999). Sequoia: **gap de receita de $600B/ano, alargando**. Consenso honesto: **os dois lados estão certos ao mesmo tempo; cronometrar o estouro é mais difícil que afirmar que ele existe.** [GeekWire/MSFT](https://www.geekwire.com/2026/microsoft-tops-wall-street-expectations-reports-accelerating-azure-growth-and-37b-ai-run-rate/), [Fortune](https://fortune.com/2026/06/08/ai-boom-tech-stocks-bubble-fears-earnings-growth-chipmakers-ipo/)

### A verdade da realidade (leitura de 2 lados, sem torcida)
A deflação (China/open-source) é o desenvolvimento novo mais forte e é **estrutural** (não some) — já força os provedores US a cortar preço, o que é o sinal mais direto de que a premissa "lucro trilionário garantido" está errada. **MAS** Jevons (19x volume) + receita real da MSFT impedem o colapso óbvio: barato-e-abundante pode crescer o bolo. O risco de bolha REAL não está em labor nem em "capex parar" — está no **financiamento circular ($7T dívida, OpenAI 46x)** + **power bottleneck (20-50% dos DCs atrasados)**. É aí que um credit-event dispara, não no vídeo.

## Sources
(links inline acima — CNBC, NY Fed, MIT/Terminal-X, Fortune, McKinsey, Morgan Stanley, CIO, Retool, Tom's Hardware, Quinn Emanuel, Spheron/Sightline, The Register, Epoch AI, VantageScore, Challenger)

---
_Capability decomposition: session-context ~10% · Bradford-mandated falsification ~35% · base parametric ~5% (interpretação, não claims). OK._
