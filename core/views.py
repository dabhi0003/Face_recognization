from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import face_recognition
import cv2
import numpy as np
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from googleapiclient.http import MediaIoBaseDownload
import io


def encode_face(face_image):
    image = cv2.imdecode(np.frombuffer(face_image.read(), np.uint8), cv2.IMREAD_COLOR)
    encodings = face_recognition.face_encodings(image)
    return encodings if encodings else None


# Function to get Google Drive credentials
def get_google_credentials():
    creds = Credentials.from_authorized_user_info(
        info={
            "client_id": "1007298964448-6pm3fm4nlah8sudtdcdktnbh60va1hnu.apps.googleusercontent.com",
            "client_secret": "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",
            "refresh_token": "1//0g7YhVU24ZxG8CgYIARAAGBASNwF-L9IrQxKJY6nEsYq7WoYbmiRMCrLoeDnydh0ctKtteTemypukKvsiyOAoB1wri5_LLse1aNc",
        }
    )
    return creds


# Function to fetch known faces from Google Drive
def fetch_known_faces(service, folder_id):
    known_faces = {}
    query = f"'{folder_id}' in parents and mimeType contains 'image/'"
    results = service.files().list(q=query, fields="files(id, name, webViewLink,thumbnailLink)").execute()
    items = results.get("files", [])

    for item in items:
        file_id = item["id"]
        filename = item["name"]
        file_url = item['webViewLink']
        thumbnailLink = item.get("thumbnailLink")
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        file.seek(0)
        encoding = encode_face(file)
        if encoding:
            known_faces[filename] = {"encoding": encoding, "thumbnailLink": thumbnailLink,"file_url":file_url}

    return known_faces


# Function to compare face encodings
def compare_faces(encoding1, encodings2_list):
    encoding1_array = np.array(encoding1)
    encodings2_array = np.array(encodings2_list)
    distances = face_recognition.face_distance(encodings2_array, encoding1_array)
    return any(distances <= 0.6)


# Django View
@csrf_exempt
def train_and_match(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    uploaded_face = request.FILES["face"]
    print('uploaded_face: ', uploaded_face)
    uploaded_encoding = encode_face(uploaded_face)

    if not uploaded_encoding:
        return JsonResponse(
            {"matched_faces": []}
        )  

    creds = get_google_credentials()
    service = build("drive", "v3", credentials=creds)

    known_faces = fetch_known_faces(service, "147CZnT28KcexxmlN1mKS7nrtLHOqqdNL")

    matches = []
    for known_face, data in known_faces.items():
        if compare_faces(uploaded_encoding, data["encoding"]):
            matches.append({"name": known_face, "thumbnailLink": data["thumbnailLink"],"file_url":data["file_url"]})


    return JsonResponse({"matched_faces": matches})