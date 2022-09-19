from selenium import webdriver

def headless_chrome():
   options = webdriver.ChromeOptions()
   options.binary_location = "/opt/chrome/headless-chromium"
   options.add_argument("--headless")
   options.add_argument("--no-sandbox")
   options.add_argument("--single-process")
   options.add_argument("--disable-gpu")
   options.add_argument("--window-size=1280x1696")
   options.add_argument("--disable-application-cache")
   options.add_argument("--disable-infobars")
   options.add_argument("--hide-scrollbars")
   options.add_argument("--enable-logging")
   options.add_argument("--log-level=0")
   options.add_argument("--ignore-certificate-errors")
   options.add_argument("--homedir=/tmp")
   options.add_argument("--disable-dev-shm-usage")

   driver = webdriver.Chrome(
       executable_path="/opt/chrome/chromedriver",
       chrome_options=options
   )
   return driver

def lambda_handler(event, context):
   
   driver = headless_chrome()
   driver.get('https://www.neaminational.org.au/')
   body = f"Headless Chrome Initialized, Page title: {driver.title}"
   print(body)
   result = {
       'statusCode': 200,
       'body': driver.title
   }
   
   driver.quit()
   
   return result
