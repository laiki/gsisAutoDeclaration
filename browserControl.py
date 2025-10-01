# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 15:31:11 2025

@author: wgout
"""

#%%

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import pathlib

#%% constants

USERNAME = "179208487"
PASSWORD = "Gg@09071998"
AFM = "179208487"
EMAIL = "zoe@goutas.de"
DOWNLOAD_DIR = pathlib.Path('./downloads').absolute()

DOWNLOAD_DIR.mkdir(exist_ok=True, parents=True)

#%% config Chrome

# Chrome-Optionen konfigurieren
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR.as_posix(),  # Zielordner
    "download.prompt_for_download": False,       # Kein Dialog
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    
    # Verhindert automatisches Öffnen von PDFs nach dem Download
    "plugins.always_open_pdf_externally": True

    })

#%%

# Starte den Browser
driver = webdriver.Chrome(ptions=chrome_options)
driver.get("https://dilosi.services.gov.gr/templates/YPDIL/create")

#%% accept coocies


wait = WebDriverWait(driver, 15)

# Schritt 1: Cookies akzeptieren
try:
    cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ενημερώθηκα')]")))
    cookie_button.click()
    print("Cookies akzeptiert.")
except:
    print("Cookie-Button nicht gefunden oder bereits akzeptiert.")

#%% login starten
# Schritt 2: Verbindung/Login starten
try:
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Σύνδεση')]")))
    login_button.click()
    print("Login gestartet.")
except:
    print("Login-Button nicht gefunden.")

#%% Taxisnet wählen

# Schritt 3: Verbindung mit Taxisnt Zuangsdaten
try:
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ΓΓΠΣΨΔ')]")))
    login_button.click()
    print("Taxtisnet Authentifitzierung geählt.")
except:
    print("Taxtisnet Authentifitzierung nicht gefunden.")


#%% user / passwort 

# Schritt 4: Authentifitzierung

try:
    username_field = wait.until(EC.presence_of_element_located((By.ID, "j_username")))
    password_field = wait.until(EC.presence_of_element_located((By.ID, "j_password")))
    
    username_field.clear()
    username_field.send_keys(USERNAME)
    password_field.clear()
    password_field.send_keys(PASSWORD)

    print("user & password Felder gefunden.")

except:
    print('user & password Felder nicht gefunden')

# Schritt 5: Verindung herstellen

try:
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "btn-login-submit")))
    login_button.click()

    print("Login durchgeführt.")
except Exception as e:
    print("Fehler beim Login:", e)

#%% AFM Prüfung


# Schritt 5: Warte auf das Feld mit Α.Φ.Μ.
try:

    afm_element = wait.until(EC.presence_of_element_located((
        By.XPATH,
        "//div[@data-testid='user'][.//dt[span[text()='Α.Φ.Μ.']]]//dd"
    )))
    afm_value = afm_element.text.strip()
    print("Α.Φ.Μ. gefunden:", afm_value)

    if afm_value == AFM:
        # Button "Συνέχεια" klicken
        continue_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-testid='button' and contains(text(), 'Συνέχεια')]")
        ))
        continue_button.click()
        print("Συνέχεια wurde geklickt.")

    else:
        print("Α.Φ.Μ. stimmt nicht überein. Kein Klick.")
except Exception as e:
    print("Fehler beim Prüfen oder Klicken:", e)


#%% continue authentification

# Schritt 6: Bestätigen der Authentifitzierung
try:
    submit_button = wait.until(EC.element_to_be_clickable((By.ID, "btn-submit")))
    submit_button.click()
    print("Bestätigungsdialog abgeschlossen.")
except:
    print("Fehler im Bestätigungsdialog der Authentifitzierung")        

#%% enter email address


# Schritt 7: Finde das Eingabefeld über die ID und trage die E-Mail-Adresse ein
try:
    email_input = driver.find_element(By.ID, "solemn:email")
    email_input.clear()
    email_input.send_keys(EMAIL)

    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Συνέχεια']")))
    submit_button.click()

    print("email Adresse eingetragen")
except:
    print("email Adressfeld nicht gefunden")

#%% Erklärungstext eingeben

# Schritt 8: füge den Text der Erklärung ein

try:
    textarea = driver.find_element(By.NAME, "free_text")
    textarea.clear()
    textarea.send_keys("test\n1\n\n2\n3\n")
    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Συνέχεια']")))
    submit_button.click()
    print("Erklärungstext eingegeben")
except:
    print("Fehler bei der Eingabe des Textes der Erklärung")
    
#%% Adressaten definieren

# Schritt 9: gebe den Empfänger der Erklärung ein
try:
    receiver_area = wait.until(EC.presence_of_element_located((By.ID, "solemn:recipient")))
    receiver_area.clear()
    receiver_area.send_keys('Empfänger')
    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Συνέχεια']")))
    submit_button.click()
    print("Empfänger definiert")
except:
    print("Fehler bei der Eingabe des Empfängers der Erklärung")


#%% Ausgabe erbeten

# Schritt 9: erbitte die Ausgabe des Dokumentes

try:
    
    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Έκδοση')]")
    submit_button.click()
    print("Ausgabe angefordert")

except:
    print("Fehler bei der Aufforderung das Dokument auszugeben")


#%% SMS Code Anfordern

# Schritt 10: Fordere SMS Bestätigungscode an
try:
    radio_input = driver.find_element(By.XPATH, "//label[contains(., 'Με αποστολή SMS')]/input[@type='radio']")
    radio_input.click()
    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Συνέχεια']")))
    submit_button.click()
    print("SMS angefordert")
except:
    print("Fehler bei der Anforderung des SMS Codes")

#%% SMS code aus Benachrichtigungen lesen

#Schritt 11: parse den Code aus den Benachrichtigungen

#%% Code Eingabe

# Schritt 12: gebe den Code in das Feld ein und bestätige

try:
    code_input = driver.find_element(By.ID, "confirmation_code")
    code_input.clear()
    code_input.send_keys(str(961324))
    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Επιβεβαίωση']")))
    submit_button.click()
    print("Bestätigungscode übergeben")
except:
    print("Fehler im Bestätigungscode")

try:
    error_element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Λανθασμένος κωδικός επιβεβαίωσης')]")
            )
        )
    if not error_element is None:
        raise Exception("wrong SMS code used")
except TimeoutException:
    print("Timeout bei der Abfrage nach Fehlern")
    
#%% save document

# Schritt 13: Speichere das Dokument

try:
    download_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Αποθήκευση')]")
    download_button.click()
    print("Download abgeschlossen")
except:
    print("Fehler beim Download")

    

    




#%%

# Warte auf das Formularfeld und fülle es aus
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email"))).send_keys("wasilios@example.com")

# Klicke auf "Code anfordern"
driver.find_element(By.ID, "send_code").click()

# Warte auf den SMS-Code (aus deinem OCR-Skript)
from sms_code_extractor import wait_for_sms_code  # dein bestehendes Modul
code = wait_for_sms_code()

# Trage den Code ins Formular ein
driver.find_element(By.ID, "sms_code").send_keys(code)

# Formular absenden
driver.find_element(By.ID, "submit_button").click()