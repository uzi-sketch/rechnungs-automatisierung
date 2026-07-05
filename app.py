import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# ====================== KONFIGURATION ======================
SENDER_EMAIL = "deine-email@gmail.com"
SENDER_PASSWORD = "dein-app-passwort"
# ===========================================================

st.set_page_config(page_title="Rechnungs-Automatisierung Demo", layout="wide")

st.title("📄 Rechnungs- & Mahnungs-Automatisierung")
st.sidebar.title("Demo-Optionen")
st.sidebar.info("Dieses Tool zeigt, wie ich Automatisierungen für KMU baue.")

st.markdown("**Demo-Projekt** – Automatische Rechnungserstellung + E-Mail-Versand + Mahnungs-Simulation")

# ====================== DATEN LADEN ======================
@st.cache_data
def load_data():
    df = pd.read_csv("data/invoices.csv", sep=",", header=0)
    df.columns = [col.strip() for col in df.columns]
    return df

df = load_data()

# ====================== PDF GENERIEREN ======================
def create_invoice_pdf(row):
    pdf = FPDF()
    pdf.add_page()

    # === HEADER ===
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "ALVI AUTOMATISIERUNGEN", ln=True, align="C")
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 6, "Informatik-Dienstleistungen - Wien", ln=True, align="C")
    pdf.ln(6)

    # Blaue Trennlinie
    pdf.set_draw_color(0, 102, 204)
    pdf.set_line_width(0.8)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(8)

    # === RECHNUNGSKOPF ===
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "RECHNUNG", ln=True, align="C")
    pdf.ln(6)

    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, f"Rechnungsnummer: {row['invoice_number']}", ln=True)
    pdf.cell(0, 7, f"Datum: {row['issue_date']}", ln=True)
    pdf.cell(0, 7, f"Fällig bis: {row['issue_date']}", ln=True)
    pdf.ln(8)

    # === KUNDE ===
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Rechnungsempfänger:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 7, row['customer_name'], ln=True)
    pdf.cell(0, 7, row['customer_email'], ln=True)
    pdf.ln(10)

    # === RECHNUNGSPOSITIONEN ===
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(230, 240, 250)
    pdf.cell(100, 8, "Beschreibung", border=1, fill=True)
    pdf.cell(25, 8, "Menge", border=1, fill=True, align="C")
    pdf.cell(30, 8, "Einzelpreis", border=1, fill=True, align="R")
    pdf.cell(35, 8, "Gesamt", border=1, fill=True, align="R")
    pdf.ln()

    pdf.set_font("Helvetica", size=11)
    
    # Position 1
    pdf.cell(100, 8, "Automatisierung & individuelle Beratung", border=1)
    pdf.cell(25, 8, "1", border=1, align="C")
    pdf.cell(30, 8, f"EUR {row['amount'] * 0.85:.2f}", border=1, align="R")
    pdf.cell(35, 8, f"EUR {row['amount'] * 0.85:.2f}", border=1, align="R")
    pdf.ln()
    
    # Position 2
    pdf.cell(100, 8, "Einrichtung & Schulung", border=1)
    pdf.cell(25, 8, "1", border=1, align="C")
    pdf.cell(30, 8, f"EUR {row['amount'] * 0.15:.2f}", border=1, align="R")
    pdf.cell(35, 8, f"EUR {row['amount'] * 0.15:.2f}", border=1, align="R")
    pdf.ln()

    # Gesamtsumme
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(0, 102, 204)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(155, 10, "Gesamtbetrag (inkl. MwSt.)", border=1, fill=True, align="R")
    pdf.cell(35, 10, f"EUR {row['amount']:.2f}", border=1, fill=True, align="R")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(12)

    # === FOOTER ===
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(0, 6, 
        "Vielen Dank für Ihr Vertrauen!\n\n"
        "Bitte überweisen Sie den Betrag innerhalb von 14 Tagen.\n\n"
        "Bei Fragen stehen wir Ihnen gerne zur Verfügung.\n\n"
        "Alvi Automatisierungen - Wien")

    filename = f"generated/{row['invoice_number']}.pdf"
    os.makedirs("generated", exist_ok=True)
    pdf.output(filename)
    return filename
