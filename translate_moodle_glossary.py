from dotenv import load_dotenv
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from openai import OpenAI
from time import sleep
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# from reportlab.lib.units import mm



# Read configuration

load_dotenv()
input_file = os.getenv("GLOSSARY_INPUT_XML_FILE")
output_xml_file = os.getenv("GLOSSARY_OUTPUT_XML_FILE")
output_pdf_file = os.getenv("GLOSSARY_OUTPUT_PDF_FILE")
delay_between_requests = 2
context = "All text are from the computer architecture or operating systems domain. " \
"Prefer termin translation as in wikipedia" 

translation_prompt = f"""You are a professional translator specializing in computer science, computer architecture, and operating systems.  
Translate the following term and its definition from English to Ukrainian.  
**For the term, use the translation most commonly used in the Ukrainian Wikipedia.**  
For the definition, translate accurately, preserving technical meaning and clarity.  
If the term is not present in Wikipedia, use the most widely accepted Ukrainian technical term.  
Return only the translation, without explanations.\n\n"""



# Client initialization

client = OpenAI()
print(client.models.list().to_dict()['data'])# Translate using OpenAI API
sleep(delay_between_requests)  # Give some time for the client to initialize

def translate(text, translation_type, source="en", target="ua"):
    term_translation_prompt = f"""You are a professional translator specializing in computer science, computer architecture, and operating systems.
                                    Translate the following term from English to Ukrainian.
                                    Use the translation most commonly used in the Ukrainian Wikipedia.  
                                    If the term is not present in Wikipedia, use the most widely accepted Ukrainian technical term.
                                    Return only the translation, without explanations.

                                    Term: {text}"""
    definition_translation_prompt = f"""You are a professional translator specializing in computer science, computer architecture, and operating systems.
                                        Translate the following definition from English to Ukrainian.
                                        Translate accurately, preserving technical meaning and clarity.
                                        Return only the translation, without explanations.
                                        
                                        Definition: {text}"""
    
    if not text.strip():
        return text
    #prompt = f"Translate from {source} to {target}\n Context {context}\n Text for translation:\n {text}"
    if translation_type == "term":
        prompt = term_translation_prompt
    elif translation_type == "definition":
        prompt = definition_translation_prompt
    else:
        raise ValueError("Invalid translation type. Use 'term' or 'definition'.")
    
    response = client.responses.create(
        model="gpt-4o-mini-2024-07-18",
        input=[{"role": "user", "content": prompt}]
    )
    sleep(delay_between_requests)
    return response.output_text.strip()

# Translate, storing HTML tegs

def translate_html(html_text,translation_type):
    soup = BeautifulSoup(html_text, 'html.parser')
    for el in soup.find_all(string=True):
        if el.strip():
            el.replace_with(translate(el,translation_type))
    return str(soup)

# Reading and translation


tree = ET.parse(input_file)
root = tree.getroot()

pdf_entries = []

for entry in root.findall(".//ENTRY"):
    concept_el = entry.find("CONCEPT")
    def_el = entry.find("DEFINITION")

    # Переклад терміна
    concept = concept_el.text if concept_el is not None else ""
    concept_uk = translate(concept, "term") 
    if concept_el is not None:
        concept_el.text = concept_uk

    print(f"Translated term: {concept} {concept_uk}")  
    


    # Переклад визначення з HTML
    definition_html = def_el.text if def_el is not None else ""
    definition_uk_html = translate_html(definition_html, "definition") 
    if def_el is not None:
        def_el.text = definition_uk_html
    print(f"Translated definition: \n {definition_html} \n {definition_uk_html}")

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

print("Translation complete.")