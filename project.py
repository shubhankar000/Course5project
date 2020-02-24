%%time

import zipfile
import json
from PIL import Image
import pytesseract
import cv2 as cv
import numpy as np
from PIL import ImageDraw
from PIL import ImageFont

font = ImageFont.truetype(r'readonly/fanwood-webfont.ttf', 20) 
final_image=Image.new('RGB', (400,1), (255,255,255)) #the final output image
face_cascade = cv.CascadeClassifier('readonly/haarcascade_frontalface_default.xml')

# Below is the internal nested data structure
# {'filename1': [PIL.image, [[bouning boxes of faces]], 'string of entire image text'], filename2: [...],...}

def generate_output(filenames):
    '''Takes a list of filenames (as processed by the get_filenames function) and finds all the faces on the given
    page. returns a dictionary formatted in a way ready for outputing
    dictionary format:
    {'filename1': [All thumbnails in file1], 'filename1': [All thumbnails in file2], ...}
    :param filenames: A list of filenames as returned by the get_filenames function
    :return images_for_sheet: A list of thumbnail sized PIL.Image objects, ready for contact sheeting
    '''
    images_for_sheet={}
    for file in filenames:
        images_for_sheet[file]=[]
        for box in database[file][1]:
            temp_img=database[file][0].crop(convert_to_boundary(box))               
            temp_img.thumbnail((80,80))
            images_for_sheet[file].append(temp_img)
    return images_for_sheet

def contactsheet(images):
    '''Create a contact sheet and 'append' it to the (bottom of) current version of final_image
    :param images: A list of PIL.Image objects, ready to be made into a contact sheet. Ideally thumbnail sized
    :return None: Function works by modifying the final_image variable
    '''
    x,y=0,0
    global final_image #to ensure the global variable gets reassigned, not a local variable created in the function
    contact_sheet=Image.new('RGB', (400,160))
    for img in images:
        # Lets paste the current image into the contact sheet
        contact_sheet.paste(img, (x, y) )
        # Now we update our X position. If it is going to be the width of the image, then we set it to 0
        # and update Y as well to point to the next "line" of the contact sheet.
        if x+80 == contact_sheet.width:
            x=0
            y=y+80
        else:
            x=x+80
    new_im=Image.new('RGB', (400, final_image.height+contact_sheet.height)) 
    new_im.paste(final_image, (0,0)) #paste the current version of final_image
    new_im.paste(contact_sheet, (0,final_image.height)) #paste the contact sheet just created
    final_image=new_im #reassigning the global variable final_image

    
def add_text(string):
    '''Adds a string to the bottom of current version of final_image
    :param string: The string to be added into the PIL.Image
    :return None: Modifies the global variable final_image
    '''
    global final_image #to ensure the global variable gets reassigned, not a local variable created in the function
    new_image=Image.new('RGB', (400, 40), (255,255,255))
    drawing=ImageDraw.Draw(new_image)
    drawing.text((1, 5), string, font=font, align='left', fill='black')
    new_im=Image.new('RGB', (400, final_image.height+40))
    new_im.paste(final_image, (0,0)) #paste current version of final_image
    new_im.paste(new_image, (0,final_image.height)) #paste the text image
    final_image=new_im #reassigning the global variable final_image
    
def convert_to_boundary(rec):
    '''Takes cv2 return bounding boxes of faces (top, left, w, h) and converts to 
    PIL standards (top, left, bottom, right)
    :param rec: A list or a tuple as returned by cv2
    :return tuple: A tuple suitable to pass into PIL.Image functions and methods
    '''
    return (rec[0], rec[1], rec[0]+rec[2], rec[1]+rec[3])
    
def get_faces(pil_img):
    '''Gets the faces from a given PIL img
    Returns a list of 4-list
    :param pil_img: A PIL.Image object to perform face recognition on
    :return list: A list of lists containing bounding boxes of type [top, left, w, h]
    '''
    #opencv only takes BGR formatted objects, so using the builtin cv.COLOR_RBG2BGR to convert to BGR then to gray
    img = cv.cvtColor(np.array(pil_img), cv.COLOR_RGB2BGR)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    var=face_cascade.detectMultiScale(img, 1.3) #1.3 worked out well enough, but has some false positives and false negetives
    #detectMultiScale return an empty tuple when no images are detected, but a list of lists when they are
    if len(var)==0:
        return np.array([]) #return an empty numpy array (not empty list because of the .tolist() method) instead of a tuple 
    else:
        return var #return the list of lists
    
def draw_faces(pil_img, faces):
    '''Takes in a PIL image to draw rectangles on with the rectangle data given from get_faces() as a 4-list
    Returns modified PIL image. This function is for testing purposes and will not be used in the getting 
    the final output.
    Call this function inside a for loop.
    :param pil_img: A PIL.Image object
    :param faces: A 4-list as returned by the get_faces function.
    :return pil_img: returns a modified PIL.Image with rectangles drawn on it'''
    drawing=ImageDraw.Draw(pil_img)
    for rec in faces:        
        drawing.rectangle((rec[0],rec[1],rec[0]+rec[2],rec[1]+rec[3]), outline="black")
    #display(pil_img)
    return pil_img

def get_filenames(user_input):
    '''Takes a string which is the user input and checks which pages contain the string
    :param user_input: String which is the search query
    :return file: String which is the filename of the file contain'''
    return [filename for filename in database if user_input in database[filename][2]]



def create_database(directory):
    '''Create an internal nested database (list of dictionaries) from a zip file, which can be used for processing.
    Database format is given below
    {'filename1': [PIL.image, [[bouning boxes of faces]], 'string of entire image text'], filename2: [...],...}
    :param directory: A string pointing to the zip file
    :return database: A dictionary with filename as key and [image, bounding-boxes,string of image text] as value
    '''
    images = zipfile.ZipFile(directory)    
    newspapers = images.infolist()
    database={}
    for i in range(len(newspapers)):
        #append a new dictionary that will contain the filename as key and a list of details about the file.
        #the first element of this list is always the image file, followed by <other things>
        #database.append({})
        #open the file in the zipfile then open it as a PIL.Image object and convert it to RGB
        pil_img=Image.open(images.open(newspapers[i])).convert('RGB')
        #create the key which is the filename and set the value to a list whose only object rn is the PIL image corresponding to the filename
        database[images.namelist()[i]] = [pil_img, get_faces(pil_img).tolist(), pytesseract.image_to_string(pil_img.convert('L'))]
    return database 

user_input=input('Enter a word to search: ')
database=create_database('readonly/images.zip') #change this directory
filenames=get_filenames(user_input)
thumbnails=generate_output(filenames)

#Contingency code for when user input is empty
if user_input!='':
    for file in filenames:
        add_text('Results found in file {}'.format(file))
        if len(thumbnails[file])>0:
            contactsheet(thumbnails[file])
        else:
            add_text('But there were no faces in that file!')
else:
    add_text('No results found in any files')
    
display(final_image)