# ====================== E-MAIL FUNKTION ======================
def send_email_with_pdf(receiver_email, subject, body, pdf_path):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with open(pdf_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(pdf_path)}")
            msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Fehler beim E-Mail-Versand: {e}")
        return False

# ====================== HAUPT-UI ======================
st.subheader("Offene Rechnungen")
st.dataframe(df, width='stretch')

col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Alle Rechnungen als PDF generieren", type="primary", key="btn_generate_all"):
        os.makedirs("generated", exist_ok=True)
        generated_files = []
        
        for idx, row in df.iterrows():
            pdf_path = create_invoice_pdf(row)
            generated_files.append(pdf_path)
        
        st.success(f"{len(generated_files)} PDFs wurden erfolgreich erstellt!")
        st.balloons()

        st.write("### Deine generierten Rechnungen")

        # Schöne Anzeige in 2 Spalten
        cols = st.columns(2)
        for i, pdf_path in enumerate(generated_files):
            with cols[i % 2]:
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label=f"📄 {os.path.basename(pdf_path)}",
                        data=f,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        key=f"dl_{i}"
                    )

	# ====================== ZIP DOWNLOAD ======================
        import zipfile
        from io import BytesIO

        if generated_files:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for pdf_path in generated_files:
                    zip_file.write(pdf_path, os.path.basename(pdf_path))
            
            zip_buffer.seek(0)
            
            st.download_button(
                label="📦 Alle Rechnungen als ZIP herunterladen",
                data=zip_buffer,
                file_name="Rechnungen_Alvi_Automatisierungen.zip",
                mime="application/zip",
                key="zip_download"
            )
        # ============================================================
with col2:
    if st.button("📧 Rechnungen per E-Mail versenden (Demo)", key="btn_send_emails"):
        os.makedirs("generated", exist_ok=True)
        for idx, row in df.iterrows():
            pdf_path = create_invoice_pdf(row)
            subject = f"Rechnung {row['invoice_number']}"
            body = f"Hallo {row['customer_name']},\n\nanbei Ihre Rechnung {row['invoice_number']} über EUR {row['amount']}.\n\nVielen Dank!"
            
            if SENDER_PASSWORD == "dein-app-passwort":
                st.info(f"Demo-Modus: E-Mail an {row['customer_email']} würde jetzt versendet werden.")
            else:
                if send_email_with_pdf(row['customer_email'], subject, body, pdf_path):
                    st.success(f"E-Mail an {row['customer_name']} versendet!")

st.divider()

# ====================== MAHNUNGS-SIMULATION ======================
st.subheader("Mahnungs-Simulation (nach 14 Tagen)")

today = datetime.now().date()

def is_overdue(issue_date, due_days):
    due_date = datetime.strptime(issue_date, "%Y-%m-%d").date() + timedelta(days=due_days)
    return today > due_date

overdue_invoices = df[df.apply(lambda x: is_overdue(x['issue_date'], x['due_days']), axis=1)]

if len(overdue_invoices) > 0:
    st.warning(f"{len(overdue_invoices)} Rechnung(en) sind überfällig!")
    st.dataframe(overdue_invoices[['customer_name', 'invoice_number', 'amount', 'issue_date']], width='stretch')

    if st.button("🔔 Mahnungen simulieren", key="btn_simulate_dunning"):
        for idx, row in overdue_invoices.iterrows():
            st.write(f"→ Mahnung würde jetzt an **{row['customer_name']}** ({row['customer_email']}) gesendet werden.")
else:
    st.success("Keine überfälligen Rechnungen im Demo-Datensatz.")

st.caption("Hinweis: Das ist eine Demo. Für echte Kunden bitte eigene Daten + sichere Zugangsdaten verwenden.")