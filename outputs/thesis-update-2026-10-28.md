# Thesis update — 2026-10-28

> Refresh após o update de 2026-07-07 (~16 semanas). Protocolo `thesis-update`: toda claim com URL fresca via WebSearch; paramétrico banido. Plano em `outputs/thesis-update-2026-10-28/query-plan.md` (o gerador repetiu 5 queries; trocadas por outras da mesma intenção, registrado no plano).
> Pendentes no dia: Microsoft e Alphabet reportam Q3 hoje após o fechamento, Amazon amanhã (29/10); BLS produtividade Q3 e NY Fed household debt Q3 saem no início de novembro.

## Current regime
- **Previous lean (07/07):** citadel no labor; citrini forte só em intermediation; peso do sinal nas emergentes (deflation, financing fragility, power).
- **New lean:** `leaning_citadel` no labor agregado (ainda "low-hire, low-fire"); citrini ganha devagar por três canais (jovens, crédito de software, renda do trabalho). **O movimento de regime está na tese emergente `ai_financing_fragility`: passou de risco estrutural a estresse de mercado observado.**
- **Confidence shift:** financing_fragility ↑↑ (de candidato a estresse com preço de mercado); open_source_deflation ↑ (Chinese tokens 4,2x os US no OpenRouter); power_bottleneck ↑ (freio regulatório no Texas); citadel-labor estável; citrini-intermediation ↑ (crédito privado de software).

## Bradford verification
- Confirming (citadel): 7 queries (35%) — GS/JPM produtividade, SaaS resiliência, augmentation, tech hiring, BLS produtividade, enterprise ROI, Engels' pause
- Challenging (citrini): 7 queries (35%) — India IT Q2 FY27, Brynjolfsson canaries, desemprego/recém-formados, PE SaaS distress, SaaS seat pricing, Challenger, NY Fed/consumo
- Adjacent-possible: 6 queries (30%) — power, token share chinês, financiamento circular, capex Q3, export controls, AI bubble/selloff
- **Bradford satisfeito: sim** (35% challenging ≥ 25%; 30% adjacent ≥ 20%). Plano previa 8 challenging; 1 foi coberta pela query de tech hiring.

