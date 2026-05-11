import anthropic
import base64
import json
import re
from datetime import datetime

client = anthropic.Anthropic()

EXTRACTION_PROMPT = """この画像またはPDFは請求書・見積書・発注書などの書類です。
以下のJSON形式で情報を抽出してください。JSON以外の文字は一切含めないでください。

{
  "client_name": "請求先の会社名または個人名（不明な場合は空文字）",
  "invoice_date": "請求日 (YYYY-MM-DD形式、不明な場合は今日の日付)",
  "invoice_number": "請求書番号（不明な場合は空文字）",
  "items": [
    {
      "description": "品目・摘要名",
      "quantity": 数量（数値、不明な場合は1）,
      "unit_price": 単価（税抜きの整数、不明な場合は0）
    }
  ],
  "notes": "備考（あれば記載、なければ空文字）"
}

注意事項:
- 金額は必ず税抜きの整数で記載する
- 消費税・税金の行はitemsに含めない
- 品目が複数ある場合は全て含める
- 数量や単価が別々に記載されていない場合は合計金額から推測する
- 消費税込みの金額が記載されている場合は1.1で割って税抜き金額を算出する
"""


def extract_invoice_data(file_content: bytes, content_type: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")

    if content_type == "application/pdf":
        encoded = base64.standard_b64encode(file_content).decode("utf-8")
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": encoded,
                            },
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )
    else:
        encoded = base64.standard_b64encode(file_content).decode("utf-8")
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": encoded,
                            },
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )

    response_text = message.content[0].text
    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
    else:
        data = json.loads(response_text)

    if not data.get("invoice_date"):
        data["invoice_date"] = today
    if not data.get("items"):
        data["items"] = []

    return data
