# Arcen Agent v1.2.1 Release Notes

**Release Date:** September 2, 2026  
**Tag:** `v1.2.1`  
**License:** MIT  
**Release Type:** Feature & Platform Stability Release  

---

## 🌟 Executive Summary

Arcen Agent **v1.2.1** introduces a major feature expansion with **12 new production-grade autonomous skills** covering algorithmic trading, marketing automation, business growth intelligence, competitive research, and Web3/crypto analytics. In addition, this release delivers complete fixes to the **Windows PowerShell installer** (`Install-NodeDeps`, `Copy-ConfigTemplates`), deterministic dependency management via `uv`, and comprehensive automated test coverage across all supported platforms.

---

## 🚀 Key Highlights & New Features

### 1. 📈 Algorithmic Trading & Market Analytics
- **Strategy Backtester (`optional-skills/trading/backtester`):**
  - High-performance historical backtesting engine for four core strategies:
    - **SMA Crossover (`sma_cross`):** Momentum trend following.
    - **RSI Mean-Reversion (`rsi_meanrev`):** Oversold/overbought recovery.
    - **MACD Cross (`macd`):** Signal & histogram crossover.
    - **Bollinger Bounce (`bollinger`):** Band mean-reversion.
  - Multi-market public OHLCV data integration (Binance for crypto, Yahoo Finance for stocks & forex).
  - Parameter grid optimization with top-N ranking and performance metrics (Total Return %, Max Drawdown %, Win Rate %, Trade Log).
  - Standard-library-only execution with zero external dependencies and CSV export.

- **Chart & Market Context Analyzer (`optional-skills/trading/chart-analyzer`):**
  - Automated technical analysis suite deriving RSI-14, MACD, Bollinger Bands, ATR-14, and 20-period volume ratios.
  - Algorithmic support & resistance level detection via swing-high/swing-low clustering.
  - Emits structured JSON market context ready for agent reasoning and narrative generation.

---

### 2. 🎯 Marketing Automation & Lead Generation
- **Influencer & Campaign Analyzer (`optional-skills/marketing/influencer-analyzer`):**
  - Ingests creator rosters, evaluates engagement rate and CTR against product briefs, scores copywriting hook strength, and outputs ranked multi-tier campaign roadmaps.
- **Marketing Automation Hub (`optional-skills/marketing/marketing-automation-hub`):**
  - Workspace-backed multi-channel content calendar planner (social, newsletters, blog, ads, cold outreach).
  - Centralized performance tracking aggregating impressions, clicks, conversions, spend, revenue, ROAS, and CPA with automated growth insights.
- **B2B Lead Generation Pipeline (`optional-skills/marketing/b2b-lead-generation`):**
  - End-to-end prospect enrichment, heuristic email verification (disposable domain & role-account filtering), 0–100 firmographic/intent scoring, and multi-touch outreach cadences with CRM-ready CSV/JSON export.

---

### 3. 💼 Business Growth & E-Commerce Strategy
- **Business Growth Intelligence (`optional-skills/business/growth-intelligence`):**
  - Complete SaaS & business unit economics engine: CAC, LTV, LTV:CAC ratio, churn %, payback months, NRR, and customer growth rates.
  - Multi-domain health checks and prioritized 90-day actionable execution plans.
- **E-Commerce Strategy Optimizer (`optional-skills/business/ecommerce-optimizer`):**
  - Store funnel diagnostics analyzing conversion rates, add-to-cart velocity, checkout abandonment, and inventory turnover.
  - Automated dynamic pricing strategies, threshold free-shipping models, and conversion rate optimization (CRO) playbooks.

---

### 4. ⛓️ Blockchain & Web3 Intelligence
- **Crypto Funding Deep-Dive (`optional-skills/blockchain/funding-dive`):**
  - Venture capital tracking, token vesting schedule modeling (TGE %, cliff months, linear release duration), investor concentration index, and sector inflow aggregation.
