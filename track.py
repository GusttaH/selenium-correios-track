from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.command import Command
from functools import reduce
import time
import re
import boto3



chrome_options = Options()
chrome_options.add_argument("--headless")        
chrome_options.add_argument("--log-level=3")
#configurando o user-agent
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135")
#desabilitando imagens
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

aws_access_key_id=''
aws_secret_access_key=''

def execute():
  driver = webdriver.Chrome(options=chrome_options)

  print("\n\n************************* Correio Track ******************************\n")
  product_code_track = input("Digite o código do Produto:")
  print("\n**********************************************************************\n\n")

  while(1):
    driver.get("https://www2.correios.com.br/sistemas/rastreamento/default.cfm")
    driver.find_element_by_id('objetos').send_keys(product_code_track)
    driver.find_element_by_id('btnPesq').click()
    time.sleep(1)

    product_status_result = []
    product_status_rows = driver.find_elements_by_class_name('listEvent')
    for product_status in product_status_rows:
      product_status_result.append({
        'date_status':  find_date(product_status.find_element_by_class_name('sroDtEvent').text),
        'status': product_status.find_element_by_class_name('sroLbEvent').text
      })
    
    # send_email(product_status_result)
    write_log(product_status_result, product_code_track)
    time.sleep(1200)
  

def send_email(status, product_code_track):
  status = format_status_to_html(status)
  client = boto3.client(
    'ses',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key  
  )

  try:
    client.send_email(
        Source='contato.gustta.h@hotmail.com',
        Destination={
            'ToAddresses': [
                'dev.gustta.h@gmail.com',
            ],
        },
        Message={
            'Subject': {
                'Data': 'ATUALIZAÇÃO DE STATUS DO PRODUTO {}'.format(product_code_track),
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': 'string',
                    'Charset': 'UTF-8'
                },
                'Html': {
                    'Data': """
                      <h1>Correio Track</h1>
                      <ul style="font-size: 16px">
                        {}
                      </ul>

                    """.format(status),
                    'Charset': 'UTF-8'
                }
            }
        },
    )
    print('\n\n---------------------------------------------------------------------')
    print('> Email succeeded!')
  except Exception as ex:
    print('Send Email error!', ex)


def find_date(text):
  date = re.findall('\d{2}\/\d{2}\/\d{4}', text)[0]
  time = re.findall('\d{2}:\d{2}', text)[0]
  return date + ' - ' + time 

def format_status_to_html(status):
  lis = ["""<li style="display: flex; margin-bottom: 10px; border-bottom: 1px dashed #cecece; color: #000 "> <b>{}</b> - {}</li>""".format(x["date_status"], x["status"]) for x in reversed(status)]
  return reduce(lambda x,y: x + y, lis)

def format_status(status):
  lis = ["""{} - {}\n""".format(x["date_status"], x["status"]) for x in reversed(status)]
  return reduce(lambda x,y: x + y, lis)


def write_log(product_status):
  print('---------------------------------------------------------------------')
  for status in reversed(product_status):
    print("""\n> [{}]: {}""".format(status['date_status'], status['status']))

  print('\n---------------------------------------------------------------------')

execute()