// Noren - XRPLウォレット作成スクリプト（初回のみ実行）
import xrpl from 'xrpl'
import fs from 'fs'

const TESTNET = "wss://s.altnet.rippletest.net:51233"

console.log("🏮 Noren - XRPLウォレットをセットアップ中...\n")

const client = new xrpl.Client(TESTNET)
await client.connect()

// ガイド（受け取り側）のウォレット作成
console.log("ガイドのウォレットを作成中...")
const { wallet: guideWallet } = await client.fundWallet()

// テスト用観光客のウォレット作成
console.log("テスト用観光客のウォレットを作成中...")
const { wallet: touristWallet } = await client.fundWallet()

const config = {
  guide: {
    address: guideWallet.address,
    seed: guideWallet.seed,
    label: "Noren Guide (受け取り)"
  },
  tourist: {
    address: touristWallet.address,
    seed: touristWallet.seed,
    label: "Test Tourist (送り手)"
  },
  network: "testnet",
  explorer: "https://testnet.xrpl.org"
}

fs.writeFileSync('./wallets.json', JSON.stringify(config, null, 2))

console.log("\n✅ ウォレット作成完了！\n")
console.log(`🏮 ガイドアドレス:  ${guideWallet.address}`)
console.log(`🌍 観光客アドレス: ${touristWallet.address}`)
console.log(`\n📁 wallets.json に保存しました`)
console.log(`🔍 確認: ${config.explorer}/accounts/${guideWallet.address}`)

await client.disconnect()
