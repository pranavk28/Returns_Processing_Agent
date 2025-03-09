import cv2
import mysql.connector
from datetime import date
import streamlit as st

import numpy as np
from PIL import Image
import json
import pyzbar.pyzbar as pyzbar

from groq import Groq
import os
from dotenv import load_dotenv
import base64
from io import BytesIO

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Initialize session state variables
if "screen" not in st.session_state:
    st.session_state.screen = "login"
if "return_valid" not in st.session_state:
    st.session_state.return_valid = None
if "defect_type" not in st.session_state:
    st.session_state.defect_type = None
if "defect_details" not in st.session_state:
    st.session_state.defect_details = ""
if "defect_present" not in st.session_state:
    st.session_state.defect_present = None
if "return_order" not in st.session_state:
    st.session_state.return_order = None
if "db_object" not in st.session_state:
    st.session_state.db_object = mysql.connector.connect(
      host="localhost",
      user="root",
      password="Priyamab$123",
      database="returns_management"
    )
if "env_vars" not in st.session_state:
    load_dotenv()
    st.session_state.env_vars = {'GROQ_API_KEY' : os.getenv('GROQ_API_KEY')}
if "llm_client" not in st.session_state:
    st.session_state.llm_client = Groq(
        api_key=st.session_state.env_vars['GROQ_API_KEY'],
    )

def set_screen(screen, params):
    if screen == "login":
        if params[0] and params[1]:
            st.session_state.screen = "scan_qr"
        else:
            st.warning("Please enter username and password.")
    elif screen == "scan_qr":
        if st.session_state.return_order:
            st.session_state.screen = "select_defect"
    elif screen == "select_defect":
        st.session_state.defect_type = params[0]
        if params[0] in ["Packaging", "Physical"]:
            st.session_state.screen = "upload_defect_image"
        else:
            # Working defects like appliance or item not working required video input and manually entered for now, skipping defect image upload screen
            st.session_state.screen = "verify_defect"
        print(st.session_state.screen)
    elif screen == "upload_defect_image":
        st.session_state.screen = "verify_defect"
    elif screen == "verify_defect":
        if st.session_state.defect_details == "":
            st.session_state.defect_details = params[0]
        st.session_state.screen = "final_screen"
        
def back_screen():
    if st.session_state.screen == "scan_qr":
        st.session_state.screen = "login"
    elif st.session_state.screen == "select_defect":
        st.session_state.screen = "scan_qr"
    elif st.session_state.screen == "upload_defect_image":
        st.session_state.screen = "select_defect"
    elif st.session_state.screen == "verify_defect":
        st.session_state.screen = "select_defect"
    elif st.session_state.screen == "final_screen":
        st.session_state.screen = "scan_qr"

