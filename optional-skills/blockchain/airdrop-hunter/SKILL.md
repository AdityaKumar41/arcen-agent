---
name: airdrop-hunter
description: "Scan wallets and track multi-chain airdrop eligibility."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [crypto, airdrop, wallet, oracle, eligibility, on-chain, claim, tracker]
    category: blockchain
    related_skills: [evm, coin-deep-dive]
    requires_toolsets: [terminal]
---

# Automated Airdrop Hunting & Qualification Tracker Skill

Scans an EVM wallet for on-chain interactions with airdrop-associated
protocols (Uniswap, Aave, Lido, bridges, etc.) via public RPC, tracks
multi-chain eligibility locally, and produces a claim-ready checklist.

Stdlib only. Read-only public RPC — no keys, no transaction signing.

---

## When to Use

- User wants to check a wallet's exposure to known airdrop protocols
- User wants to track eligibility + required actions per protocol over time
- User wants a claim checklist (marked when actions are done)
- User wants to add their own protocol/contract to the scan set

---

## Prerequisites

Python 3.8+ standard library only — no pip installs. Public EVM RPC (no key):

```bash
export ETH_RPC_URL=https://ethereum.publicnode.com
export BASE_RPC_URL=https://mainnet.base.org
export ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
```

Helper script path: `~/.arcen/skills/blockchain/airdrop-hunter/scripts/airdrop_hunter.py`

Store: JSON at `~/.arcen/skills/blockchain/airdrop-hunter/airdrops.json` (override `--store`).

---

## How to Run

```bash
SCRIPT=~/.arcen/skills/blockchain/airdrop-hunter/scripts/airdrop_hunter.py

python3 $SCRIPT scan 0xYourWallet --blocks 50000 --track
python3 $SCRIPT track "MyProtocol" --chain ethereum --contract 0x... --note "new drop"
python3 $SCRIPT status
python3 $SCRIPT report --out checklist.md
python3 $SCRIPT scan 0xYourWallet --json
```

---

## Procedure

1. **Scan** — `scan <wallet>` checks each tracked protocol contract for
   ERC-20 `Transfer` events to/from the wallet over the lookback window
   (default 50k blocks) on its chain. A match = interaction → likely
   eligible candidate.
2. **Track** — `--track` persists matches; `track` registers a custom
   protocol (name, chain, contract) so it joins future scans.
3. **Status** — `status` shows tracked eligibility + notes + action items.
4. **Report** — `report` prints a claim checklist with checkboxes for each
   eligible protocol.

---

## Built-in Protocol Seed (Ethereum/Base)

Uniswap V2/V3, Aave, Lido, 1inch, SushiSwap, Arbitrum bridge, Optimism bridge,
zkSync Era, EigenLayer, Base. Verify contracts on-chain before relying on them;
the list is a seed, not gospel.

---

## Pitfalls

- **Log-scan heuristics** — "matched" means *some* Transfer event touched the
  contract in the window; it does not prove eligibility under a specific
  snapshot or criteria. Airdrops often gate on usage depth (volume, staking,
  activity count), not a single transfer.
- **RPC speed** — public RPCs throttle heavy `eth_getLogs`. Keep `--blocks`
  moderate (50k) and raise it selectively; the script sleeps briefly between
  contracts.
- **Contract addresses change** — reconfirm the token/bridge address per
  chain; stale addresses silently produce false negatives.
- **Never claim with agent-held keys** — claiming requires the user's wallet
  and careful review of contract approvals. The skill only discovers and
  tracks; the user performs and signs the claim.
- **Not financial advice** — airdrop markets are speculative.

---

## Verification

```bash
# Should return the latest Ethereum block (connectivity check)
python3 - <<'PY'
import sys; sys.path.insert(0,'~/.arcen/skills/blockchain/airdrop-hunter/scripts')
import airdrop_hunter as a
print(a.block_number(a.RPC_ETH))
PY
# Mock-logic check is covered in the repo tests (tests/skills/test_airdrop_hunter_skill.py)
```