import requests
from requests.adapters import HTTPAdapter
from requests_ntlm import HttpNtlmAuth
from selectolax.parser import HTMLParser
import os
from dataclasses import dataclass, asdict

DOMAIN = "https://cms.guc.edu.eg"
course_url = "/apps/student/CourseViewStn.aspx?id=175&sid=59"

def login(username, password):
    url = "https://apps.guc.edu.eg/student_ext/Console.aspx"
    try:
        print("MY URL: " + url)
        resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
        print("STATUS: " + str(resp.status_code))
        if (resp.status_code == 200):
              return True
        else:
              return False
    except:
        return False


def update_course_url(username, password, selected_course):
    global course_url

    url = "https://cms.guc.edu.eg/apps/student/HomePageStn.aspx"
    resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))

    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return
    
    html = HTMLParser(resp.text)
    all_courses = html.css("table#ContentPlaceHolderright_ContentPlaceHoldercontent_GridViewcourses tr")[1:]

    for course in all_courses:
        course_name = course.css("td")[1].text()
        course_name = course_name[course_name.find("|)") + 3: course_name.find(" (")]
        if selected_course == course_name:
            course_url = "/apps/student/CourseViewStn.aspx?id=" + course.css("td")[4].text() + "&sid=" + course.css("td")[5].text()
            break
    
    
      

def get_courses(username, password):
    url = "https://cms.guc.edu.eg/apps/student/HomePageStn.aspx"
    resp = requests.get(url, auth=HttpNtlmAuth(username.strip()+"@student.guc.edu.eg", password))
    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return {'exam_sched': [], 'success' : False}
    
    html = HTMLParser(resp.text)
    final_courses=[]
    all_courses = html.css("table#ContentPlaceHolderright_ContentPlaceHoldercontent_GridViewcourses tr")[1:]

    for course in all_courses:
        course_name = course.css("td")[1].text()
        course_name = course_name[course_name.find("|)") + 3: course_name.find(" (")]
        final_courses.append(course_name)

    return final_courses


def get_types(username, password):
    global DOMAIN, course_url
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
    
    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return {'exam_sched': [], 'success' : False}
    
    html = HTMLParser(resp.text)
    all_cards = html.css(".card-body")
    course_name = html.css_first("#ContentPlaceHolderright_ContentPlaceHoldercontent_LabelCourseName").text()
    course_name = course_name[course_name.find("|)") + 3: course_name.find(" (")]
    all_types = []

    for card in all_cards:
            title = card.css_first("div").text().strip().split("\n")[0]
            title = title[title.find("(")+1 : title.find(")")]
            
            if title not in all_types:
                all_types.append(title)

    return {'types' : all_types, 'course_name' : course_name}
        

def download_content(username, password, types):
    global DOMAIN, course_url
    resp = requests.get(DOMAIN + course_url, auth=HttpNtlmAuth(username+"@student.guc.edu.eg", password))
    
    if resp.status_code != 200:
            print("An Error Occurred. Check Credentials And Try Again.")
            return {'exam_sched': [], 'success' : False}
    
    html = HTMLParser(resp.text)
    all_cards = html.css(".card-body")
    all_types = []
    for card in all_cards:
            title = card.css_first("div").text().strip().split("\n")[0]
            title = title[title.find("(")+1 : title.find(")")]
            
            if title not in all_types:
                all_types.append(title)
            if (title in types):
                course_name = html.css_first("#ContentPlaceHolderright_ContentPlaceHoldercontent_LabelCourseName").text()
                course_name = course_name[course_name.find("|)") + 3: course_name.find(" (")]
                lecture_title = card.css_first("div strong").text().split(" - ")[1]
                link = card.css_first("a").attributes.get('href')
                file_format = link.split(".")[1]
                print(DOMAIN + link)
                download_resp = requests.get(DOMAIN + link, auth=HttpNtlmAuth(username, password))
                try: 
                    os.mkdir(course_name) 
                except OSError as error: 
                    print(error)  
                with open(course_name + "/" + course_name + " - " + lecture_title + "." + file_format, "wb") as file:
                    file.write(download_resp.content)
    return all_types

# login("seif.alsaid", "2002frolicGamer")
# download_content("seif.alsaid", "2002frolicGamer", ["Lecture slides"])
# get_courses("seif.alsaid", "2002frolicGamer")
# update_course_url("seif.alsaid", "2002frolicGamer", "Computer System Architecture")
# print(DOMAIN + course_url)