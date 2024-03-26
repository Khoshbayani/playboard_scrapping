from selenium import webdriver
from selenium.webdriver.common.by import By
import re
from time import sleep
from pypasser import reCaptchaV2
import json
import os
from pandas import DataFrame,read_csv,concat
from datetime import datetime
from pytz import timezone


iran_timezone = timezone('Asia/Tehran')



if not os.path.isfile("log.csv"):
    DataFrame(columns=["time","subscription",'playRate',"playRate_step","subscription_step","isSuccessfull",'collected_emails_number',"error"]).to_csv('log.csv',index=False)


def write_json(new_data, filename='data.json'):
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            f.write("[]")
    # File path of the existing JSON file
    file_path = "data.json"

    # Read the existing JSON file
    with open(file_path, "r") as json_file:
        existing_data = json.load(json_file)

    # Extend the existing list with the new data list
    existing_data.extend(new_data)

    # Write the updated list back to the JSON file
    with open(file_path, "w") as json_file:
        json.dump(existing_data, json_file, indent=4)  # indent for pretty formatting


options = webdriver.FirefoxOptions()
# options.set_preference("permissions.default.image", 2)


isGUI = input("Do you want to run scraper with GUI browser? y or n: ")
if isGUI == 'y':
    headless = False
else:
    headless = True

print("I hope you find it useful\nstarted...")

def run_browser():
    options.headless = headless
    driver = webdriver.Firefox(options=options)
    return driver




def rchap(driver,where):
    sleep(5)
    try:
        driver.find_element(By.CLASS_NAME, "capcha")
    except:
        return True
    else:
        try:
            is_checked = reCaptchaV2(driver,play=False, attempts=6)
        except :
            return False
        else:
            if is_checked:
                if where == 'first_page':
                    sleep(2.5)
                    driver.find_element(By.XPATH,"/html/body/div[1]/div/div/div[1]/div/div/div/div/div[4]/span").click()
                    sleep(2.5)
                elif where == 'in_progress':
                    sleep(5)
                    driver.find_element(By.XPATH,"/html/body/div[1]/div/div/div[1]/div/main/div/div/div[2]/div/div/div[4]").click()
                    sleep(5)
                return True
            else:
                return False



def log(s,p,s_step,p_step,is_successfull,collected_email_num,errorMassage=None):
    current_time_iran = str(datetime.now(iran_timezone).strftime('%Y-%m-%d %H:%M:%S'))
    log_df = read_csv("log.csv")
    log_df = concat([log_df, DataFrame({"time": current_time_iran, "subscription": s, 'playRate': p,"subscription_step":s_step,"playRate_step":p_step, "isSuccessfull": is_successfull,'collected_emails_number': collected_email_num, "error": errorMassage},index=[1000])], ignore_index=True)
    log_df.to_csv('log.csv',index=False)



def restart_browser(driver,waithing_time=1200):
    driver.quit()
    sleep(waithing_time)
    driver = run_browser()
    return driver


def utf(text):
    return (text.encode('UTF-8')).decode('UTF-8')


def emails_extractor(text):
    emails = re.findall(r"[A-Za-z0-9_%+-.]+"
                       r"@[A-Za-z0-9.-]+"

                       r"\.[A-Za-z]{2,5}", text)
    return emails

driver = run_browser()




#restore log
s_start = 1300
p_start = 1300
p_step= 60
s_step= 100

try:
   logged = read_csv("log.csv")
   s_start = int(logged['subscription'].iloc[-1])
   p_start = int(logged['playRate'].iloc[-1])
   s_step = int(logged['subscription_step'].iloc[-1])
   p_step = int(logged['subscription_step'].iloc[-1])

   s_start = s_start+s_step

except:
    pass
counter = 0
number_of_extracted_emails_all = 0


