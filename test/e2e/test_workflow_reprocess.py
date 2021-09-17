import pytest
import time
from webdriver_manager.chrome import ChromeDriverManager
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
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    ####### TESTING - remove headless to see browser actions
    
    browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    return browser

# Test the happy path through the app by loading and verifying data after a successful workflow run.  No
# CRUD interactions such as creating vocabularies are included here
def test_workflow_reprocess(browser, workflow_to_modify, testing_env_variables):

#### TESTING - workflow is already created
#def test_complete_app(browser, testing_env_variables):
#### TESTING - workflow is already created

    print(workflow_to_modify)

    browser.implicitly_wait(5)
    browser.get(testing_env_variables['APP_ENDPOINT'])

    ####### Login

    username_field = browser.find_element_by_xpath("/html/body/div[1]/div/div/div/div[2]/div[1]/div/input")
    username_field.send_keys(testing_env_variables['APP_USERNAME'])
    password_field = browser.find_element_by_xpath("/html/body/div[1]/div/div/div/div[2]/div[2]/input")
    password_field.send_keys(testing_env_variables['APP_PASSWORD'])
    browser.find_element_by_xpath("/html/body/div[1]/div/div/div/div[3]/span[1]/button").click()
    
    time.sleep(20)

    # Analyze view
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div/div/div/div[1]/div/div/table/tbody/tr[1]/td[6]/a[1]").click()
    # Speech recognition
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[1]/div/div/div[1]/ul/li[2]/a").click()
    time.sleep(5)
                                   
    ####### SUBTITLES COMPONENT
    # Navigate to subtitles and wait for them to load
    #browser.find_elements_by_link_text("Subtitles")[0].click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/ul/li[2]/a").click()
    wait = WebDriverWait(browser, 120)
    wait.until(EC.presence_of_element_located((By.ID, "caption0")))

    # Check a subtitle
    subtitle1 = browser.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[1]/div[2]/div/div/div/div/table/tbody/tr[1]/td[2]/div/div/div[1]/textarea")
    subtitle1_text = subtitle1.get_attribute("value")
    assert "Boulder" in subtitle1_text

    # Edit a subtitle
    subtitle1.send_keys("\ue003\ue003\ue003\ue003\ue003\ue003\ue003\ue003 00BOULDEREPLACEDBYSOURCELANGUAGEEDITS00")

    # Save edits
    time.sleep(1)
    # Save edits
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[2]/div/div/button[3]").click()
    time.sleep(5)
    # Confirm Save Edits
    #browser.find_elements_by_link_text("Confirm")[0].click()
    
    wait = WebDriverWait(browser, 120)
    wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div/div/footer/button[2]")))
    browser.find_element_by_xpath("/html/body/div[2]/div[1]/div/div/footer/button[2]").click()
    time.sleep(10)
    

    # Check that the workflow has started
    # Collection
    browser.find_element_by_xpath("/html/body/div/div/div[1]/nav/div/ul/li[2]/a").click()
    # Status should be "Started"
    time.sleep(5)
    workflow_status = browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div/div/div/div[1]/div/div/table/tbody/tr[1]/td[3]/a").get_attribute("textContent")
    assert workflow_status == "Started"

    iterations = 0

    while workflow_status != "Complete" and iterations < 20:
        print('Sleeping for 60 seconds before retrying')
        iterations = iterations + 1
        time.sleep(55)
        browser.refresh()
        time.sleep(5)
        workflow_status = browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div/div/div/div[1]/div/div/table/tbody/tr[1]/td[3]/a").get_attribute("textContent")
        assert workflow_status in ["Started", "Queued", "Complete"]
        print (workflow_status)
        print (iterations)

    # Check that editing is disabled
    # FIXME - ISSUE #131 UI editing and save edits of source language subtitles should be disabled when there is an active workflow on an asset


    # Reload the page and check for the edits
    # Analyze view
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div/div/div/div[1]/div/div/table/tbody/tr[1]/td[6]/a[1]").click()
    # Speech recognition
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[1]/div/div/div[1]/ul/li[2]/a").click()
    time.sleep(5)
    # Navigate to subtitles
    #browser.find_elements_by_link_text("Subtitles")[0].click()
    browser.find_element_by_xpath("/html/body/div/div/div[2]/div/div[1]/div[1]/div/div/div[2]/div[2]/div/div[1]/ul/li[2]/a").click()
    wait = WebDriverWait(browser, 120)
    wait.until(EC.presence_of_element_located((By.ID, "caption0")))

    # FIXME - ISSUE #132 Edits are not applied after workflow reprocess
    # subtitle1 = browser.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div[1]/div[2]/div/div/div/div/table/tbody/tr[1]/td[2]/div/div/div[1]/textarea")
    # subtitle1_text = subtitle1.get_attribute("value")
    # assert "00BOULDEREPLACEDBYSOURCELANGUAGEEDITS00" in subtitle1_text

    # Check for the edits in the Translation
    
    # Cancel 
    #browser.find_element_by_xpath('/html/body/div[2]/div[1]/div/div/footer/button[1]').click()

    time.sleep(5)

     ####### TRANSLATE COMPONENT

    # Sign out
    browser.find_element_by_xpath("/html/body/div/div/div[1]/nav/div/ul/li[4]/a/p").click()