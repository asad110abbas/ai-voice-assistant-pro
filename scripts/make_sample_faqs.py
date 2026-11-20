"""Generate data/sample_faqs.docx: a synthetic FAQ knowledge base for a fictional online electronics store.

The RAG module (src/brain/rag.py) expects each answer as a quoted paragraph that starts with
"Topic: <name>." Run:  python scripts/make_sample_faqs.py
"""
from pathlib import Path

from docx import Document

FAQS = [
    ("Delivery", "Orders inside major cities are delivered in 2 to 3 working days, and in 4 to 6 working days elsewhere. "
                 "You receive a tracking link by SMS as soon as your parcel is dispatched."),
    ("Delivery charges", "Delivery is free on orders above 5,000 rupees. Smaller orders have a flat delivery fee of 199 rupees."),
    ("Cash on delivery", "Cash on delivery is available on all orders up to 300,000 rupees. "
                         "Please keep the exact amount ready, as couriers may not carry change."),
    ("Payment methods", "We accept cash on delivery, debit and credit cards, bank transfer and popular mobile wallets."),
    ("Installments", "Installment plans of 3, 6 and 12 months are available on selected credit cards from partner banks. "
                     "The available plans are shown on the checkout page."),
    ("Warranty", "All products come with the official brand warranty. Mobile phones carry a 12 month warranty, "
                 "and accessories carry a 6 month warranty unless stated otherwise on the product page."),
    ("Returns", "You can return an unused product in its original packaging within 7 days of delivery. "
                "Open a return request from My Orders and a courier will collect it."),
    ("Refunds", "Refunds are processed within 5 to 7 working days after the returned item passes inspection. "
                "Card payments are refunded to the same card, and cash orders by bank transfer."),
    ("Damaged item", "If your item arrives damaged, please share photos of the box and product within 48 hours "
                     "and we will arrange a free replacement."),
    ("Order cancellation", "You can cancel an order free of charge any time before it is dispatched, from My Orders or by asking support."),
    ("Order tracking", "To track an order, share your order ID with the assistant or open My Orders on the website."),
    ("Product authenticity", "We only sell new, original, sealed products sourced from authorized distributors."),
    ("Price match", "If you find the same product cheaper at an authorized seller within 3 days of purchase, "
                    "contact support and we will refund the difference."),
    ("Support hours", "Human support agents are available every day from 9 AM to 9 PM. "
                      "The AI assistant is available around the clock."),
    ("Account", "You can reset your password from the login page using your registered phone number or email."),
]


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "data" / "sample_faqs.docx"
    out.parent.mkdir(exist_ok=True)
    doc = Document()
    for topic, answer in FAQS:
        doc.add_paragraph(f'"Topic: {topic}. {answer}"')
    doc.save(out)
    print(f"wrote {len(FAQS)} FAQs to {out}")


if __name__ == "__main__":
    main()
