# -*- coding: utf-8 -*-
"""
This module automates the process of creating and downloading official declarations
from the Greek government's public services portal (gov.gr).

It uses Selenium to navigate the website, log in with user credentials, fill out the
declaration form, and handle the SMS verification process. The final declaration
is downloaded as a PDF file.

"""


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import pathlib
import argparse
import tempfile
import shutil
import requests
from datetime import datetime as dt

#%% defaults

GSIS_DEFAULTS = {
        'download_dir' : pathlib.Path('./downloads').absolute()
      , 'url'          : "https://dilosi.services.gov.gr/templates/YPDIL/create"
      , 'timeout'      : 60
      #, 'retries'      : 3
    }
 
#%% 


class gsisGrabber:
    """
    A class to automate the creation of official declarations on the gov.gr portal.

    This class manages the web scraping process using Selenium, from logging in to
    downloading the final PDF. It handles user authentication, form submission,
    and SMS code verification.

    """
    
    def __init__(  self, username, password, taxid, email, receiver, text, download_dir
                 , url, timeout
                 #, retries
                 , getCode=None, filename=None
                 ) :
        """
        Initializes the gsisGrabber instance.

        Args:
            username (str): The Taxisnet username for login.
            password (str): The Taxisnet password for login.
            taxid (str): The user's tax identification number for verification.
            email (str): The user's email address.
            receiver (str): The name of the recipient of the declaration.
            text (str): The main content of the declaration.
            download_dir (str): The directory where the final PDF will be saved.
            url (str): The URL of the declaration creation page.
            timeout (int): The timeout in seconds for web driver waits.
            getCode (function, optional): A function to retrieve the SMS code. Defaults to None.
            filename (str, optional): The desired filename for the downloaded PDF. Defaults to None.

        """
        self.username = username
        self.password = password
        self.taxID    = taxid
        self.email    = email
        self.receiver = receiver
        self.declarationText = text
        self.download_dir = pathlib.Path(download_dir)
        self.url      = url
        self.filename = filename
        self.timeout  = timeout
        #self.retries  = int(retries)
        
        debug_dir = pathlib.Path('./debug')
        #shutil.rmtree(debug_dir, ignore_errors=True)
        if not debug_dir.exists():
            debug_dir.mkdir(parents=True, exist_ok=False)

        
        self.chrome_options = Options()
        self.chrome_options.add_argument("--incognito") # private mode
        self.chrome_options.add_argument("--disable-popup-blocking")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.tmpdir = tempfile.TemporaryDirectory()
        pathlib.Path(self.tmpdir.name).mkdir(parents=True, exist_ok=True)
        self.chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.tmpdir.name,  # Zielordner
            "download.prompt_for_download": False,       # Kein Dialog
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,            
            # Verhindert automatisches Öffnen von PDFs nach dem Download
            "plugins.always_open_pdf_externally": True        
            })
        
        self.download_dir.mkdir(exist_ok=True, parents=True)

        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.get("https://dilosi.services.gov.gr/templates/YPDIL/create")
        self.wait = WebDriverWait(self.driver, self.timeout)
        self._acceptCoockies()
        
        self.getCode = getCode
        self.filepath = None
        self.fileurl  = None
        return
    
    def __del__(self):
        """Destructor to clean up resources."""
        self.cleanup()
    
    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context related to this object."""
        self.cleanup()
        
        
    def cleanup(self):
        """
        Cleans up the resources used by the gsisGrabber.

        This method quits the web driver and removes the temporary download directory.

        """
        if not self.driver is None:
            self.driver.quit()
        if not self.tmpdir is None:
            self.tmpdir.cleanup()
        return
        
    def _acceptCoockies(self):
        """
        Accepts the cookie consent banner on the website.

        This method waits for the cookie button to be clickable and then clicks it.
        It will pass silently if the button is not found.

        """
        try:
            cookie_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Ενημερώθηκα')]")))
            self._scroll_and_click(cookie_button)
        except:
            pass
        return
    
    def _login(self):
        """
        Handles the login process on the gov.gr portal.

        This method navigates through the Taxisnet authentication by entering the
        provided username and password.

        Raises:
            Exception: If any step of the login process fails.

        """
        try:
            login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Σύνδεση')]")))
            self._scroll_and_click(login_button)

        except Exception as e:
            raise Exception("Login button not found.") from e
         
        try:
            auth_selector = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ΓΓΠΣΨΔ')]")))
            self._scroll_and_click(auth_selector)
        except Exception as e: 
            raise Exception("Taxisnet authentification not found.") from e
            
        try:
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "j_username")))
            password_field =self. wait.until(EC.presence_of_element_located((By.ID, "j_password")))
            username_field.clear()
            username_field.send_keys(self.username)
            password_field.clear()
            password_field.send_keys(self.password)
            
            login_button = self.wait.until(EC.element_to_be_clickable((By.ID, "btn-login-submit")))
            self._scroll_and_click(login_button)


        except:
            raise Exception("login failed")
        
        self._authentificate()
        return
            
    def _authentificate(self) :
        """
        Authenticates the user after login.

        This method confirms the user's identity by verifying the Tax ID and
        proceeding to the main form.

        Raises:
            Exception: If the Tax ID does not match or if authentication fails.

        """
        try:    
            begin_label = self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Συνέχεια')]")))
            self._scroll_and_click(begin_label)

            begin_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Αποστολή']")))
            self._scroll_and_click(begin_button)


            afm_element = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@data-testid='user'][.//dt[span[text()='Α.Φ.Μ.']]]//dd")
            ))
            afm_value   = afm_element.text.strip()
    
            if afm_value != str(self.taxID):
                raise Exception(f"TaxID received {afm_value} differs from {self.taxID}")
                
            submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Συνέχεια']")))
            self._scroll_and_click(submit_button)

            

        except Exception as e:
            self.driver.save_screenshot( (self.debug_dir / f"{dt.now()}_screenshot_authentification.png").as_posix() )
            raise Exception("error in authentification. TaxIDs differ") from e
        return
    
    def _initForm(self):
        """
        Initializes the declaration form.

        This method enters the user's email address and proceeds to the next step.

        Raises:
            Exception: If the email field cannot be found or the form cannot be submitted.

        """
        
        try:
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "solemn:email")))
            email_input.clear()
            email_input.send_keys(self.email)
        except Exception as e:
            raise Exception("can't find email field") from e
        
        try:
            submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Συνέχεια']")))
            self._scroll_and_click(submit_button)

        except Exception as e:
            raise e

        return
    
    def _declare(self) :
        """
        Fills out and submits the declaration form.

        This method enters the declaration text, specifies the recipient, and handles
        the SMS verification process to finalize and issue the declaration.

        Raises:
            Exception: If any step of filling or submitting the form fails.

        """
                
        try:
            textarea = self.wait.until(EC.presence_of_element_located((By.XPATH, "//textarea[@name='free_text']")))
            self._scroll_to(textarea)
            textarea.clear()
            textarea.send_keys(self.declarationText)
        except Exception as e:
            self.driver.save_screenshot( (self.debug_dir / f"{dt.now()}_screenshot_free_text.png").as_posix() ) 
            raise Exception("failed on providing declaration text") from e

        try:
            submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Συνέχεια']")))
            self._scroll_and_click(submit_button)
        except Exception as e:
            self.driver.save_screenshot( (self.debug_dir / f"{dt.now()}_screenshot_declaration_text.png").as_posix() )

            raise Exception("failed on submit declaration text") from e
        
        try:
            receiver_area = self.wait.until(EC.presence_of_element_located((By.ID, "solemn:recipient")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", receiver_area)
            WebDriverWait(self.driver, 5).until(EC.visibility_of(receiver_area)) # Warten, bis das Element sichtbar ist

            receiver_area.clear()
            receiver_area.send_keys(self.receiver)
            
            submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Συνέχεια']")))
            self._scroll_and_click(submit_button)
        except Exception as e:
            self.driver.save_screenshot( (self.debug_dir / f"{dt.now()}_screenshot_receipient_definition.png").as_posix() )
            raise Exception("failed on defining the receipient") from e
            
        try:
            submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Έκδοση')]")))
            self._scroll_and_click(submit_button)
        except Exception as e:
            self.driver.save_screenshot( (self.debug_dir / f"{dt.now()}_screenshot_declaration_export.png").as_posix() )
            raise Exception("failed to request the declaration export") from e
            
        try:
            radio_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(., 'Με αποστολή SMS')]/input[@type='radio']")))
            #radio_input = self.driver.find_element(By.XPATH, "//label[contains(., 'Με αποστολή SMS')]/input[@type='radio']")
            self._scroll_and_click(radio_input)


            submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Συνέχεια']")))
            self._scroll_and_click(submit_button)

        except Exception as e:
            self.driver.save_screenshot( (self.debug_dir / f"{dt.now()}_screenshot_SMS_request.png").as_posix() )
            raise Exception("failed to requeest SMS code") from e
            

        local_retry = 3
        while(True): 
            try:
                print('going to read code')
                code = self._getSMSCode()
                print('read code:', code)
                if code is None:
                    continue
            except Exception as e:
                raise Exception("no SMS code received") from e
                
            try:
                print('going to send code')
                self._sendCode(code)
                print('code send:', code)
                break
            except Exception as e:
                #self.retries -= 1 
                local_retry -= 1
                if local_retry == 0:
                    raise Exception("unable too send the SMS code") from e
                    
            break            
        
        #if self.retries == 0:
        #    raise Exception("too many failing attempts to provide the right code")
        
        self._saveDocument()

        return
    
    def _sendCode(self, code):
        """
        Submits the SMS verification code.

        Args:
            code (str): The verification code received via SMS.

        Raises:
            Exception: If the code cannot be submitted or is incorrect.

        """
        try:
            code_input = self.driver.find_element(By.ID, "confirmation_code")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", code_input)
            WebDriverWait(self.driver, 5).until(EC.visibility_of(code_input)) # Warten, bis das Element sichtbar ist
            code_input.clear()
            code_input.send_keys(code)
            
            submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Επιβεβαίωση']")))
            self._scroll_and_click(submit_button)

        except Exception as e:
            self.driver.save_screenshot( (self.debug_dir / f"{dt.now()}_screenshot_confirmation_code_entry.png").as_posix() )
            raise Exception("failed sending confirmation code") from e
            
        
        try:
            error_element = WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Λανθασμένος κωδικός επιβεβαίωσης')]")
                ))
            if not error_element is None:
                raise Exception("wrong SMS code used")
        except TimeoutException:
            pass # timeout while querying for errors, timeout here is good :)
        except Exception as e:
            self.driver.save_screenshot( (self.debug_dir / f"{dt.now()}_screenshot_confirmation_code_submission.png").as_posix() )
            raise Exception("failed while providing confirmation code") from e
        return
    
    def _getSMSCode(self):
        """
        Retrieves the SMS verification code.

        If a `getCode` function was provided during initialization, it will be called.
        Otherwise, it will prompt for the code from the console.

        Returns:
            str: The SMS verification code.

        """
        code = None
        if self.getCode is None:
            code = input("enter code: ")
        else:
            code = self.getCode()
        return code
    
    def _saveDocument(self):
        """
        Downloads and saves the final declaration PDF.

        This method finds the download link, downloads the file, and saves it to the
        specified directory, handling potential filename conflicts.

        Raises:
            Exception: If the download fails or the file cannot be saved.

        """
        #download_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Αποθήκευση')]")))
        #self._scroll_and_click(download_button)
        link_element  = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "pdf-download")]')))
        self.fileurl = link_element.get_attribute("href")
        
        response = requests.get(self.fileurl, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            (pathlib.Path(self.tmpdir.name)/"declaration.pdf").write_bytes(response.content)
        else:
            raise Exception(f"failed downloading file from {self.fileurl}")

        downloaded = list( pathlib.Path(self.tmpdir.name).glob('*') )
        if len(downloaded) != 1:
            print('failed downloading file', downloaded)
            raise Exception(f"error in processing file download. check download folder {self.tmpdir.name}")
            
        base_dest = self.download_dir/self.filename if not self.filename is None else self.download_dir/downloaded[0]
        dest = base_dest
        idx = 1
        while dest.exists():
            dest = dest.with_stem(base_dest.stem + f' ({idx})')
            idx += 1
        shutil.move(downloaded[0], dest)   
        #downloaded[0].replace(dest)  # cannot  move accross drives :(
        self.filepath = dest         
        return
    
    
    def run(self):
        """
        Executes the full process of creating and downloading a declaration.

        This is the main entry point for the class, which orchestrates the login,
        form filling, and download processes.

        Returns:
            tuple: A tuple containing the file URL and the local file path of the
                   downloaded declaration.

        """

        try:
            self._login()
        except Exception as e:
            print('login failed')
            raise e
        
        try:
            self._initForm()
        except Exception as e:
            print('initialization of declaration failed')
            raise e
        
        try:
            self._declare()
        except Exception as e:
            print('declaration failed')
            raise e
            
        return self.fileurl, self.filepath                  

    def _scroll_to(self, element, timeout=5):
        """
        Scrolls the page to bring a specified element into view.

        Args:
            element (WebElement): The Selenium WebElement to scroll to.
            timeout (int, optional): The time to wait for the scroll to complete. Defaults to 5.

        """
        # Scrollen
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
    
        # Warten, bis das Element vollständig im Viewport ist
        WebDriverWait(self.driver, timeout).until(lambda d: d.execute_script("""
            const rect = arguments[0].getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight)
            );
        """, element))

        return
    
    def _scroll_and_click(self, element, timeout=5):
        """
        Scrolls to an element and securely clicks it.

        This method ensures an element is fully visible before attempting to click it,
        which helps prevent misclicks or errors.

        Args:
            element (WebElement): The Selenium WebElement to click.
            timeout (int, optional): The time to wait for the element to be visible. Defaults to 5.

        """
        self._scroll_to(element, timeout)
        # Klicken
        element.click()
        return
#%%

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
          prog='gsisDeclaration'
        , description="goes through the steps needed to create an official declaration"
        )
    parser.add_argument('-u', '--user', dest='user',  default=None, required=True)
    parser.add_argument('-p', '--password', dest='password', default=None, required=True)
    parser.add_argument('--taxid', dest='taxid',   default=None, type=int, required=True)
    parser.add_argument('--email', dest='email', default=None, required=True)
    parser.add_argument('--receiver', dest='receiver', default=None, required=True)
    parser.add_argument('--download-dir', dest='download_dir', default=GSIS_DEFAULTS['download_dir'], required=False)
    parser.add_argument('--text', dest='text', default=None, required=True)
    parser.add_argument('--url', dest='url', default=GSIS_DEFAULTS['url'], required=False)
    #parser.add_argument('--retries', dest='retries', default=GSIS_DEFAULTS['retries'], type=int, required=False)
    parser.add_argument('--timeout', dest='timeout', default=GSIS_DEFAULTS['timeout'], type=int, required=False)
    parser.add_argument('--filename', dest='filename', default=None, required=False)
    
        
    args = vars(parser.parse_args())

    try:
        with gsisGrabber(  username   = args['user']
                           , password   = args['password']
                           , taxid      = args['taxid']
                           , email      = args['email']
                           , receiver   = args['receiver']
                           , text       = args['text']
                           , download_dir = args['download_dir']
                           , url        = args['url']
                           #, retries    = args['retries']
                           , timeout    = args['timeout']
                           , getCode    = None
                           , filename   = args['filename']
                           ) as gsis:
            url, declaration = gsis.run()
            print(url, declaration)
            
    except Exception as e:
        print(e)
    #finally: 
    #    gsis.cleanup() # <-ist explicitl
    #
    


            
