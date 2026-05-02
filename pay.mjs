// Noren - サービス決済スクリプト (OpenClaw から呼ばれる)
// Usage: node pay.mjs <service_id> [tourist_note]
// service_id: soba / sento / bar / luggage / tip
import xrpl from 'xrpl'
import fs from 'fs'

const TESTNET = "wss://s.altnet.rippletest.net:51233"

const wallets = JSON.parse(fs.readFileSync('./wallets.json', 'utf8'))
const statusData = JSON.parse(fs.readFileSync('./noren-status.json', 'utf8'))

const SERVICE_MAP = {}
for (const s of statusData.services) {
  SERVICE_MAP[s.id] = s
}
// エイリアス対応
SERVICE_MAP['luggage'] = { id: 'luggage', name: '荷物預かり', price_xrp: 2, emoji: '🧳' }
SERVICE_MAP['soba_make'] = { id: 'soba_make', name: 'そば打ち体験', price_xrp: 10, emoji: '🍜' }

const args = process.argv.slice(2)
const serviceId = args[0]
const touristNote = args[1] || ''

if (!serviceId) {
  console.log('Usage: node pay.mjs <service_id>')
  console.log('Services:', Object.keys(SERVICE_MAP).join(', '))
  process.exit(1)
}

const service = SERVICE_MAP[serviceId]
if (!service) {
  console.log(`❌ Unknown service: ${serviceId}`)
  console.log('Available:', Object.keys(SERVICE_MAP).join(', '))
  process.exit(1)
}

const guideAddress = wallets.guide.address
const touristWallet = xrpl.Wallet.fromSeed(wallets.tourist.seed)

const memo = touristNote
  ? `Noren: ${service.name} - ${touristNote}`
  : `Noren: ${service.name}`

const client = new xrpl.Client(TESTNET)
await client.connect()

const prepared = await client.autofill({
  TransactionType: "Payment",
  Account: touristWallet.address,
  DeliverMax: xrpl.xrpToDrops(service.price_xrp.toString()),
  Destination: guideAddress,
  Memos: [{
    Memo: {
      MemoData: Buffer.from(memo, 'utf8').toString('hex').toUpperCase()
    }
  }]
})

const signed = touristWallet.sign(prepared)
const result = await client.submitAndWait(signed.tx_blob)
await client.disconnect()

if (result.result.meta.TransactionResult === "tesSUCCESS") {
  const explorerUrl = `https://testnet.xrpl.org/transactions/${signed.hash}`

  // 確認ファイルに書き出し（payment-server も読める）
  const confirmation = {
    service: serviceId,
    service_name: service.name,
    emoji: service.emoji,
    amount_xrp: service.price_xrp,
    tx_hash: signed.hash,
    explorer: explorerUrl,
    paid_at: new Date().toISOString(),
    memo,
    confirmation_message: `✅ ${service.emoji} ${service.name} の決済完了！ ${service.price_xrp} XRP received. TX: ${signed.hash}`
  }
  fs.writeFileSync('./last-payment.json', JSON.stringify(confirmation, null, 2))

  // OpenClaw が読みやすい形式で出力
  console.log(`PAYMENT_SUCCESS`)
  console.log(`SERVICE: ${service.emoji} ${service.name}`)
  console.log(`AMOUNT: ${service.price_xrp} XRP`)
  console.log(`TX: ${signed.hash}`)
  console.log(`EXPLORER: ${explorerUrl}`)
  console.log(`---`)
  console.log(`✅ Payment confirmed! ${service.price_xrp} XRP received for "${service.name}".`)
  console.log(`🔍 ${explorerUrl}`)
} else {
  console.log(`PAYMENT_FAILED`)
  console.log(`ERROR: ${result.result.meta.TransactionResult}`)
  process.exit(1)
}
