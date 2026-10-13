# Public repository readiness audit — October 12, 2026 (Pacific)

All 83 public non-fork repositories were inventoried and checked for their actual purpose, setup, tests, missing implementation, and demonstration readiness. This is a coverage report, not a claim that all 83 products work end to end. Forks and private repositories were excluded.

Functional changes are proposed on separate review branches. No merge, release, deployment, GIF or video is claimed. A recording must use the final tested source tree and show the actual interface; changed code invalidates older capture evidence. Two other functional sessions acknowledged ownership handoffs. No separate media worker or named video skill could be found.

## Verified improvements

| Repository | Pull request | Tested source tree |
|---|---|---|
| jadenfix/solanatools | [#1](https://github.com/jadenfix/solanatools/pull/1) | `60f3f1316a7191ab6b1319f4d499a12a3c3b277a` |
| jadenfix/trading | [#23](https://github.com/jadenfix/trading/pull/23) | `ba0a87e619e17db7090adae2986abbe601342545` |
| jadenfix/jadenfix.github.io | [#2](https://github.com/jadenfix/jadenfix.github.io/pull/2) | `4800656586ae6dc43ce0e94e80a43c89d1efaa16` |
| jadenfix/matteoshafer.github.io | [#1](https://github.com/jadenfix/matteoshafer.github.io/pull/1) | `bf0508e96e08509b63540a9ee9f39dc3fc0f59a2` |
| jadenfix/roe-ai- | [#1](https://github.com/jadenfix/roe-ai-/pull/1) | `43b2445195a4766e227f3551f271ae7d8b88969e` |
| jadenfix/1115_hack | [#2](https://github.com/jadenfix/1115_hack/pull/2) | `d153d4b9d0a085ec45d56008f42e9b8801f0ce4b` |
| jadenfix/NLP | [#1](https://github.com/jadenfix/NLP/pull/1) | `08cad3a2e871b7ae5cec5da31d8cbedffeda9eed` |
| jadenfix/8257-tools | [#2](https://github.com/jadenfix/8257-tools/pull/2) | `910ea1965dc2cf2d83da87b86c3dd159e92197a3` |
| jadenfix/cpp_fundamentals | [#3](https://github.com/jadenfix/cpp_fundamentals/pull/3) | `45d1dc75f5ff8157528475719b71dea3f59c5476` |
| jadenfix/financial_cpp_copy | [#1](https://github.com/jadenfix/financial_cpp_copy/pull/1) | `a05fbc2db23331d4837ffa8de5de47c96f534b73` |
| jadenfix/MiniGPTEngine-CPP | [#1](https://github.com/jadenfix/MiniGPTEngine-CPP/pull/1) | `91ff9c46109c038e36282021b5d1f6d596af2f82` |
| jadenfix/supervised_fine_tuning | [#1](https://github.com/jadenfix/supervised_fine_tuning/pull/1) | `ba20858182a753764d75e9da7d2b6c13e9477cbe` |
| jadenfix/trading_website | [#4](https://github.com/jadenfix/trading_website/pull/4) | `2f9aaf250c63644f441bf222bd5dde10590c92f8` |
| jadenfix/InvoiceFlowAgent | [#2](https://github.com/jadenfix/InvoiceFlowAgent/pull/2) | `3ea78eab69bd664dfd2637669618a27a64b1efb1` |
| jadenfix/DRL4MM | [#3](https://github.com/jadenfix/DRL4MM/pull/3) | `7f762abd115760fedfb6712b4773b8c8dc10b3ea` |
| jadenfix/categorization_embeddings_sementic_search | [#2](https://github.com/jadenfix/categorization_embeddings_sementic_search/pull/2) | `80c056e6718c700ea50b48cb8d79743e230dd671` |
| jadenfix/EmotiFuse | [#1](https://github.com/jadenfix/EmotiFuse/pull/1) | `1475215329b37d5dbbe4107f8183aeae17865cb2` |
| jadenfix/DF | [#1](https://github.com/jadenfix/DF/pull/1) | `87ce6f338c0972ab5a514eb4b8f275b253f08515` |
| jadenfix/alpaca | [#2](https://github.com/jadenfix/alpaca/pull/2) | `2420e0cb165176adc210a23ca72b9ebdb7e3dfbc` |
| jadenfix/CreditAssignment-LongHorizon | [#2](https://github.com/jadenfix/CreditAssignment-LongHorizon/pull/2) | `2aad63875cc0f1bb4a02c19fa83ae8f9f72f5730` |
| jadenfix/hackathon | [#1](https://github.com/jadenfix/hackathon/pull/1) | `cb10d393516f16901b96372d0fa1f93cc9a3820e` |
| jadenfix/OrbitAgents | [#2](https://github.com/jadenfix/OrbitAgents/pull/2) | `ac0c66bf159e5cc3bd3e83c784f17c0745160e6a` |
| jadenfix/ruby | [#1](https://github.com/jadenfix/ruby/pull/1) | `3cbbed4061c61772f6d195f7e5fba85e30665d8e` |

The detailed machine-readable evidence is [public-repo-readiness-2026-10-12.json](public-repo-readiness-2026-10-12.json). Full CI is explicitly blocked for DF and InvoiceFlowAgent; their scoped fixes are not merge/readiness claims.

## Priority holds

- HumanVoiceAI fabricates emotion labels from file size/random confidence. A frontend build cannot validate model inference.
- MiniGPT trained inference still uses canned response maps; only the new attention kernel has verified numeric behavior.
- DRL4MM requires real historical full-session validation under Rules.md. The Bellman regression is verified; synthetic market performance is not authorized.
- Five repository checkouts have no tracked content: JaneStreetTradingComp, stochastic512, resume, xgbitcoin, satellite_deeplearning. Historical coursework/design-only repositories require different completion criteria than runnable products.
- Live provider, cloud, exchange, full trained-model, GPU and hardware lanes remain held unless explicitly covered by the evidence below.
- Rusty passed 24 core tests with Rust 1.99; its full coding-agent workflow and pinned-toolchain compatibility are not established.
- Full simulation-theory pytest was interrupted during expensive exact solvers after 19 minutes; 11 targeted physics/Bayesian/algorithmic tests pass.

## Repository coverage

| Repository | Classification | Actual status | Recording gate |
|---|---|---|---|
| [jadenfix/1115_hack](https://github.com/jadenfix/1115_hack) | application | structure inspected; runtime unverified | Ready for actual frontend/CLI capture at tested SHA; full deployment/provider workflows explicitly excluded |
| [jadenfix/145](https://github.com/jadenfix/145) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/145-Project-](https://github.com/jadenfix/145-Project-) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/8257-tools](https://github.com/jadenfix/8257-tools) | source | lint/build/15 unit tests/16 desktop-mobile E2E tests passed | fixture frontend interaction lane only; no real blockchain/network/signing/payment integrations |
| [jadenfix/advanced_econometrics_I](https://github.com/jadenfix/advanced_econometrics_I) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/advanced_econometrics_II](https://github.com/jadenfix/advanced_econometrics_II) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/advanced_econometrics_III](https://github.com/jadenfix/advanced_econometrics_III) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/agentic_ai_HF](https://github.com/jadenfix/agentic_ai_HF) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/AI_and_Machine_Learning](https://github.com/jadenfix/AI_and_Machine_Learning) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/AICH](https://github.com/jadenfix/AICH) | documentation | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/alpaca](https://github.com/jadenfix/alpaca) | source | structure inspected; runtime unverified | verified seeded offline research only; both live market transport and broker remain unfinished |
| [jadenfix/android-simulator](https://github.com/jadenfix/android-simulator) | source | archived_tests_pass | blocked_pending_actual_browser_e2e_or_live_prerequisites |
| [jadenfix/arrha](https://github.com/jadenfix/arrha) | source | verification_blocked | held; recorded checks do not establish full product E2E |
| [jadenfix/backpacking-eastern-sierra](https://github.com/jadenfix/backpacking-eastern-sierra) | source | core_tests_and_build_pass | blocked_pending_actual_browser_e2e_or_live_prerequisites |
| [jadenfix/Bayesian-Neural-Network-for-CIFAR-10-Image-Classification](https://github.com/jadenfix/Bayesian-Neural-Network-for-CIFAR-10-Image-Classification) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/Bayesian__Stats](https://github.com/jadenfix/Bayesian__Stats) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/business-documents](https://github.com/jadenfix/business-documents) | source | dependency_install_environment_blocked | blocked_pending_actual_browser_e2e_or_live_prerequisites |
| [jadenfix/categorization_embeddings_sementic_search](https://github.com/jadenfix/categorization_embeddings_sementic_search) | source | portable configuration fixed; offline loading/ranking verified | local stored-results/candidate-ranking only |
| [jadenfix/causal_machinelearning](https://github.com/jadenfix/causal_machinelearning) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/core-domains](https://github.com/jadenfix/core-domains) | documentation | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/cpp_fundamentals](https://github.com/jadenfix/cpp_fundamentals) | source | ready | allow verified lane only |
| [jadenfix/cradle](https://github.com/jadenfix/cradle) | source | verification_blocked | held; recorded checks do not establish full product E2E |
| [jadenfix/CreditAssignment](https://github.com/jadenfix/CreditAssignment) | source | local collection verified | local diagnostic benchmark only |
| [jadenfix/CreditAssignment-LongHorizon](https://github.com/jadenfix/CreditAssignment-LongHorizon) | source | minimum-Flax compatibility fixed; unit/integration pass | local NanoLM/replay fixtures only |
| [jadenfix/Daytuh](https://github.com/jadenfix/Daytuh) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/DF](https://github.com/jadenfix/DF) | source | lazy_vision_provider_fix_tested; full CI still blocked | blocked_pending_actual_browser_e2e_or_live_prerequisites |
| [jadenfix/document_parsing_product_demo](https://github.com/jadenfix/document_parsing_product_demo) | source | local_fix_superseded_by_external_PR1_pending_comparison | blocked_pending_actual_browser_e2e_or_live_prerequisites |
| [jadenfix/dreamForge](https://github.com/jadenfix/dreamForge) | source | frontend_build_pass_api_tests_failed | blocked_pending_actual_browser_e2e_or_live_prerequisites |
| [jadenfix/DRL4MM](https://github.com/jadenfix/DRL4MM) | source | Bellman target regression verified; historical E2E blocked | BLOCKED: Rules.md requires real historical full-session order replay |
| [jadenfix/dynamic_stochastic_modeling](https://github.com/jadenfix/dynamic_stochastic_modeling) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/ecosystem](https://github.com/jadenfix/ecosystem) | source | checkout resolution fixed; 2 regression tests pass; actual uniformity/cross-product E2E still fails | held; live cross-product scenarios unwired |
| [jadenfix/EmotiFuse](https://github.com/jadenfix/EmotiFuse) | source | audio/model pipeline repaired | synthetic random-weight model smoke only |
| [jadenfix/eth](https://github.com/jadenfix/eth) | source | verification_blocked | held; recorded checks do not establish full product E2E |
| [jadenfix/eth-tools](https://github.com/jadenfix/eth-tools) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/eval_mvp](https://github.com/jadenfix/eval_mvp) | source | unit suite passed | blocked pending verified runnable path |
| [jadenfix/financial_cpp](https://github.com/jadenfix/financial_cpp) | source | checkout_blocked | hold |
| [jadenfix/financial_cpp_copy](https://github.com/jadenfix/financial_cpp_copy) | source | research_lane_ready | allow verified lane only |
| [jadenfix/FullStack-Bench](https://github.com/jadenfix/FullStack-Bench) | source | 83 scoped admission/budget/quality/replay/receipt tests passed | held; scoped harness logic only,not full benchmark performance |
| [jadenfix/gemhub](https://github.com/jadenfix/gemhub) | documentation | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/hackathon](https://github.com/jadenfix/hackathon) | source | offline energy cycle repaired and verified | synthetic offline CLI forecast/bid/allocation/cooling/dispatch cycle only |
| [jadenfix/HumanVoiceAI](https://github.com/jadenfix/HumanVoiceAI) | source | frontend_build_pass | blocked_pending_actual_browser_e2e_or_live_prerequisites |
| [jadenfix/InftyThink](https://github.com/jadenfix/InftyThink) | source | CLI and tiny model forward/gradient verified | blocked for full reasoning/training until checkpoint/data experiment verified |
| [jadenfix/insurance-front-site](https://github.com/jadenfix/insurance-front-site) | documentation | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/InvoiceFlowAgent](https://github.com/jadenfix/InvoiceFlowAgent) | source | frontend_workflow_repair_tested; full CI still blocked | blocked_pending_actual_browser_e2e_or_live_prerequisites |
| [jadenfix/jadenfix](https://github.com/jadenfix/jadenfix) | documentation | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/jadenfix.github.io](https://github.com/jadenfix/jadenfix.github.io) | frontend | structure inspected; runtime unverified | Ready for actual frontend/CLI capture at tested SHA; full deployment/provider workflows explicitly excluded |
| [jadenfix/JaneStreetTradingComp](https://github.com/jadenfix/JaneStreetTradingComp) | empty | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/KILN](https://github.com/jadenfix/KILN) | source | environment_blocked | hold |
| [jadenfix/machine_learning](https://github.com/jadenfix/machine_learning) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/masters_thesis_cold_runs](https://github.com/jadenfix/masters_thesis_cold_runs) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/matteoshafer.github.io](https://github.com/jadenfix/matteoshafer.github.io) | frontend | structure inspected; runtime unverified | Ready for actual frontend/CLI capture at tested SHA; full deployment/provider workflows explicitly excluded |
| [jadenfix/mft_crypto_research](https://github.com/jadenfix/mft_crypto_research) | source | notebook_only_unverified | hold |
| [jadenfix/MiniGPTEngine-CPP](https://github.com/jadenfix/MiniGPTEngine-CPP) | source | kernel_ready_full_model_blocked | allow verified lane only |
| [jadenfix/NLP](https://github.com/jadenfix/NLP) | research/coursework | structure inspected; runtime unverified | Ready for actual frontend/CLI capture at tested SHA; full deployment/provider workflows explicitly excluded |
| [jadenfix/OrbitAgents](https://github.com/jadenfix/OrbitAgents) | source | typecheck/build/7 tests passed;13 existing lint warnings | blocked pending actual browser interaction and required live services |
| [jadenfix/palette](https://github.com/jadenfix/palette) | source | verification_blocked | held; recorded checks do not establish full product E2E |
| [jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-](https://github.com/jadenfix/Predictive-Stochastic-Modeling-for-Financial-Markets-) | source | structure inspected; runtime unverified | held; no complete workflow verification |
| [jadenfix/python_crypto_trading_engine](https://github.com/jadenfix/python_crypto_trading_engine) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/random_cpp_doesnt_work](https://github.com/jadenfix/random_cpp_doesnt_work) | source | blocked | hold |
| [jadenfix/remi](https://github.com/jadenfix/remi) | source | verification_blocked | held; recorded checks do not establish full product E2E |
| [jadenfix/ReplayKit](https://github.com/jadenfix/ReplayKit) | source | exclusive collaborating-session owner; final tested release awaited | held until owning session publishes exact final revision and evidence |
| [jadenfix/resume](https://github.com/jadenfix/resume) | empty | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/rl](https://github.com/jadenfix/rl) | source | partial_verification | hold |
| [jadenfix/roe-ai-](https://github.com/jadenfix/roe-ai-) | frontend | structure inspected; runtime unverified | Ready for actual frontend/CLI capture at tested SHA; full deployment/provider workflows explicitly excluded |
| [jadenfix/ruby](https://github.com/jadenfix/ruby) | source | clean install,zero-warning lint,and strict production build pass | blocked pending actual browser interaction and required live services |
| [jadenfix/rusty](https://github.com/jadenfix/rusty) | source | 24 Rust core tests passed on Rust 1.99 override | held; full agent/model/provider/tool E2E not verified |
| [jadenfix/satellite_deeplearning](https://github.com/jadenfix/satellite_deeplearning) | empty | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/simulation-theory](https://github.com/jadenfix/simulation-theory) | source | 11 scoped tests passed; full suite interrupted during expensive exact solver after 19 minutes | scoped research results only; full claim registry and solver suite not verified |
| [jadenfix/smartpaydoc](https://github.com/jadenfix/smartpaydoc) | source | exclusive collaborating-session owner; final tested release awaited | held until owning session publishes exact final revision and evidence |
| [jadenfix/solanatools](https://github.com/jadenfix/solanatools) | source | offline replay verified | offline synthetic spot replay only |
| [jadenfix/space-simulation-engine](https://github.com/jadenfix/space-simulation-engine) | source | ready | allow verified lane only |
| [jadenfix/startup](https://github.com/jadenfix/startup) | source | exclusive collaborating-session owner; final tested release awaited | held until owning session publishes exact final revision and evidence |
| [jadenfix/stochastic-site](https://github.com/jadenfix/stochastic-site) | source | exclusive collaborating-session owner; final tested release awaited | held until owning session publishes exact final revision and evidence |
| [jadenfix/stochastic512](https://github.com/jadenfix/stochastic512) | empty | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/supervised_fine_tuning](https://github.com/jadenfix/supervised_fine_tuning) | source | gpu_verification_blocked | hold |
| [jadenfix/temp.js](https://github.com/jadenfix/temp.js) | source | verification_blocked | held; recorded checks do not establish full product E2E |
| [jadenfix/tempo](https://github.com/jadenfix/tempo) | source | verification_blocked | held; recorded checks do not establish full product E2E |
| [jadenfix/tempOS](https://github.com/jadenfix/tempOS) | source | verification_blocked | held; recorded checks do not establish full product E2E |
| [jadenfix/trading](https://github.com/jadenfix/trading) | source | paper_control_layer_verified | held; recorded checks do not establish full product E2E |
| [jadenfix/trading_research](https://github.com/jadenfix/trading_research) | source | python_lane_ready_native_blocked | allow verified lane only |
| [jadenfix/trading_website](https://github.com/jadenfix/trading_website) | source | frontend_build_fix_tested | blocked_pending_actual_browser_e2e_or_live_prerequisites |
| [jadenfix/WS](https://github.com/jadenfix/WS) | research/coursework | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
| [jadenfix/xgbitcoin](https://github.com/jadenfix/xgbitcoin) | empty | structure inspected; runtime unverified | blocked until final tested SHA and real browser or research demonstration |
