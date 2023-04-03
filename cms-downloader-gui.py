import customtkinter
import requests
from requests_ntlm import HttpNtlmAuth
from selectolax.parser import HTMLParser
from main import download_content, get_types, login, get_courses, update_course_url

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")

input_username = ""
input_password = ""
all_types = ["--"]
page_index = 0
all_checkboxes = []

root = customtkinter.CTk()
root.geometry("600x600")
root.title("GUC CMS Downloader")


def start_download():
    selected_types = get_selected()
    [username, password] = getCredentials()
    download_content(username, password, selected_types)


def getCredentials():
    with open("cms_downloader.config", "r") as file:
            return [file.readline().split("=")[1].strip(), file.readline().split("=")[1].strip()]


def next_page(selected_course):
    [username, password] = getCredentials()
    global page_index
    if page_index < len(pages) - 1:
        page_index += 1
        for page in pages:
            page.pack_forget()
        if page_index == 2:
            update_course_url(username, password, selected_course)
            render_checkboxes()
        pages[page_index].pack(pady=20, padx=60, fill="both", expand=True)
        

def prev_page():
    global page_index
    if page_index > 0:
        page_index -= 1
        for page in pages:
            page.pack_forget()
        pages[page_index].pack(pady=20, padx=60, fill="both", expand=True)


def update_courses(username, password):
    all_courses = get_courses(username, password)
    type_select.configure(values=all_courses)
    type_select.set(all_courses[0])
    next_button.pack(pady=12, padx=10)


def render_checkboxes():
    [username, password] = getCredentials()
    get_types_output = get_types(username, password)
    all_types = get_types_output.get('types')
    course_name = get_types_output.get('course_name')

    course_label.configure(text=course_name, font=('Outfit', 25))
    course_label.pack(pady=12, padx=10)

    download_button.pack_forget()
    back_button.pack_forget()

    for box in all_checkboxes:
        box.pack_forget()

    for type in all_types:
        checkboxes[type] = customtkinter.CTkCheckBox(download_frame, text=type)
        checkboxes[type].pack(pady=12, padx=10)
        all_checkboxes.append(checkboxes[type])
    
    download_button.pack(pady=12, padx=10)
    back_button.pack(pady=12, padx=10)


def get_selected():
    [username, password] = getCredentials()
    selected = []
    all_types = get_types(username, password).get('types')
    for type in all_types:
        if checkboxes[type].get() == 1:
            selected.append(type)
    return selected


def loginGUI(username, password):
    global input_username, input_password

    loginState = login(username=username, password=password)

    if (loginState):
        with open("cms_downloader.config", "w") as file:
            file.write("username="+username)
            file.write("\npassword="+password)
            file.close()
        update_courses(username, password)
        next_page(type_select.get())
    else:
        print("Error baby")
        error_label.pack(pady=12, padx=10)



# Login Page
login_frame = customtkinter.CTkFrame(master=root)
# login_frame.pack(pady=20, padx=60, fill="both", expand=True)

label = customtkinter.CTkLabel(master=login_frame, text="CMS Downloader")
label.pack(pady=12, padx=10)

error_label = customtkinter.CTkLabel(master=login_frame, text="Error. Please Check Credentials", fg_color='#f00')

username = customtkinter.CTkEntry(master=login_frame, placeholder_text="Username")
username.pack(pady=12, padx=10)

password = customtkinter.CTkEntry(master=login_frame, placeholder_text="Password", show="*")
password.pack(pady=12, padx=10)

login_button = customtkinter.CTkButton(master=login_frame, text="Login", command= lambda: loginGUI(username=username.get(), password=password.get()))
login_button.pack(pady=12, padx=10)


# Course Select Page
courses_frame = customtkinter.CTkFrame(master=root)

courses_label = customtkinter.CTkLabel(master=courses_frame, text="Choose a course")
courses_label.pack(pady=12, padx=10)

type_select = customtkinter.CTkOptionMenu(courses_frame, values=all_types)
type_select.pack(pady=12, padx=10)

next_button = customtkinter.CTkButton(master=courses_frame, text="Next", command= lambda: next_page(type_select.get()))


# Download Page
download_frame = customtkinter.CTkFrame(master=root)

course_label = customtkinter.CTkLabel(master=download_frame, text="")
# course_label.pack(pady=12, padx=10)

checkboxes = {}
checkboxes[""] = customtkinter.CTkCheckBox(download_frame, text=type)

download_button = customtkinter.CTkButton(master=download_frame, text="Download", command= start_download)
back_button = customtkinter.CTkButton(master=download_frame, text="Back", command= prev_page)
# download_button.pack(pady=12, padx=10)

config_username = getCredentials()[0]
config_password = getCredentials()[1]
if config_username != "" and config_password != "":
    update_courses(config_username, config_password)
    page_index = 1
    courses_frame.pack(pady=20, padx=60, fill="both", expand=True)
else:
    login_frame.pack(pady=20, padx=60, fill="both", expand=True)


pages = [login_frame, courses_frame, download_frame]
root.mainloop()