- **Granular Coin Deep-Dive (`optional-skills/blockchain/coin-deep-dive`):**
  - 5-dimension weighted rubric audit (Tokenomics, Utility, On-Chain Metrics, Team & Transparency, Architecture & Scalability).
  - Real-time CoinGecko market telemetry and circulating-float dilution analysis.
- **Airdrop Hunter (`optional-skills/blockchain/airdrop-hunter`):**
  - Multi-chain EVM RPC interaction scanner utilizing `eth_getLogs` for ERC-20 `Transfer` signatures across Ethereum, Base, and Arbitrum.
  - Local protocol eligibility tracking and markdown claim checklists.

---

### 5. 🛠️ Platform & Windows Installer Hardening
- **Windows `Copy-ConfigTemplates` Fix:** Implemented `Copy-ConfigTemplates` in `scripts/install.ps1` to establish `$ArcenHome` (`%LOCALAPPDATA%\arcen`) directory trees, configuration templates (`config.yaml`), `.env`, and `SOUL.md` persona files.
- **Windows `Install-NodeDeps` Stage:** Implemented `Install-NodeDeps` in `scripts/install.ps1` to achieve 100% parity with POSIX install flows, enabling smooth installation of browser tools and `ui-tui` on Windows machines.
- **Cross-Process Stage Isolation:** Dynamic PATH and node binary resolution ensuring headless/GUI installer runners function seamlessly without race conditions.
- **Stage Protocol Regression Guards:** Added automated validation in `scripts/tests/test-install-ps1-stage-protocol.ps1` to guarantee all installer stage workers are strictly defined.
- **Dependency Synchronization:** Synchronized `uv.lock` with `pyproject.toml` version `1.2.1` for deterministic, zero-drift CI builds.

---

## 🧪 Quality Assurance & Test Verification

- **Automated Skill Tests:** **91 passed** out of 91 tests (100% pass rate).
- **Compilation Check:** Full repository bytecode compilation verified with 0 errors (`python3 -m compileall`).
- **Distribution Package Check:** Wheels and source tarballs verified with `twine check` (**PASSED**).

```text
tests/skills/test_airdrop_hunter_skill.py .......... PASSED [5/5]
tests/skills/test_b2b_lead_gen_skill.py ............ PASSED [7/7]
tests/skills/test_backtester_skill.py .............. PASSED [11/11]
tests/skills/test_chart_analyzer_skill.py .......... PASSED [7/7]
tests/skills/test_coin_deep_dive_skill.py .......... PASSED [6/6]
tests/skills/test_coingecko_skill.py ............... PASSED [14/14]
tests/skills/test_ecommerce_optimizer_skill.py ..... PASSED [6/6]
tests/skills/test_funding_dive_skill.py ............ PASSED [6/6]
tests/skills/test_growth_intelligence_skill.py ...... PASSED [7/7]
tests/skills/test_influencer_analyzer_skill.py ..... PASSED [7/7]
tests/skills/test_market_research_skill.py ......... PASSED [7/7]
tests/skills/test_marketing_hub_skill.py ........... PASSED [6/6]
tests/skills/test_xurl_article_ingestion_docs.py ... PASSED [2/2]

======================== 91 passed in 1.00s (100% Pass Rate) ========================
```

---

## 📦 Installation & Upgrades

### Via `pip` or `uv`
```bash
pip install --upgrade arcen-agent
# or
uv add arcen-agent
```

### Via One-Line Installers

**macOS / Linux:**
```bash
curl -fsSL https://arcen-cli.arcenpay.com/install.sh | bash
```

**Windows (PowerShell):**
```powershell
iex (irm https://arcen-cli.arcenpay.com/install.ps1)
```

---

## 📋 Release Artifacts

| Filename | Type | Size |
|---|---|---|
| `arcen_agent-1.2.1-py3-none-any.whl` | Wheel Package | ~10.6 MB |
| `arcen_agent-1.2.1.tar.gz` | Source Distribution | ~8.6 MB |
