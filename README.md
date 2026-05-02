# 🏮 Noren — Asakusa Local Experience Platform

> "浅草でそばを打って、食べて、飲む。AIが予約と決済を全部やる。スタッフが体験を届ける。"

## What is Noren?

**Noren** is a local experience platform powered by AI + XRPL payments. Based at a guesthouse in Higashi-Komagata, Asakusa — when the noren (暖簾) is up, inbound tourists can book authentic local experiences and pay instantly with XRP.

Built for **Clawathon Tokyo Edition 2026** using **OpenClaw + XRPL**.

---

## The Problem

Asakusa's 1F cafe bar had just opened — zero customers. 6,000 guests/year at the guesthouse above, but no one was coming down. The challenge: how do you turn foot traffic into actual bookings and revenue?

## The Solution

An AI guide that speaks 5 languages, books experiences, and processes payments — automatically.

- Tourist messages the Telegram bot in any language
- AI (OpenClaw) responds as "Toru," a real Google Local Guide Lv.7
- Tourist selects a service → **payment processes automatically on XRPL testnet**
- Blockchain confirmation is sent back instantly

---

## Demo

```bash
# 1. Open for business
node noren.mjs open

# 2. Tourist books soba making experience
node pay.mjs soba_make "Tourist from NYC"
# OUTPUT:
# PAYMENT_SUCCESS
# SERVICE: 🍜 そば打ち体験
# AMOUNT: 10 XRP
# TX: <hash>
# EXPLORER: https://testnet.xrpl.org/transactions/<hash>

# 3. Check last payment
cat last-payment.json
```

---

## Architecture

```
Tourist (Telegram) 
    → OpenClaw AI Agent (クロ / Noren mode)
        → node pay.mjs <service_id>    ← shell command
            → XRPL Testnet payment
                → last-payment.json
                    → OpenClaw reads → confirmation back to tourist
```

**Key files:**
| File | Purpose |
|---|---|
| `noren.mjs` | Toggle noren open/close |
| `pay.mjs` | Automatic XRPL payment by service ID |
| `payment-server.mjs` | HTTP API + real-time XRPL subscription listener |
| `noren-status.json` | Service menu & pricing |
| `wallets.json` | XRPL testnet wallets |
| `index.html` | Landing page (QR code target) |
| `~/.openclaw/workspace/NOREN.md` | AI agent personality & payment instructions |

---

## Services & Pricing

| | Service | Price |
|---|---|---|
| 🍜 | **Soba Making Experience** — make & eat your own soba at the cafe bar | 10 XRP |
| 🍜 | Standing Soba Tour — Toru's handpicked spots | 5 XRP |
| ♨️ | Sento (Bathhouse) Guide — with etiquette map | 3 XRP |
| 🧳 | Luggage Storage — drop bags, explore freely | 2 XRP |
| 🍺 | 1F Cafe Bar — drinks in a local atmosphere | 2 XRP |
| 🙏 | Tip — if the advice helped | 1 XRP+ |

---

## Why XRPL?

- **No credit card friction** for inbound tourists
- **Micropayments** work at the 2–10 XRP scale
- **On-chain proof** of booking (tourist can verify)
- **No middleman** — Toru gets paid directly

---

## Guide Profile

**Toru** — Google Local Guide Lv.7 (13,375 pts, ~3M photo views)
- Standing soba researcher
- Higashi-Komagata resident
- Runs guesthouse (6,000 guests/year)
- Speaks Japanese, some English
- Staff: English / Chinese / Korean / Vietnamese

---

## Tech Stack

- **OpenClaw** — AI agent framework (Telegram + Discord)
- **XRPL (xrpl.js)** — XRP Ledger testnet payments
- **Node.js** — ES Modules
- **Telegram Bot** — Tourist-facing chat interface

---

## Setup

```bash
cd ~/noren-asakusa-guide
npm install
node setup-wallet.mjs   # Create XRPL testnet wallets
node noren.mjs open     # Open for business
```

**Guide wallet:** `rwvWe88gznptuX416q2Yc55zDPci7WE8eW`

---

## Hackathon

Built at **Clawathon Tokyo Edition** — May 2, 2026
Powered by **OpenClaw × XRPL**

Location: Ochanomizu Sola City → Higashi-Komagata 1-chome, Asakusa
