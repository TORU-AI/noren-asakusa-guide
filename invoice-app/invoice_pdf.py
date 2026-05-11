import math
import os
import tempfile
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
]

FONT = "Helvetica"
for _path in _FONT_CANDIDATES:
    if os.path.exists(_path):
        try:
            pdfmetrics.registerFont(TTFont("JaFont", _path))
            FONT = "JaFont"
        except Exception:
            pass
        break

COMPANY = {
    "name": "ネクストパートナー株式会社",
    "postal": "〒130-0005",
    "address": "東京都墨田区東駒形１丁目１８−８",
    "tel": "TEL：03-5637-7845",
    "reg": "登録番号：T2380001027928",
}

BANK = {
    "bank": "みずほ銀行　六本木支店",
    "type": "普通　4611447",
    "holder": "ネクストパートナー株式会社",
    "rep": "代表取締役　富永義規",
}

TAX_RATE = 0.10


def _fmt(n: float) -> str:
    return f"¥{int(round(n)):,}"


def _apply_markup(items: list, markup_type: str):
    if markup_type == "20":
        processed = [
            {
                "description": it["description"],
                "quantity": it.get("quantity", 1),
                "unit_price": it.get("unit_price", 0) * 1.2,
                "amount": it.get("unit_price", 0) * 1.2 * it.get("quantity", 1),
            }
            for it in items
        ]
        extra = []

    elif markup_type == "40":
        processed = [
            {
                "description": it["description"],
                "quantity": it.get("quantity", 1),
                "unit_price": it.get("unit_price", 0) * 1.4,
                "amount": it.get("unit_price", 0) * 1.4 * it.get("quantity", 1),
            }
            for it in items
        ]
        extra = []

    else:  # kanri — keep prices, add 現場管理費 20%
        processed = [
            {
                "description": it["description"],
                "quantity": it.get("quantity", 1),
                "unit_price": it.get("unit_price", 0),
                "amount": it.get("unit_price", 0) * it.get("quantity", 1),
            }
            for it in items
        ]
        base = sum(i["amount"] for i in processed)
        kanri = math.floor(base * 0.2)
        extra = [
            {
                "description": "現場管理費",
                "quantity": 1,
                "unit_price": kanri,
                "amount": kanri,
            }
        ]

    all_items = processed + extra
    subtotal = sum(i["amount"] for i in all_items)
    tax = math.floor(subtotal * TAX_RATE)
    total = subtotal + tax
    return all_items, subtotal, tax, total


def _style(name, **kwargs):
    defaults = {"fontName": FONT, "fontSize": 9, "leading": 14}
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)


