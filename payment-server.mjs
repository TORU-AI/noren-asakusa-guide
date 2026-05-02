// Noren Payment Server
// XRPLをサブスクライブして着金を自動検知 + HTTP APIで決済リクエスト管理
import http from 'http'
import xrpl from 'xrpl'
import fs from 'fs'

const PORT = 3847  // NOREのASCII合計
const TESTNET = "wss://s.altnet.rippletest.net:51233"

const wallets = JSON.parse(fs.readFileSync('./wallets.json', 'utf8'))
const statusData = JSON.parse(fs.readFileSync('./noren-status.json', 'utf8'))

const GUIDE_ADDRESS = wallets.guide.address

// サービス定義
const SERVICES = {
  soba: { name: '立ち食いそばツアー', price_xrp: 5, emoji: '🍜' },
  soba_make: { name: 'そば打ち体験', price_xrp: 10, emoji: '🍜' },
  sento: { name: '銭湯ガイド', price_xrp: 3, emoji: '♨️' },
  bar: { name: 'カフェバー（1F）', price_xrp: 2, emoji: '🍺' },
  luggage: { name: '荷物預かり', price_xrp: 2, emoji: '🧳' },
  tip: { name: 'チップ', price_xrp: 1, emoji: '🙏' },
}

// 決済リクエスト（メモリ内）
const requests = new Map()

function genId() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  return Array.from({ length: 6 }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

// XRPL接続 + サブスクリプション
const client = new xrpl.Client(TESTNET)

async function startXRPL() {
  await client.connect()
  console.log(`✅ XRPL connected`)
  console.log(`👁  Watching: ${GUIDE_ADDRESS}`)

  await client.request({ command: 'subscribe', accounts: [GUIDE_ADDRESS] })

  client.on('transaction', (event) => {
    const tx = event.transaction
    if (!tx || tx.TransactionType !== 'Payment') return
    if (tx.Destination !== GUIDE_ADDRESS) return

    const drops = tx.DeliverMax || tx.Amount
    const xrpAmount = parseFloat(xrpl.dropsToXrp(drops))
    const txHash = event.transaction.hash || event.tx_json?.hash || 'unknown'

    console.log(`\n💰 PAYMENT DETECTED`)
    console.log(`   From: ${tx.Account}`)
    console.log(`   Amount: ${xrpAmount} XRP`)
    console.log(`   TX: https://testnet.xrpl.org/transactions/${txHash}`)

    // 対応するリクエストを探す
    let matched = false
    for (const [id, req] of requests.entries()) {
      if (req.status === 'pending' && xrpAmount >= req.amount_xrp) {
        req.status = 'paid'
        req.paid_at = new Date().toISOString()
        req.tx_hash = txHash
        req.explorer = `https://testnet.xrpl.org/transactions/${txHash}`
        console.log(`   ✅ Matched request: ${id} (${req.service_name})`)

        // 確認ファイルに書き出し（OpenClawが読める）
        fs.writeFileSync('./last-payment.json', JSON.stringify({
          request_id: id,
          service: req.service,
          service_name: req.service_name,
          amount_xrp: xrpAmount,
          tx_hash: txHash,
          explorer: req.explorer,
          paid_at: req.paid_at,
          confirmation_message: `✅ ${req.emoji} ${req.service_name}のお支払いを確認しました！\n💰 ${xrpAmount} XRP received\n🔍 ${req.explorer}`
        }, null, 2))
        matched = true
        break
      }
    }

    if (!matched) {
      // リクエストなしでも直接送金された場合
      fs.writeFileSync('./last-payment.json', JSON.stringify({
        request_id: null,
        amount_xrp: xrpAmount,
        tx_hash: txHash,
        explorer: `https://testnet.xrpl.org/transactions/${txHash}`,
        paid_at: new Date().toISOString(),
        confirmation_message: `✅ ${xrpAmount} XRP received!\n🔍 https://testnet.xrpl.org/transactions/${txHash}`
      }, null, 2))
    }
  })
}

// HTTPサーバー
const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json')
  res.setHeader('Access-Control-Allow-Origin', '*')

  const url = new URL(req.url, `http://localhost:${PORT}`)

  // GET / - ステータス確認
  if (req.method === 'GET' && url.pathname === '/') {
    res.writeHead(200)
    res.end(JSON.stringify({
      status: 'running',
      noren: statusData.isOpen ? 'OPEN' : 'CLOSED',
      guide_address: GUIDE_ADDRESS,
      services: SERVICES,
      active_requests: requests.size
    }, null, 2))
    return
  }

  // POST /request - 決済リクエスト作成
  if (req.method === 'POST' && url.pathname === '/request') {
    let body = ''
    req.on('data', c => body += c)
    req.on('end', () => {
      try {
        const data = JSON.parse(body || '{}')
        const serviceId = data.service
        const service = SERVICES[serviceId]
        if (!service) {
          res.writeHead(400)
          res.end(JSON.stringify({ error: `Unknown service: ${serviceId}`, available: Object.keys(SERVICES) }))
          return
        }
        const id = genId()
        const request = {
          id,
          service: serviceId,
          service_name: service.name,
          emoji: service.emoji,
          amount_xrp: service.price_xrp,
          destination: GUIDE_ADDRESS,
          status: 'pending',
          created_at: new Date().toISOString()
        }
        requests.set(id, request)
        console.log(`📋 New request: ${id} - ${service.emoji} ${service.name} (${service.price_xrp} XRP)`)

        res.writeHead(200)
        res.end(JSON.stringify({
          ...request,
          instruction: `Send ${service.price_xrp} XRP to ${GUIDE_ADDRESS}`,
          bot_message: `${service.emoji} *${service.name}* | 💳 Send *${service.price_xrp} XRP* to: ${GUIDE_ADDRESS} | Request ID: ${id} | I'll confirm once payment is received!`
        }))
      } catch (e) {
        res.writeHead(400)
        res.end(JSON.stringify({ error: e.message }))
      }
    })
    return
  }

  // GET /status/:id - 決済ステータス確認
  if (req.method === 'GET' && url.pathname.startsWith('/status/')) {
    const id = url.pathname.replace('/status/', '')
    const request = requests.get(id)
    if (!request) {
      res.writeHead(404)
      res.end(JSON.stringify({ error: 'Request not found' }))
      return
    }
    res.writeHead(200)
    res.end(JSON.stringify(request))
    return
  }

  // GET /last - 最後の着金確認
  if (req.method === 'GET' && url.pathname === '/last') {
    if (fs.existsSync('./last-payment.json')) {
      res.writeHead(200)
      res.end(fs.readFileSync('./last-payment.json'))
    } else {
      res.writeHead(200)
      res.end(JSON.stringify({ message: 'No payments yet' }))
    }
    return
  }

  res.writeHead(404)
  res.end(JSON.stringify({ error: 'Not found' }))
})

await startXRPL()

server.listen(PORT, () => {
  console.log(`\n🏮 Noren Payment Server`)
  console.log(`📡 http://localhost:${PORT}`)
  console.log(`\nEndpoints:`)
  console.log(`  GET  /            - Status`)
  console.log(`  POST /request     - Create payment request`)
  console.log(`  GET  /status/:id  - Check request status`)
  console.log(`  GET  /last        - Last confirmed payment`)
  console.log(`\nReady! Watching for XRP payments... 🚀\n`)
})
