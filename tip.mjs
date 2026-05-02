// Noren - チップ送金スクリプト
import xrpl from 'xrpl'
import fs from 'fs'

const TESTNET = "wss://s.altnet.rippletest.net:51233"

const args = process.argv.slice(2)
const amountXRP = args[0] || "1"
const memo = args[1] || "Noren tip - ありがとう!"

const wallets = JSON.parse(fs.readFileSync('./wallets.json', 'utf8'))

console.log(`\n🏮 Noren - チップを送ります`)
console.log(`💰 金額: ${amountXRP} XRP`)
console.log(`💬 メモ: ${memo}\n`)

const client = new xrpl.Client(TESTNET)
await client.connect()

const sender = xrpl.Wallet.fromSeed(wallets.tourist.seed)
const destination = wallets.guide.address

const prepared = await client.autofill({
  TransactionType: "Payment",
  Account: sender.address,
  DeliverMax: xrpl.xrpToDrops(amountXRP),
  Destination: destination,
  Memos: [{
    Memo: {
      MemoData: Buffer.from(memo, 'utf8').toString('hex').toUpperCase()
    }
  }]
})

const signed = sender.sign(prepared)

console.log("⏳ 送金中...")
const result = await client.submitAndWait(signed.tx_blob)

if (result.result.meta.TransactionResult === "tesSUCCESS") {
  console.log("✅ チップ送信成功！")
  console.log(`🔍 確認: https://testnet.xrpl.org/transactions/${signed.hash}`)
} else {
  console.log("❌ エラー:", result.result.meta.TransactionResult)
}

await client.disconnect()