def generate_invoice_pdf(invoice_data: dict, markup_type: str) -> str:
    items = invoice_data.get("items", [])
    client_name = invoice_data.get("client_name", "")
    invoice_date = invoice_data.get("invoice_date", datetime.now().strftime("%Y-%m-%d"))
    invoice_number = invoice_data.get("invoice_number", "")
    notes = invoice_data.get("notes", "")

    all_items, subtotal, tax, total = _apply_markup(items, markup_type)

    try:
        dt = datetime.strptime(invoice_date, "%Y-%m-%d")
        date_str = f"{dt.year}年{dt.month}月{dt.day}日"
    except Exception:
        date_str = invoice_date

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()

    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    w = A4[0] - 30 * mm  # usable width

    story = []

    # ── Title ──────────────────────────────────────────────────────────────
    story.append(
        Paragraph("請　求　書", _style("title", fontSize=26, alignment=TA_CENTER, leading=34, spaceAfter=4 * mm))
    )

    # ── Header: client (left) | company (right) ────────────────────────────
    company_block = (
        f"<b>{COMPANY['name']}</b><br/>"
        f"{COMPANY['postal']}　{COMPANY['address']}<br/>"
        f"{COMPANY['tel']}<br/>"
        f"{COMPANY['reg']}"
    )
    client_display = f"<b>{client_name}　御中</b>" if client_name else "　　　　　　　　　　御中"
    date_block = f"請求日：{date_str}"
    if invoice_number:
        date_block += f"<br/>請求番号：{invoice_number}"

    header = Table(
        [
            [
                Paragraph(client_display, _style("cli", fontSize=13, leading=20)),
                Paragraph(company_block, _style("co", fontSize=9, alignment=TA_RIGHT, leading=15)),
            ],
            [
                Paragraph(date_block, _style("dt", fontSize=9, leading=14)),
                "",
            ],
        ],
        colWidths=[w * 0.52, w * 0.48],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black))
    story.append(Spacer(1, 4 * mm))

    # ── Greeting ───────────────────────────────────────────────────────────
    story.append(Paragraph("下記の通り、ご請求申し上げます。", _style("gr")))
    story.append(Spacer(1, 3 * mm))

    # ── Total box ──────────────────────────────────────────────────────────
    total_tbl = Table(
        [
            [
                Paragraph("合計金額（税込）", _style("tl", fontSize=11, alignment=TA_CENTER, leading=16)),
                Paragraph(_fmt(total), _style("ta", fontSize=18, alignment=TA_CENTER, leading=26)),
            ]
        ],
        colWidths=[w * 0.35, w * 0.65],
    )
    total_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.5, colors.black),
                ("LINEAFTER", (0, 0), (0, 0), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(total_tbl)
    story.append(Spacer(1, 5 * mm))

    # ── Items table ────────────────────────────────────────────────────────
    col_w = [w * 0.45, w * 0.10, w * 0.22, w * 0.23]

    th = _style("th", fontSize=9, alignment=TA_CENTER, leading=13)
    td_l = _style("tdl", fontSize=9, alignment=TA_LEFT, leading=13)
    td_r = _style("tdr", fontSize=9, alignment=TA_RIGHT, leading=13)
    td_c = _style("tdc", fontSize=9, alignment=TA_CENTER, leading=13)

    rows = [
        [
            Paragraph("品目・摘要", th),
            Paragraph("数量", th),
            Paragraph("単価", th),
            Paragraph("金額", th),
        ]
    ]
    for it in all_items:
        rows.append(
            [
                Paragraph(it["description"], td_l),
                Paragraph(str(int(it["quantity"])), td_c),
                Paragraph(_fmt(it["unit_price"]), td_r),
                Paragraph(_fmt(it["amount"]), td_r),
            ]
        )

    # Pad to at least 5 data rows so the table doesn't look empty
    while len(rows) - 1 < 5:
        rows.append(["", "", "", ""])

    sub_row = len(rows)
    tax_row = sub_row + 1
    tot_row = sub_row + 2

    rows += [
        ["", "", Paragraph("小　計", td_r), Paragraph(_fmt(subtotal), td_r)],
        [
            "",
            "",
            Paragraph(f"消費税（{int(TAX_RATE * 100)}%）", td_r),
            Paragraph(_fmt(tax), td_r),
        ],
        [
            "",
            "",
            Paragraph("合　計", _style("totl", fontSize=10, alignment=TA_RIGHT, leading=14)),
            Paragraph(_fmt(total), _style("tota", fontSize=10, alignment=TA_RIGHT, leading=14)),
        ],
    ]

    item_tbl = Table(rows, colWidths=col_w)
    item_tbl.setStyle(
        TableStyle(
            [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.15, 0.15, 0.15)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                # Outer box and grid
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.Color(0.6, 0.6, 0.6)),
                # Padding
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                # Span first two cols on summary rows
                ("SPAN", (0, sub_row), (1, sub_row)),
                ("SPAN", (0, tax_row), (1, tax_row)),
                ("SPAN", (0, tot_row), (1, tot_row)),
                # Total row highlight
                ("BACKGROUND", (0, tot_row), (-1, tot_row), colors.Color(0.93, 0.93, 0.93)),
                # Alternating row shading for item rows
                *[
                    ("BACKGROUND", (0, i), (-1, i), colors.Color(0.97, 0.97, 0.97))
                    for i in range(2, sub_row, 2)
                ],
            ]
        )
    )
    story.append(item_tbl)
    story.append(Spacer(1, 6 * mm))

    # ── Bank info + Notes ──────────────────────────────────────────────────
    bank_style = _style("bank", fontSize=9, alignment=TA_LEFT, leading=15)
    bank_hdr = _style("bankh", fontSize=9, alignment=TA_LEFT, leading=14)

    notes_text = "振り込み手数料はご負担ください"
    if notes:
        notes_text += f"<br/>{notes}"

    bank_tbl = Table(
        [
            [
                Paragraph("【お振込先】", bank_hdr),
                Paragraph("【備考】", bank_hdr),
            ],
            [
                Paragraph(
                    f"{BANK['bank']}<br/>"
                    f"{BANK['type']}<br/>"
                    f"{BANK['holder']}<br/>"
                    f"{BANK['rep']}",
                    bank_style,
                ),
                Paragraph(notes_text, bank_style),
            ],
        ],
        colWidths=[w * 0.60, w * 0.40],
    )
    bank_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.Color(0.5, 0.5, 0.5)),
                ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.Color(0.5, 0.5, 0.5)),
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.88, 0.88, 0.88)),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(bank_tbl)

    doc.build(story)
    return tmp.name
