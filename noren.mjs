// Noren - のれんを上げる/下げるコマンド
import fs from 'fs'

const args = process.argv.slice(2)
const command = args[0] // 'open' or 'close'

const status = JSON.parse(fs.readFileSync('./noren-status.json', 'utf8'))

if (command === 'open') {
  status.isOpen = true
  status.openedAt = new Date().toISOString()
  fs.writeFileSync('./noren-status.json', JSON.stringify(status, null, 2))
  console.log("🏮 のれんを上げました！ Noren is UP!")
  console.log(`📍 ${status.guide.location}`)
  console.log(`\n今日のサービス:`)
  status.services.forEach(s => {
    console.log(`  ${s.emoji} ${s.name} - ${s.price_xrp} XRP`)
  })
} else if (command === 'close') {
  status.isOpen = false
  status.closedAt = new Date().toISOString()
  fs.writeFileSync('./noren-status.json', JSON.stringify(status, null, 2))
  console.log("🌙 のれんを下げました。今日はお疲れ様でした。")
} else {
  const state = status.isOpen ? "🏮 上がっています（OPEN）" : "🌙 下がっています（CLOSED）"
  console.log(`現在ののれん: ${state}`)
}
