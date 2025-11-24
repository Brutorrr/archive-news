import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Configuration de la page
st.set_page_config(page_title="Newsletter Injector", page_icon="💉")

st.title("💉 Injecteur de Newsletter")
st.markdown("Cet outil permet d'envoyer manuellement du HTML brut à votre archive.")

# Récupération des secrets (si configurés dans Streamlit)
default_user = st.secrets["GMAIL_USER"] if "GMAIL_USER" in st.secrets else ""
default_pass = st.secrets["GMAIL_PASSWORD"] if "GMAIL_PASSWORD" in st.secrets else ""

with st.form("email_form"):
    col1, col2 = st.columns(2)
    with col1:
        user_email = st.text_input("Votre Gmail (Expéditeur)", value=default_user)
        app_password = st.text_input("Mot de passe d'application", type="password", value=default_pass)
    
    with col2:
        dest_email = st.text_input("Envoyer à (Adresse Archive)", value=default_user) # Souvent le même
    
    subject = st.text_input("Sujet de la Newsletter")
    html_content = st.text_area("Collez le Code HTML (OuterHTML) ici", height=300)
    
    submitted = st.form_submit_button("🚀 Envoyer l'archive")

if submitted:
    if not user_email or not app_password or not subject or not html_content:
        st.error("Veuillez remplir tous les champs.")
    else:
        try:
            with st.spinner("Connexion au serveur SMTP..."):
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = user_email
                msg["To"] = dest_email
                
                # Corps HTML
                part = MIMEText(html_content, "html")
                msg.attach(part)
                
                # Envoi
                server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
                server.login(user_email, app_password)
                server.sendmail(user_email, dest_email, msg.as_string())
                server.quit()
                
            st.success(f"✅ Newsletter '{subject}' envoyée avec succès !")
            st.balloons()
            
        except Exception as e:
            st.error(f"Erreur lors de l'envoi : {e}")
