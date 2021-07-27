import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By


@pytest.fixture
def browser():
    chrome_options = Options()
    
    ####### TESTING - remove headless to see browser actions
    chrome_options.add_argument("--headless")
    ####### TESTING - remove headless to see browser actions
    
    browser = webdriver.Chrome(chrome_options=chrome_options)
    return browser

# Test the happy path through the app by loading and verifying data after a successful workflow run.  No
# CRUD interactions such as creating vocabularies are included here
def test_complete_app(browser, workflow_with_customizations, testing_env_variables):

#### TESTING - workflow is already created
#def test_complete_app(browser, testing_env_variables):
#### TESTING - workflow is already created

    browser.implicitly_wait(5)
    browser.get(testing_env_variables['APP_ENDPOINT'])

    ####### Login

    username_field = browser.find_element_by_xpath("/html/body/div[1]/div/div/div/div[2]/div[1]/div/input")
    username_field.send_keys(testing_env_variables['APP_USERNAME'])
    password_field = browser.find_element_by_xpath("/html/body/div[1]/div/div/div/div[2]/div[2]/input")
    password_field.send_keys(testing_env_variables['APP_PASSWORD'])
    browser.find_element_by_xpath("/html/body/div[1]/div/div/div/div[3]/span[1]/button").click()
    
    time.sleep(10)

    ####### UPLOAD VIEW
    # This test visits all the input form elements that should be activated with the default workflow configuration
    # It does not run any workflows
    
    # Navigate to the Upload View
    
    #browser.find_element_by_link_text("Upload").click()
    browser.find_element_by_xpath("/html/body/div/div/div[1]/div[1]/nav/div/ul/li[1]/a").click()                            

    # Check the default boxes are set for the subtitles workflow

    # Expand the configure workflow menu
    browser.find_element_by_xpath("/html/body/div/div/div[2]/button[1]").click()
    time.sleep(2)
    # Configure transcribe
    transcribe_language_box = browser.find_element_by_xpath("/html/body/div/div/div[2]/div[2]/div/div[1]/div[2]/div[2]/fieldset/div/div/div[2]/select[1]")
    
    # # default language is en-US
    # assert transcribe_language_box.get_attribute("value") == "en-US"
    
    # transcribe_language_box.send_keys("ru-RU")
    
    # # now it should be ru-RU
    # assert transcribe_language_box.get_attribute("value") == "ru-RU"
    
    # Configure subtitles
    subtitles_box = browser.find_element_by_xpath("/html/body/div/div/div[2]/div[2]/div/div[1]/div[2]/div[2]/fieldset/div/div/div[4]/input")
    subtitles_box.send_keys("test.vtt")
    assert subtitles_box.get_attribute("value") == "test.vtt"

    # Configure translate language to en-ES
    
    translate_languages_box = browser.find_element_by_xpath("/html/body/div/div/div[2]/div[2]/div/div[1]/div[3]/div[2]/fieldset/div/div[3]/fieldset/div/div[2]/div[1]/p/input")
    assert translate_languages_box.get_attribute("textContent") == ""
    # Select spanish badge
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div[2]/div/div[1]/div[3]/div[2]/fieldset/div/div[3]/fieldset/div/div/div[2]/p/span[44]").click() 

    # Check that spanish badge is in the input box
    assert browser.find_element_by_xpath("/html/body/div/div/div[2]/div[2]/div/div[1]/div[3]/div[2]/fieldset/div/div[3]/fieldset/div/div/div[1]/span/span").get_attribute("textContent") == "Spanish"

    # click the Swedish badge
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div[2]/div/div[1]/div[3]/div[2]/fieldset/div/div[3]/fieldset/div/div/div[2]/p/span[45]").click()
    assert browser.find_element_by_xpath("/html/body/div/div/div[2]/div[2]/div/div[1]/div[3]/div[2]/fieldset/div/div[3]/fieldset/div/div/div[1]/span[2]/span").get_attribute("textContent") == "Swedish"
    
     ####### Collection View
     # Navigate to Collection view
    #browser.find_element_by_link_text("Collection").click()
    browser.find_element_by_xpath("/html/body/div/div/div[1]/nav/div/ul/li[2]/a").click()
    time.sleep(5)

    # Find the base test asset in the collection
    # FIXME - it would be better to find the workflow with the correct assetId, but I can't figure out how to do it with selenium.  
    # Instead, we ae taking the first workflow in the list and assume it is the one for the test

     ####### TRANSCRIPT COMPONENT
    # Navigate to the transcript
    #Analyze
    #browser.find_element_by_link_text("Analyze").click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div/div/div/div[1]/div/div/table/tbody/tr[1]/td[6]/a[1]").click()
    time.sleep(2)
    #Speech Recognition
    #browser.find_element_by_link_text("Speech Recognition").click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[1]/div/div/div[1]/ul/li[2]/a").click()
    time.sleep(2)
    #Transcript
    #browser.find_element_by_link_text("Transcript").click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/ul/li[1]/a").click()
    time.sleep(8)

    # Check the text for some keywords
    transcript_text = browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div").get_attribute("textContent")
    assert("farm to" in transcript_text)

    # Download text
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div/button").click()
    
    # FIXME - Unable to test the video player in Selenium Chrome Driver - the player doesn't load from this test environment even though it loads when running the app - test env issue
    # time.sleep(5)
    # # Check the video player
    # player = browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div/video")
    # # Pause
    # browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div/div[4]/div[12]/button").click()
    # # Play
    # browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div/div[4]/button[1]").click()
    # # Speed 1.5x
    # browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div/div[4]/div[9]/button").click()
    # # Toggle language
    # browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[2]/div[1]/div/div[1]/div/div[4]/div[12]/button").click()

    # Check the File Information
    duration = browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[2]/div[2]/div/div/div/div/div/div/div[1]/div[1]").get_attribute("textContent")
    # SHould look like: "Video duration:\n              00:09\n            "
    assert duration.split()[0] == "Video"
    assert len(duration.split()) == 3

    time.sleep(5)
    
    ####### SUBTITLES COMPONENT
    # Navigate to subtitles
    #browser.find_elements_by_link_text("Subtitles")[0].click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/ul/li[2]/a").click()
    wait = WebDriverWait(browser, 120)
    wait.until(EC.presence_of_element_located((By.ID, "caption0")))

    # Check a subtitle
    subtitle1 = browser.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[1]/div[2]/div/div/div/div/table/tbody/tr[1]/td[2]/div/div/div[1]/textarea")
    subtitle1_text = subtitle1.get_attribute("value")
    assert "Boulder" in subtitle1_text

    # Edit a subtitle
    #subtitle1.clear()
    #subtitle1.send_keys("EDITED: COME BACK TO PORTLAND")
    subtitle1.send_keys("\ue003\ue003\ue003\ue003\ue003\ue003 00STEEN REPLACED BY EDITS00")

    # Check the file info
    source_language = browser.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[2]/div[2]/div/div/div/div/div/div/div[2]/div[4]").get_attribute("textContent")
    # Should look like: "Source Language: English, US"
    assert "English" in source_language

    # Test download button
    browser.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[1]/div[2]/div/div/button[1]").click()
    
    # Test vocabularies
    # Save vocabulary button
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div/button[2]").click()
    # Check the table for the edits
    vocabylary_1_display_as = browser.find_element_by_xpath("/html/body/div[3]/div[1]/div/div/div/div[3]/table/tbody/tr/td[5]/div/div[1]/div/input").get_attribute("value")
    assert vocabylary_1_display_as == "00STEEN REPLACED BY EDITS00" 

    # Name vocabulary
    # Invalid name
    vocabulary_name_box = browser.find_element_by_xpath("/html/body/div[2]/div[1]/div/div/div/div[1]/div[2]/input")
    vocabulary_name_box.send_keys("automated_test_vocabulary")
    error_text = browser.find_element_by_xpath("/html/body/div[2]/div[1]/div/div/div/div[4]").get_attribute("textContent")
    assert "Invalid vocabulary name" in error_text
    vocabulary_name_box.clear()
    # valid name
    vocabulary_name_box.send_keys("automatedtestvocabulary")

    # Add a row to vocabulary
    time.sleep(1)
    browser.find_element_by_xpath("/html/body/div[2]/div[1]/div/div/div/div[3]/table/tbody/tr/td[5]/div/div[2]/span[2]/button").click()
    time.sleep(3)
    # Delete a row from vocabulary
    browser.find_element_by_xpath("/html/body/div[2]/div[1]/div/div/div/div[3]/table/tbody/tr[2]/td[5]/div/div[2]/span[1]/button").click()
    
    # Cancel 
    browser.find_element_by_xpath('/html/body/div[2]/div[1]/div/div/footer/button[1]').click()

    time.sleep(5)

     ####### TRANSLATE COMPONENT
     # Navigate to translation
    #browser.find_elements_by_link_text("Translation")[0].click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/ul/li[3]/a").click()
    wait = WebDriverWait(browser, 120)
    wait.until(EC.presence_of_element_located((By.ID, "caption0")))

    # Check the radio button menus at the top - the language shoulf be Spanish
    button_language = browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div/fieldset/div/div/div/label").get_attribute("textContent")
    assert button_language == "Spanish"

    # Check a subtitle
    subtitle1 = browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div/div[1]/div/table/tbody/tr[1]/td[2]/div/div/div[1]/textarea")
    subtitle1_text = subtitle1.get_attribute("value")
    assert "Boulder" in subtitle1_text
    assert "JEFF STEEN-replaced-by-terminology" in subtitle1_text

    # Edit a subtitle
    #subtitle1.clear()
    #subtitle1.send_keys("EDITED: COME BACK TO PORTLAND")
    subtitle1.send_keys("\ue003\ue003\ue003\ue003\ue003\ue003\ue003\ue003\ue003\ue003\ue003\ue003 00terminology REPLACED BY EDITS00")

    # Check the file info
    source_language = browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[2]/div[2]/div/div/div/div/div/div/div[2]/div[4]").get_attribute("textContent")
    # Should look like: "Source Language: English, US"
    assert "English" in source_language

    # Test download buttons
    # VTT
    #browser.find_elements_by_link_text("Download VTT").click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div/div[2]/ul/li[1]/a")
    #browser.find_elements_by_link_text("Download SRT").click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div/div[2]/ul/li[2]/a")
    #browser.find_elements_by_link_text("Download Audio").click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div/div[2]/ul/li[3]/a")
    
    # # Test terminologies
    # # Save terminology button
    # browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div/button[1]").click()
    # # Check the table for the edits
    # vocabylary_1_display_as = browser.find_element_by_xpath("/html/body/div[3]/div[1]/div/div/div/div[3]/table/tbody/tr/td[5]/div/div[1]/div/input").get_attribute("value")
    # assert vocabylary_1_display_as == "00STEEN REPLACED BY EDITS00" 

    # # Name terminology
    # # Invalid name
    # vocabulary_name_box = browser.find_element_by_xpath("/html/body/div[2]/div[1]/div/div/div/div[1]/div[2]/input")
    # vocabulary_name_box.send_keys("automated_test_vocabulary")
    # error_text = browser.find_element_by_xpath("/html/body/div[2]/div[1]/div/div/div/div[4]").get_attribute("textContent")
    # assert "Invalid vocabulary name" in error_text
    # vocabulary_name_box.clear()
    # # valid name
    # vocabulary_name_box.send_keys("automatedtestvocabulary")

    # # Add a row to terminology
    # time.sleep(1)
    # browser.find_element_by_xpath("/html/body/div[2]/div[1]/div/div/div/div[3]/table/tbody/tr/td[5]/div/div[2]/span[2]/button").click()
    # time.sleep(3)
    # # Delete a row from terminology
    # browser.find_element_by_xpath("/html/body/div[2]/div[1]/div/div/div/div[3]/table/tbody/tr[2]/td[5]/div/div[2]/span[1]/button").click()
    
    # # Cancel 
    # browser.find_element_by_xpath('/html/body/div[2]/div[1]/div/div/footer/button[1]').click()

    time.sleep(5)

    # Sign out
    browser.find_element_by_xpath("/html/body/div/div/div[1]/nav/div/ul/li[4]/a/p").click()