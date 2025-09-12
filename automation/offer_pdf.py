from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def build_offer(path="/app/data_analytics/reports/offer_proplus.pdf"):
    ...

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=A4)
    story = []

    # Title
    story.append(Paragraph("🚀 Automated Finance Reports — Pro+++ Offer", styles["Title"]))
    story.append(Spacer(1, 18))

    # Intro
    story.append(Paragraph(
        "Պրոֆեսիոնալ ավտոմատ հաշվետվություններ (PNG + PDF + Email). "
        "Օգնում է տեսնել եկամուտ/պարտք/խնայողության շարժը մեկ էջում։",
        styles["Normal"]
    ))
    story.append(Spacer(1, 14))

    # Packages
    data = [
        ["Փաթեթ", "Նկարագրություն", "Գին"],
        ["Starter", "1× PDF + PNG հաշվետվություն, պարզ բացատրություն", "50,000֏"],
        ["Growth",  "Շաբաթական report (4×), auto email, history tracking", "100,000֏/ամիս"],
        ["Pro",     "Ամսական մոնիթորինգ, report + email + mini dashboard, CSV export", "150–200,000֏/ամիս"],
    ]
    table = Table(data, colWidths=[100, 300, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (2,1), (2,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))

    # Contacts (փոխարինի քո տվյալներով)
    story.append(Paragraph("📩 Կոնտակտ: your_email@example.com | 📱 +374 XX XXX XXX", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Պատրաստ ենք սկսել այսօր 🚀", styles["Normal"]))

    doc.build(story)
    print(f"✅ Offer PDF created: {path}")

if __name__ == "__main__":
    build_offer()