## Metric updates (por módulo)
| Módulo | Sinal | Valor | Leitura | Fonte |
|---|---|---|---|---|
| productivity | Produtividade nonfarm Q2'26 | +1,4% anualizado, **+2,2% YoY**; tendência do ciclo 2,1% | ↑ citadel (ganho real) | [BLS](https://www.bls.gov/opub/ted/2026/productivity-up-2-2-percent-from-second-quarter-2025-to-second-quarter-2026.htm), [BLS release](https://www.bls.gov/news.release/pdf/prod2.pdf) |
| productivity / distribuição | **Labor share nonfarm 52,8% (mínima da série, desde 1947)**; lucro unitário não-financeiro +43% no trimestre; salário real/hora −3,3% (choque de energia) | ganho vai para capital | [BLS release](https://www.bls.gov/news.release/pdf/prod2.pdf), [Productivity Lab](https://lab.productivity.ac.uk/insights/q2-2026-us-productivity-growth-revival-continues/) |
| productivity (forecast) | GS: AI +15% de produtividade em 10 anos; JPM AM: produtividade do trabalho 2,2%/ano | ↑ citadel (longo prazo) | [Fortune/GS](https://fortune.com/2026/10/22/goldman-sachs-forecast-how-many-jobs-lost-to-ai-9-percent/), [JPM AM](https://am.jpmorgan.com/at/en/asset-management/institutional/insights/portfolio-insights/ltcma/a-brighter-productivity-outlook-for-the-ai-era/) |
| labor | Payroll set +29k; desemprego **4,2%**; U-6 7,6% (mínima desde jan/25); "low-hire, low-fire" | ↔ citadel | [CNBC](https://www.cnbc.com/2026/10/02/jobs-report-september-2026.html), [St. Louis Fed](https://www.stlouisfed.org/on-the-economy/2026/oct/flash-report-unemployment-rises-slightly-job-growth-slows-september) |
| labor (jovens) | Brynjolfsson: emprego 22–25 anos em ocupações expostas **19% abaixo** dos pares (era ~13–15%); via menos contratação; sem deslocamento amplo | ↑ citrini (lento) | [Stanford DEL](https://digitaleconomy.stanford.edu/news/canariesaug26/) |
| labor (forecast) | GS: AI pode deslocar **9%** dos trabalhadores na transição (era 6–7%), concentrado na próxima recessão | ↑ citrini condicional | [Fortune/GS](https://fortune.com/2026/10/22/goldman-sachs-forecast-how-many-jobs-lost-to-ai-9-percent/) |
| labor (cortes) | Challenger: AI citada em **120.136** cortes no ano (21%, 1º motivo), mas só 3.961 (9%) em setembro | ↔ (desacelerou) | [Challenger set/26](https://www.challengergray.com/wp-content/uploads/2026/10/Challenger-Report-September-2026.pdf) |
| labor (software) | Indeed software postings +21% YoY, ainda −22% vs fev/2020; 71% do aumento em sênior; entry-level 4,5% das vagas | ↔ (recupera pelo sênior) | [Full Scale/Indeed](https://fullscale.io/blog/developer-hiring-trends/) |
| labor (proxy India IT) | Big-5 +13.918 pessoas no Q2 FY27 (vs −1.606 há 1 ano); TCS: ~50% dos contratos repreçados por AI, valor −10–20%; Infosys guia FY27 1–2% | headcount ↑ mas deflação de preço | [Zee Biz](https://www.zeebiz.com/companies/news-it-q2-results-fy27-tcs-infosys-hcltech-wipro-tech-mahindra-who-led-in-revenue-profit-ai-guidance-hiring-404539), [AIM](https://analyticsindiamag.com/it-services/infosyss-52-billion-deal-wins-fail-to-lift-fy27-outlook) |
| diffusion | BCG: ~50% das empresas geram valor com AI; WRITER: 29% veem ROI significativo, 48% "decepção"; EY: governança atrás da implantação | ↔ (fricção persiste) | [BCG](https://www.bcg.com/publications/2026/the-formula-for-agentic-ai-value), [WRITER](https://writer.com/blog/enterprise-ai-adoption-2026/), [EY](https://www.ey.com/en_us/newsroom/2026/09/ey-survey-finds-that-autonomous-ai-implementation-outpaces-oversight-yielding-an-ai-governance-gap) |
| intermediation | SAP Q3 cloud +25% cc (ERP resiliente); ServiceNow: 50% do novo negócio sem seat, margem bruta de assinatura 83%→80,5%; Workday cita headcount reduction como risco no 10-K | ↑ citrini no modelo de preço | [Investing/SAP](https://www.investing.com/news/transcripts/earnings-call-transcript-sap-tops-q3-2026-estimates-as-cloud-growth-accelerates-93CH-4964320), [io-fund](https://io-fund.com/ai-stocks/agentic-ai-squeezing-saas-margins), [SaaSRise](https://www.saasrise.com/news/servicenow-shifts-to-aibased-pricing-as-seat-demand-slumps-57532fe9-5815-4ecb-aed1-ee014e267e81) |
| intermediation (crédito) | BDC distressed +64% YoY para **$6,8B** (89% do aumento em software); bids de loans de software 87,97 vs 96,08 do resto; novos empréstimos secaram, só amend-and-extend | ↑↑ citrini (estresse sem default em massa) | [Forbes](https://www.forbes.com/sites/mayrarodriguezvalladares/2026/10/03/private-credit-and-equity-face-warnings-on-ai-lending-concentration/), [Morningstar/LCD](https://www.morningstar.com/markets/private-credit-software-space-is-becoming-tougher-sell-lenders), [PMI](https://www.privatemarketsinsights.com/post/private-credit-s-q1-2026-stress-stayed-inside-software-loans) |
| demand | Beige Book out: gasto estável, puxado por alta renda; Michigan mínima de 5 meses; Ipsos mínima desde 2011 | ↑ citrini fraco (confundido por energia/juros) | [Fed Beige Book](https://www.federalreserve.gov/monetarypolicy/beigebook202610-summary.htm), [Ipsos](https://ipsos.com/en/ipsos-consumer-confidence-october-2026) |
| credit_housing | Delinquência agregada **4,7%** no Q2 (melhorou de 4,8%); student loans 90+ 10,6%; Q3 sai em novembro | ↔ (não-sistêmico) | [NY Fed](https://www.newyorkfed.org/newsevents/news/research/2026/20260811) |

## Emergent thesis candidates

### `ai_financing_fragility` — de candidato a ESTRESSE OBSERVADO (movimento principal)
- **CoreWeave:** CDS 5 anos passou de **1.100 bps** (nível de distress) em 15/10; bonds 2032 a ~77 centavos; ação −38% em outubro; capex do 1º semestre $14,1B contra caixa operacional $3,7B. [CNBC](https://www.cnbc.com/2026/10/15/coreweave-credit-default-swaps-hit-distress-levels-as-investors-sour-on-ai-debt.html), [CNBC](https://www.cnbc.com/2026/10/19/coreweave-oracle-ai-credit-stress.html)
- **Oracle:** CDS recorde 288→308 bps (era 141 em jan); S&P rebaixou para o último degrau de grau de investimento. **SoftBank** CDS 432 bps. Amazon, Alphabet, Meta e Nvidia com CDS em máximas (ainda baixos). [Securitas](https://www.securitasglobal.com/risk-perspectives/oracle-cds-record-288-basis-points-ai-debt/), [CNBC](https://www.cnbc.com/2026/10/22/ai-debt-and-french-bonds-stress-test.html)
- **Hyperscaler:** Meta Q3 com FCF **negativo pela 1ª vez desde 2012** (capex $34,9B no trimestre), recompra suspensa, nova classe de ação sem voto, ação −7%. Investidores punem "tanto quem corta quanto quem aumenta capex". [Global DC Hub](https://www.globaldatacenterhub.com/p/meta-q3-2026-earnings-capex-cash-equity-raise), [Japan Times/Reuters](https://www.japantimes.co.jp/business/2026/10/26/ai-spending-tech-earnings/)
- **Circularidade:** Sona AM mapeou $3,6T de financiamento AI em 176 deals, ~120 altamente circulares; dívida AI emitida em 2026 > $466B. [Benzinga](https://www.benzinga.com/markets/prediction-markets/26/09/61868516/oracle-coreweave-ai-financing-3-6-trillion)
- **Mercado:** Nasdaq 100 −7% em outubro; STAR 50 chinês −40% (−$480B). [Kathmandu Post/Reuters](https://kathmandupost.com/world/2026/10/27/in-china-the-ai-bubble-has-already-burst), [CNBC](https://www.cnbc.com/2026/10/15/sk-hynix-samsung-softbank-stocks-asia-tech-rout-ai-funding-worries.html)
- **Proposta:** `ai_credit_stress_index` (CDS 5y de CoreWeave, Oracle, SoftBank; preço dos bonds CRWV 2032) no módulo `financing_fragility`; tripwire: CDS de um neocloud > 1.000 bps por 10 dias **(já disparado)**.

### `open_source_deflation` — reforçado
- Semana 19–25/out: modelos chineses processaram **93,5T tokens no OpenRouter, 4,2x os US**; top 5 todos chineses. [Dealroom/Caixin](https://dealroom.co/news/167092-deepseek-jumps-801-as-chinese-ai-models-route-4x-the-us-on-openrouter/)
- Preço dos labs US: GPT-5.6 Luna −80% (jul); GPT-6 ~50% abaixo da geração anterior (set); Claude Haiku 5.5 a $0,10/$0,50 (out). Índice BenchLM: preço frontier −84% vs mar/2023. [CryptoBriefing](https://cryptobriefing.com/openai-anthropic-price-cuts-open-source-ai/), [BenchLM](https://benchlm.ai/llm-pricing-trends)
- **Contra:** DeepSeek subiu alguns preços em até 12x (custos, IPO); OpenRouter é amostra de startups, Google sozinho processa 35–40x o volume dele. Deflação continua estrutural, mas não é monótona.

### `power_bottleneck` — reforçado com freio regulatório
- 30–50% dos 16 GW de capacidade US previstos atrasados ou cancelados; filas de 4–7 anos. [ABC17/Stacker](https://abc17news.com/stacker-technology/2026/10/19/tech-companies-need-more-data-centers-so-why-are-nearly-half-of-all-planned-projects-delayed-or-canceled/)
- **Texas:** governador mandou ERCOT auditar todos os data centers na fila (474 GW, 5x o pico do estado) antes de aprovar novos; BNEF estima atraso de 20% do pipeline US. S&P vê risco de rebaixamento de projetos de data center. [Bloomberg/S&P](https://www.bloomberg.com/news/articles/2026-10-23/data-centers-face-downgrade-risk-amid-local-pushback-s-p-says), [Utility Dive](https://www.utilitydive.com/news/efforts-to-curb-data-center-speculation-gain-ground-across-the-us/830495/)

### `capital_capture` (Engels' pause) — NOVO candidato
- **Mecanismo:** o ganho de produtividade vai para lucro, não para salário, sem desemprego alto. A renda do trabalho encolhe por preço (salário real), não por quantidade (emprego). Citadel acerta no emprego; citrini acerta na renda; nenhum dos dois modela o canal de distribuição.
- **Evidência:** labor share 52,8% (mínima histórica) com produtividade em alta e lucro unitário +43% no Q2. Comentário recorrente de "Engels' pause" em 2026. [BLS](https://www.bls.gov/news.release/pdf/prod2.pdf), [Advisor Perspectives](https://www.advisorperspectives.com/articles/2026/06/01/timing-productivity-benefits-ai-economy), [Computer Weekly](https://www.computerweekly.com/feature/AI-promises-a-productivity-windfall-who-will-reap-the-benefits)
- **Ressalva:** o Q2 teve choque de energia (salário real −3,3%); parte da queda de labor share é preço de energia, não AI. Precisa de 2+ trimestres.
- **Proposta:** métricas `nonfarm_labor_share` (BLS PRS85006173) e `real_hourly_compensation_yoy`; módulo `distribution` ou extensão de `labor`.

### `geopolitical_chip_decoupling` — ativo nos dois lados
- Nvidia diz estar "efetivamente excluída" do data center chinês; share caiu a 34% (IDC). China propôs (16/10) controle de exportação de 23 tecnologias de AI, incluindo LLMs e agentes. [Yahoo/Reuters](https://finance.yahoo.com/technology/ai/articles/u-export-restrictions-drive-nvidia-124325286.html), [Bloomberg](https://www.bloomberg.com/news/articles/2026-10-16/china-proposes-export-controls-on-ai-models-chips-and-agents)

## Confirming evidence (citadel — fricção limita dano)
- Desemprego 4,2%, U-6 na mínima desde jan/25, layoffs baixos ("low-hire, low-fire").
- Produtividade real e acelerando (+2,2% YoY), sem colapso de emprego.
- India IT voltou a contratar (+13.918 no trimestre); software postings +21% YoY.
- Adoção corporativa ainda travada por governança e integração (WRITER, EY, Deloitte).

## Challenging evidence (contra citadel)
- Jovens em ocupações expostas: gap de 19%, crescendo (Brynjolfsson); 42% dos recém-formados subempregados.
- Crédito privado de software em estresse estrutural (BDC distressed +64%).
- Labor share na mínima histórica: o ganho não chega ao salário.
- GS subiu a estimativa de deslocamento para 9% (concentrado na próxima recessão).

## Veredito
1. **O risco mudou de lugar.** Em julho, financiamento circular era "onde a bolha pode estourar". Em outubro, o mercado de crédito começou a precificar isso: CoreWeave em distress, Oracle com CDS recorde, Meta com FCF negativo. É o primeiro estresse financeiro observado ligado à AI. Ainda não é crise: hyperscalers seguem com CDS baixo e receita crescendo.
2. **Citadel segue certo no emprego agregado**, mas o dano aparece por outros canais: menos contratação de jovens, salário real e labor share, e crédito de software. Citrini avança devagar, sem confirmação no consumo agregado.
3. **Deflação de tokens continua o fator estrutural mais forte** e alimenta o item 1: preço caindo pressiona a recuperação do capex financiado com dívida.
4. **Juros e energia confundem tudo:** 10y a 5,19% e inflação acima do esperado. Parte do estresse de crédito e do consumo fraco é macro, não AI.

## O que observar nas próximas 2 semanas
- Microsoft e Alphabet (hoje) e Amazon (29/10): capex 2027 e reação da ação. Uma hyperscaler premiada por cortar capex seria o tripwire de julho.
- CoreWeave: CDS acima de 1.000 bps por mais tempo, ou um amend/extend de dívida.
- BLS produtividade Q3 (início de nov): labor share abaixo de 53% de novo confirma `capital_capture`.
- NY Fed Q3 (início de nov): delinquência acima de 4,8% reabre citrini em credit_housing.

## Sources
Links inline acima (BLS, CNBC, Stanford DEL, Challenger, NY Fed, Fed Beige Book, Forbes, Morningstar, Fortune/Goldman, JPMorgan AM, BCG, WRITER, EY, SAP, ServiceNow, Dealroom/Caixin, BenchLM, Bloomberg, Reuters via Japan Times/Kathmandu Post, Securitas, Benzinga, Utility Dive, Stacker, Zee Biz, Analytics India Mag).

---
_Capability decomposition: session-context ~10% · Bradford-mandated falsification ~35% · base parametric ~5% (interpretação, não claims). OK._
