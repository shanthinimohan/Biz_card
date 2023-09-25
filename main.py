# Installing EasyOCR Library

# pip install easyocr
# !pip install Ipython


# Importing Necessary Libraries

import PIL
import easyocr
import streamlit as st
import pandas as pd
import re
import mysql.connector
import os

# Streamlit Web page appearance
st.set_page_config(page_title="BizCardX: Extracting Business Card Data with OCR",
                   layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={
                       'About': """This OCR App is created by Shanthini, GUVI DataScience, Batch-DT6DT7."""})
st.markdown("<h1 style='text-align: center; color: green;'>BizCardX: Extracting Business Card Data with OCR</h1>",
            unsafe_allow_html=True)
st.markdown(
    'This project extracts the text data from the uploaded business card image using EasyOCR. The extracted data is then stored in MySQL database and CRUD operations are performed.')

# Initialising EasyOCR
reader = easyocr.Reader(['en'], gpu=False)

# Connecting MySQL Database
mydb = mysql.connector.connect(host='localhost', user='root', password='Pranavi2022', database='biz_card')
mycursor = mydb.cursor(buffered=True)

# Creating Table
mycursor.execute('''create table if not exists BizCard (ID integer primary key auto_increment,
                                                         Image longblob,
                                                         Company_Name text,
                                                         Name text,
                                                         Designation text,
                                                         Phone_Number varchar(50),
                                                         Email text,
                                                         Website text,
                                                         Address varchar(255),
                                                         PinCode varchar(60))''')


def read_text(file_path):
    '''This function reads the image file from the specified path, converts into greyscale image and extracts text'''
    img = PIL.Image.open(file_path)
    # Converts the color image to greyscale image
    imgGrey = img.convert('L')
    imgGrey.save('grey_image.png')
    text = reader.readtext('grey_image.png', detail=0, paragraph=False)
    return text


images = st.file_uploader(label='Upload your image', type=['png', 'jpg', 'jpeg'])
image_path = os.getcwd() + '\\' + 'images' + '\\' + images.name


# CONVERTING IMAGE TO BINARY TO UPLOAD TO SQL DATABASE
def img2binary(file):
    # Convert image data to binary format
    with open(file, 'rb') as file:
        BinaryData = file.read()
    return BinaryData


def text_analysis(text):
    '''This function processes the extracted data and saves them as a dictionary in the corresponding key names'''
    processed = {'Image': image_path,
                 'Company_Name': '',
                 'Name': '',
                 'Designation': '',
                 'Phone_Number': '',
                 'Email': '',
                 'Website': '',
                 'Address': '',
                 'PinCode': ''}
    address = ""
    phone = ""
    company_name = ""

    for i in range(len(text)):
        if i == 0:
            processed['Name'] = text[i].title()
            continue
        if i == 1:
            processed['Designation'] = text[i].title()
            continue
        if "-" in text[i]:
            phone = " , ".join([phone, text[i]])
            processed['Phone_Number'] = phone[2:]
            continue
        if "@" in text[i]:
            processed['Email'] = text[i].lower()
            continue
        if "WWW" in text[i] or "www" in text[i] or "TTT" in text[i] or ".com" in text[i]:
            if "@" not in text[i]:
                processed['Website'] = text[i].lower()
            continue
        if "-" not in text[i] and "@" not in text[i] and "www" not in text[i] and "WWW" not in text[i]:
            if any(char.isdigit() for char in text[i]) or "," in text[i] or ";" in text[i]:
                address = address + text[i]
                cor_address = address.replace('  ', ' ').replace(';', ',').replace(',,', ',')
                pincode_pattern = r'(\d{5,6})'
                pincode = re.findall(pincode_pattern, cor_address)
                corr_address = re.sub(pincode_pattern, '', cor_address)
                processed['Address'] = corr_address
                postal = ''.join(pincode)
                processed['PinCode'] = postal
                continue
            else:
                company_name = " ".join([company_name, text[i]])
                processed['Company_Name'] = company_name[0:].title()
                continue

    return processed


def streamlit_UI():
    '''This function mainly uses streamlit, EasyOCR, MySQL to extract text from uploaded images and save it in a MySQL database for further CRUD operations'''

    # Reading and Extracting

    # images=st.file_uploader(label='Upload your image',type=['png','jpg','jpeg'])

    st.success('Uploaded Image')
    st.image(images)
    if images is not None:
        data_dict = text_analysis(read_text(images))
        df = pd.DataFrame(data_dict, index=[0, ])
        st.success('Extracted text ...')
        st.write(df)
        if st.button('Save to SQL Database'):
            for i, row in df.iterrows():
                sql = '''insert into BizCard(Image,Company_Name,Name,Designation,Phone_Number,Email,Website,Address,PinCode)
                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                mycursor.execute(sql, tuple(row))
                mydb.commit()
            st.success('SQL Data updated successfully!')


streamlit_UI()

# Editing and Deleting data in MySQL

option = st.selectbox('Select a CRUD operation', ('Read', 'Update', 'Delete'))
# Reading data
if option == 'Read':
    st.subheader('Records List')
    mycursor.execute(
        'select Image,Company_Name,Name,Designation,Phone_Number,Email,Website,Address,PinCode from BizCard')
    df_read = pd.DataFrame(mycursor.fetchall(),
                           columns=['Image', 'Company_Name', 'Name', 'Designation', 'Phone_Number', 'Email', 'Website',
                                    'Address', 'PinCode'])
    st.write(df_read)

# Modifying Extracted Data
elif option == 'Update':
    mycursor.execute('select Name from BizCard')
    result = mycursor.fetchall()
    Bizcard = {}
    for row in result:
        Bizcard[row[0]] = row[0]
    selected_card = st.selectbox('Select the Card holder name to update', list(Bizcard.keys()))
    st.markdown('#### Update or Modify')
    mycursor.execute(
        'select Company_Name,Name,Designation,Phone_Number,Email,Website,Address,PinCode from BizCard where Name=%s',
        (selected_card,))
    result = mycursor.fetchone()

    # Editing details
    Company_Name = st.text_input('Company_Name', result[0])
    Name = st.text_input('Name', result[1])
    Designation = st.text_input('Designation', result[2])
    Phone_Number = st.text_input('Phone_Number', result[3])
    Email = st.text_input('Email', result[4])
    Website = st.text_input('Website', result[5])
    Address = st.text_input('Address', result[6])
    PinCode = st.text_input('PinCode', result[7])

    # Update the information for the selected business card in the database
    if st.button('Commit Changes'):
        mycursor.execute("""UPDATE BizCard SET Company_Name=%s,Name=%s,Designation=%s,Phone_Number=%s,Email=%s,Website=%s,Address=%s,PinCode=%s
                                WHERE Name=%s""", (
            Company_Name, Name, Designation, Phone_Number, Email, Website, Address, PinCode, selected_card))
        mydb.commit()
        st.success("Details updated successfully.")

# Delete Operation
elif option == 'Delete':
    mycursor.execute("SELECT Name FROM BizCard")
    result = mycursor.fetchall()
    Bizcard = {}
    for row in result:
        Bizcard[row[0]] = row[0]
    selected_card = st.selectbox("Select a card holder name to Delete", list(Bizcard.keys()))
    st.write(f"### You have selected :red[**{selected_card}'s**] card to delete")
    st.write("#### Proceed to delete this card?")
    if st.button("Yes"):
        mycursor.execute(f"DELETE FROM BizCard WHERE Name ='{selected_card}'")
        mydb.commit()
        st.success("Business card data deleted from MySQL database.")
