from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from PIL import Image
import numpy as np
import pyrebase
from fer import FER
import matplotlib.pyplot as plt

firebaseConfig = {
    'apiKey': "AIzaSyAMJv3Ooto_AAr1shf9MkPVkHbl0yqlZrM",
    'authDomain': "pythonfirebase-186f1.firebaseapp.com",
    'databaseURL': "https://pythonfirebase-186f1-default-rtdb.firebaseio.com",
    'projectId': "pythonfirebase-186f1",
    'storageBucket': "pythonfirebase-186f1.appspot.com",
    'messagingSenderId': "342993434754",
    'appId': "1:342993434754:web:64edf826b0a7062104dc9b",
    'measurementId': "G-4Y31GEGXML"
}

firebase=pyrebase.initialize_app(firebaseConfig)
db=firebase.database()


def push_to_firebase(emb,name,contact,medical_history,prescription_taken,additional_info):
    patient_name=name
    na=emb.detach().numpy()                        #convert tensor to numoy array
    lst=na.tolist()                                #convert numpy array to list
    data =  {  'name': patient_name,               #insrt the data you want to upload
               'contact':contact,
               'embeding':lst ,
               'medical_history': medical_history,
               'prescription_taken':prescription_taken,
               'additional_info':additional_info
               }

    patients=db.child('patients').shallow().get()     # to get primarykeys of patient table
    key=int(max(patients.val()))
    pk=key+1
    db.child("patients").child(pk).set(data)          #push data into firebase
    return "successfully updated details"

def Algorithm(path,name,contact,medical_history,prescription_taken,additional_info):
    pp=path+"/image.jpg";
    mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection
    resnet = InceptionResnetV1(pretrained='vggface2').eval() # initializing resnet for face img to embeding conversion
    img = Image.open(pp)
    img_cropped = mtcnn(img)


    boxes, probs= mtcnn.detect(img)
    if boxes is None:
        boxes = []
    if (len(boxes)>1):
        return "Cant Upload as many faces detected"
    elif (len(boxes)==0):
        return "Cant Upload as no faces detected"
    else:
        img_embedding = resnet(img_cropped.unsqueeze(0))
        #resnet.classify = True
        #img_probs = resnet(img_cropped.unsqueeze(0))
        res=push_to_firebase(img_embedding,name,contact,medical_history,prescription_taken,additional_info)
        return "Uploaded"

def get_embeddigns_names_from_firebsae():
    embedding_list=[]  # get all embs from firebase
    name_list=[]       # get all names frmo firebase
    patients=db.child('patients').shallow().get()
    dict_keys=list(patients.val())    #pk of table
    for i in patients.val():
        name = db.child("patients").child(i).child('name').get().val()     #get name
        e = db.child("patients").child(i).child('embeding').get().val()    #get embedding
        np_arr=np.array(e)                                                  #convert list to numpy arrat
        emb=torch.tensor(np_arr)                                               # convert np array to tensor

        name_list.append(name)
        embedding_list.append(emb)
    return embedding_list,name_list,dict_keys



def find_patient(img_paht):

    mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection
    resnet = InceptionResnetV1(pretrained='vggface2').eval() # initializing resnet for face img to embeding conversion

    img = Image.open(img_paht)
    face, prob = mtcnn(img, return_prob=True) # returns cropped face and probability
    emb = resnet(face.unsqueeze(0)).detach() # detech is to make required gradient false

    embedding_list,name_list,dict_keys = get_embeddigns_names_from_firebsae()

    dist_list = [] # list of matched distances, minimum distance is used to identify the person
    for idx, emb_db in enumerate(embedding_list):
        dist = torch.dist(emb, emb_db.float()).item()
        dist_list.append(dist)

    idx_min = dist_list.index(min(dist_list))
    min_dist=min(dist_list)

    patient_name=name_list[idx_min]
    i=dict_keys[idx_min]
    if min_dist< 1.0:
        name=db.child("patients").child(i).child('name').get().val()
        contact=db.child("patients").child(i).child('contact').get().val()
        medical_hist = db.child("patients").child(i).child('medical_history').get().val()
        prescription_taken=db.child("patients").child(i).child('prescription_taken').get().val()
        additional_info=db.child("patients").child(i).child('additional_info').get().val()
        s1="NAME: "+name+"\n"+"EMERGENCY CONTACT: "+contact+"\n"+"MEDICAL HISTORY: "+medical_hist+"\n"+"CURRENT PRESCRIPTIONS: "+prescription_taken+"\nADDITIONAL INFO: "+"\n"+additional_info
        return s1
    else:
        patient_name="person unknown"
        contact='not available'
        medical_hist='not available'
        prescription_taken='not available'
        additional_info='not available'
        return "Person detail not found"

#to edit details of a patient
def edit_details_in_firebase(name,contact,medical_history,prescription_taken,additional_info,key):
    old_contact=db.child("patients").child(key).child('contact').get().val()
    old_medical_hist = db.child("patients").child(key).child('medical_history').get().val()
    old_prescription_taken=db.child("patients").child(key).child('prescription_taken').get().val()
    old_additional_info=db.child("patients").child(key).child('additional_info').get().val()
    emb=db.child("patients").child(key).child('embeding').get().val()

    if(contact==""):
        contact=old_contact
    if(medical_history==""):
        medical_history=old_medical_hist
    if(prescription_taken==""):
        prescription_taken=old_prescription_taken
    if(additional_info==""):
        additional_info=old_additional_info

    data =  {  'name': name,               #insrt the data you want to upload
               'embeding':emb,
               'contact':contact,
               'medical_history': medical_history,
               'prescription_taken':prescription_taken,
               'additional_info':additional_info
               }

    db.child("patients").child(key).set(data)          #push data into firebase
    return "successfully updated details"

#start to edit details of patient
def edit_details(name,contact,medical_history,prescription_taken,additional_info):
    name=name.lower()
    name_list=[]
    patients=db.child('patients').shallow().get()
    dict_keys=list(patients.val())    #pk of table
    for i in dict_keys:
        name_list.append((db.child("patients").child(i).child('name').get().val()).lower())     #get names of db
    if(name in name_list):
        id_of_patient=dict_keys[name_list.index(name)]
        return edit_details_in_firebase(name,contact,medical_history,prescription_taken,additional_info,id_of_patient)
    else:
        return "patient is not registered or check patient name you have given"

def depression(path):
    img = plt.imread(path)
    detector = FER()
    x=(detector.detect_emotions(img))
    y=(x[0]["emotions"])
    #print(x)
    #print(y)
    a=[]
    p=0
    n=0
    sequence=[]
    for i,j in y.items():
        if j>0.20:
            a.append(i)
    for i in a:
        if i=="angry":
            sequence.append("Negative")
        elif i=="disgust":
            sequence.append("Negative")
        elif i=="fear":
            sequence.append("Negative")
        elif i=="sad":
            sequence.append("Negative")
        elif i=="happy":
            sequence.append("Positive")
        elif i=="surprise":
            sequence.append("Positive")
        elif i=="neutral":
            sequence.append("Positive")
    #print(a)
    #print(sequence)
    for i in sequence:
        if(i=='Positive'):
            p+=1
        if(i=='Negative'):
            n+=1
    #print(p)
    #print(n)
    total=len(sequence)
    if(n!=0):
        dep_level=n/total*100
    elif(n==0):
        dep_level=0
    #print(dep_level)
    if(dep_level<=15):
        return "No depression"
    elif(16<dep_level<=40):
        return "low depression"
    elif(40<dep_level<=70):
        return "mildy depressed"
    else:
        return "highly depressed"