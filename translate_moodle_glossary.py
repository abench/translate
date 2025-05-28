from dotenv import load_dotenv
# import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from openai import OpenAI
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# from reportlab.lib.units import mm

# Client initialization
load_dotenv()
client = OpenAI()

# === НАЛАШТУВАННЯ ===
input_file = "Архітектура компютерів та операційні системи(1).xml"
output_xml_file = "glossary_uk.xml"
output_pdf_file = "glossary_uk.pdf"

# === ПЕРЕКЛАД ТЕКСТУ ЧЕРЕЗ GPT ===
def translate(text, source="en", target="ua"):
    if not text.strip():
        return text
    prompt = f"Translate from {source} to {target}:\n{text}"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# === ПЕРЕКЛАД HTML ЗІ ЗБЕРЕЖЕННЯМ ТЕГІВ ===
def translate_html(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    for el in soup.find_all(string=True):
        if el.strip():
            el.replace_with(translate(el))
    return str(soup)

# === ЧИТАННЯ І ПЕРЕКЛАД XML ===
tree = ET.parse(input_file)
root = tree.getroot()

pdf_entries = []

for entry in root.findall(".//ENTRY"):
    concept_el = entry.find("CONCEPT")
    def_el = entry.find("DEFINITION")

    # Переклад терміна
    concept = concept_el.text if concept_el is not None else ""
    concept_uk = translate(concept)
    if concept_el is not None:
        concept_el.text = concept_uk

    # Переклад визначення з HTML
    definition_html = def_el.text if def_el is not None else ""
    definition_uk_html = translate_html(definition_html)
    if def_el is not None:
        def_el.text = definition_uk_html

    # Для PDF — текст без тегів
    # text_only = BeautifulSoup(definition_uk_html, 'html.parser').get_text(separator=" ", strip=True)
    # pdf_entries.append((concept_uk, text_only))

# === ЗБЕРЕЖЕННЯ ОНОВЛЕНОГО XML ===
tree.write(output_xml_file, encoding="utf-8", xml_declaration=True)

# # === СТВОРЕННЯ PDF ===
# pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))

# doc = SimpleDocTemplate(output_pdf_file, pagesize=A4,
#                         rightMargin=20, leftMargin=20,
#                         topMargin=20, bottomMargin=20)

# styles = getSampleStyleSheet()
# styles.add(ParagraphStyle(name='Term', fontName='DejaVu', fontSize=12, leading=14, spaceAfter=4, spaceBefore=6))
# styles.add(ParagraphStyle(name='Def', fontName='DejaVu', fontSize=11, leading=13))

# story = [Paragraph("Глосарій (українською)", styles['Title']), Spacer(1, 10 * mm)]

# for concept, definition in pdf_entries:
#     story.append(Paragraph(f"<b>{concept}</b>", styles['Term']))
#     story.append(Paragraph(definition, styles['Def']))
#     story.append(Spacer(1, 4 * mm))

# doc.build(story)

print("✅ Готово: перекладено, збережено як XML і PDF")