for p in range(p_start,2*10**7,p_step):
    for s in range(s_start,2*10**7,s_step):
        try:
            counter += 1
            driver.get(f"https://playboard.co/en/search?subscribers={s}%3A{s+s_step-1}&country=US&country=CA&country=GB&playRate={p}%3A{p+p_step-1}&sortTypeId=1")
            sleep(2)
            if not rchap(driver,'first_page'):
                is_completed= False
                break

            # is_timeout = False
            # t1 = time.time()
            num_try = 0
            while True:
                # t2 = time.time()
                # if (t2 - t1) >= time_out:
                #     is_timeout = True
                #     break
                chan_num = len(driver.find_elements(By.CLASS_NAME, "meta"))
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                try:
                    retry_btn = driver.find_element(By.XPATH,"/html/body/div/div/div/div[1]/div/main/div/div/div[2]/div/div/div[4]/span")
                    sleep(4)
                    retry_btn.click()
                    sleep(4)
                except:
                    pass
                try:
                    if not rchap(driver, 'in_progress'):
                        is_completed = False
                        break
                    else:
                        driver.find_element(By.CLASS_NAME, "loading")
                except:
                    try:
                        driver.find_element(By.CLASS_NAME,"message")
                    except:
                        ##############
                        is_completed = True
                        break
                        ##############
                    else:
                        if not rchap(driver, 'in_progress'):
                            is_completed = False
                            break

                now_chan_num = len(driver.find_elements(By.CLASS_NAME, "meta"))
                if now_chan_num == chan_num:
                    num_try += 1
                if (now_chan_num == chan_num) and (num_try >=5):
                    is_completed = False
                    break
            # if is_timeout:
            #     break

            try:
                number_of_extracted_emails_in_this_try = 0
                this_page_data_list = []
                channels_info = driver.find_elements(By.CLASS_NAME, "meta")
                for chan_inf in channels_info:
                    id = utf(
                        chan_inf.find_element(By.CLASS_NAME, "name").find_element(By.CSS_SELECTOR, "a").get_attribute(
                            "href").replace(
                            "https://playboard.co/en/channel/", ""))
                    name = utf(chan_inf.find_element(By.CLASS_NAME, "name").text)
                    subs = utf(chan_inf.find_element(By.CLASS_NAME, "simple-scores").find_element(By.CSS_SELECTOR,
                                                                                                  "li:nth-child(1)").text.replace(
                        " subscribers,", ""))
                    try:
                        tags = None
                        tags_txt_list = []
                        tags = chan_inf.find_elements(By.CLASS_NAME, "ttags__item")
                        for t in tags:
                            tags_txt_list.append(utf(t.text))
                        if tags_txt_list == []:
                            tags_txt_list = None
                        else:
                            tags_txt_list = str(tags_txt_list)
                    except:
                        tags_txt_list = None

                    try:
                        emails = None
                        desc = None
                        desc = utf(chan_inf.find_element(By.CLASS_NAME, "desc").text)
                        emails = emails_extractor(desc)
                        if emails == []:
                            emails = None
                    except:
                        pass
                    current_data = list()
                    current_data.append({"id":id,"name": name, "description": desc, "tags": tags_txt_list, "subscibers_count": subs,
                                        "email": emails})
                    this_page_data_list.append(current_data)
                    # count extracted emails:
                    if emails != None:
                        number_of_extracted_emails_in_this_try += len(emails)
                        number_of_extracted_emails_all += len(emails)

                write_json(this_page_data_list)
                print("====================================")
                # log-ing:
                # log(s, p, s_step, p_step, True, number_of_extracted_emails_in_this_try)
                print(f"this is {counter}th page")
                print("number of extracted emails in this try: ", number_of_extracted_emails_in_this_try)
                print("number of extracted emails until now: ", number_of_extracted_emails_all)
            except:
                pass
            # if is_completed == False:
            log(s,p,s_step,p_step,is_completed,number_of_extracted_emails_in_this_try,None)
            # print("<<<<<<<<<<<<time-out>>>>>>>>>>>>>")
            if is_completed == False:
                print("waiting for 20 min")
                driver = restart_browser(driver)

        except:
            log(s, p, s_step, p_step, False, None, None)
            print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
            print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
            print(f"s is {s} and p is {p} and s_step is {s_step} and p_step is {p_step}")
            print("code 325")
            print("!!!!!!!!!!program stopped!!!!!!!!")
            while True:
                sleep(100)