# Screen: Employee Login (Any username and password for now)
if st.session_state.screen == "login":
    st.title("Return Processing Employee Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    st.button("Login", on_click = set_screen, args=["login",(username,password)])

# Screen: Scan QR Code (Upload Image)
elif st.session_state.screen == "scan_qr":
    st.title("Scan QR Code to Get Purchase Details")
    qr_image = st.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"])
    if qr_image:
        img = Image.open(qr_image)
        purchase_details = json.loads(pyzbar.decode(img)[0].data.decode('utf-8'))
        print(purchase_details)
        if purchase_details["purchase_id"]:
            st.success("Purchase details retrieved successfully!")
            # Verify wether purchase is valid for return
            cursor = st.session_state.db_object.cursor()
            query = f"SELECT * FROM purchases where purchase_id = {purchase_details['purchase_id']} and (curdate() - purchase_date) < 7;"
            cursor.execute(query)
            if len(cursor.fetchall())<1:
                st.error("Return is not valid")
            else:
                st.session_state.return_order = {
                    "customer_id": purchase_details["customer_id"],
                    "product_id": purchase_details["product_id"],
                    "return_date": date.today().strftime("%Y/%m/%d")
                }
            cursor.close()
        else:
            st.error("Could not read qr code. Please retry")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Process return", on_click = set_screen, args=["scan_qr",()])
    with col2:
        st.button("Back", on_click=back_screen)

# Screen: Select Defect Type
elif st.session_state.screen == "select_defect":
    st.title("Select Defect Type")
    defect_type = st.radio("Choose defect type:", ["Packaging", "Physical", "Working"])
    col1, col2 = st.columns(2)
    with col1:
        st.button("Next", on_click = set_screen, args=["select_defect",(defect_type,)])
    with col2:
        st.button("Back", on_click=back_screen)

# Screen: Upload Defect Image (for Packaging or Physical defect)
elif st.session_state.screen == "upload_defect_image":
    st.title("Upload Defect Image")
    defect_image = st.file_uploader("Upload image of the defect", type=["png", "jpg", "jpeg"])
    if defect_image:
        img = Image.open(defect_image)
        img_base64 = image_to_base64(img)
        if st.session_state.defect_type == "Physical":
            prompt = "Tell me if the item in this image has one of the following damage types or no damage: Cracked surface, paint or color worn off, broken item, damaged wires, burnt surface\n Give output in this format only and no other information: Damaged - [Yes/No], Damage type - [Damage type]"
        elif st.session_state.defect_type == "Packaging":
            prompt = "Tell me if the package in this image is in good condition or not\n Give output in this format only and no other information: Damaged - [Yes/No]"
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                    }
                ]
            }
        ]
    
        completion = st.session_state.llm_client.chat.completions.create(
            model="llama-3.2-11b-vision-preview", 
            messages=messages, 
            max_tokens=500,
        )
        response = completion.choices[0].message.content
        
        if 'yes' in response.lower():
            st.session_state.defect_present = True
            if st.session_state.defect_type == 'Physical':
                st.session_state.defect_details = response.split(',')[1].split('-')[1].strip().replace(".","")
            else:
                st.session_state.defect_details = 'Damaged packaging'
            st.success("Defect detected successfully!")
        elif 'no' in response.lower():
            st.error("Defect not detected. Continue to next screen for manual entry if incorrect detection.")
            #Allowing human action in the loop in case of model inaccuracy
            st.session_state.defect_present = False
        else:
            st.error("Sytem failed to get an output. Retry input or continue to next screen for manual entry.") 

    col1, col2 = st.columns(2)
    with col1:
        st.button("Verify Defect", on_click = set_screen, args=["upload_defect_image",()])
    with col2:
        st.button("Back", on_click=back_screen)

# Screen: Verify Defect
elif st.session_state.screen == "verify_defect":
    st.title("Verify Defect Details")
    if st.session_state.defect_type == "Packaging":
        defect_text = "Packaging damaged"
    elif st.session_state.defect_type == "Physical":
        defect_text = st.session_state.defect_details
    else:
        defect_text = ""

    if st.session_state.defect_type == "Working":
        st.write("Describe the working defect manually:")
        defect_input = st.text_area("Enter the verified defect details")
        
    else:
        defect_input = st.text_area("Defect details:", defect_text)

    col1, col2 = st.columns(2)
    with col1:
        st.button("Process Return", on_click = set_screen, args=["verify_defect",(defect_input,)])
    with col2:
        st.button("Back", on_click=back_screen)

# Screen: Final Confirmation
elif st.session_state.screen == "final_screen":
    if st.session_state.defect_present:
        status = 'Approved'
    else:
        #In case of inaccurate detection model response and manual correction return is marked pending for further inspection before approval
        status = 'Pending'
    cursor = st.session_state.db_object.cursor()
    query = f"INSERT INTO `returns_management`.`returns` (`customer_id`, `product_id`, `return_date`, `status`, `defect_type`, `defect_detail`) VALUES ({st.session_state.return_order['customer_id']},{st.session_state.return_order['product_id']},curdate(),'{status}','{st.session_state.defect_type}','{st.session_state.defect_details}');"
    print(query)
    cursor.execute(query)
    st.session_state.db_object.commit()
    cursor.close()
    st.title("Return Processed Successfully")
    st.success("The return has been successfully processed.")

    st.button("Go to Home", on_click = back_screen)
