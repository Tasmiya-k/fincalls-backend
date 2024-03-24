
import tempfile
from bson import ObjectId
from flask import Flask, make_response, request, jsonify, send_file
from flask_cors import CORS 
import requests
from pymongo import MongoClient
from api_secrets import API_KEY_ASSEMBLYAI
import sys
import time
from gridfs import GridFS
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from summary import extract_financial_sentences, generate_pdf
from timeline import plot_graph,separate_and_highlight_tenses
import PyPDF2
from flask import render_template, request
import spacy
from termcolor import colored
import matplotlib.pyplot as plt
import io
import base64


from flask_pymongo import PyMongo

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['FinCalls']
collection = db['fincalls']
fs = GridFS(db)

CORS(app) 

upload_endpoint = "https://api.assemblyai.com/v2/upload"
# Transcription endpoint
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
# endpoint ends
filename = ""
headers = {'authorization': API_KEY_ASSEMBLYAI}


def upload(audio_file_id):
    
    audio_file = fs.get(audio_file_id)

    # Get the file path associated with the audio file
    filename = audio_file.filename

    # Reading the audio file in chunks
    def read_file(file_object, chunk_size=5242880):
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            yield data

    # Upload the audio file to AssemblyAI
    upload_response = requests.post(upload_endpoint, headers=headers, data=read_file(audio_file))

    # Retrieve the audio URL from the upload response
    audio_url = upload_response.json()['upload_url']
    return audio_url

# -------------------------------------------------------------------------------

# Transcribe
def transcribe(audio_url):
    transcript_request = {"audio_url": audio_url, "speaker_labels": True}
    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
    # Using the following print statement, we get a much longer response which contains the audio_url, the id and a lot more. We will be using the id from that response for polling
    # print(response.json())
    transcript_id = transcript_response.json()['id']
    return transcript_id



@app.route('/')
def index():
    return 'Hello, this is the root path!'

from flask import request

@app.route('/upload_files', methods=['POST'])
def upload_files():
    if 'audioFile' in request.files:
        # If audio file is uploaded
        file = request.files['audioFile']
        if file:
            # Save the audio file to MongoDB using GridFS
            audio_file_id = fs.put(file, filename=file.filename)

            # Upload the audio file to AssemblyAI and get the transcript
            audio_url = upload(audio_file_id)
            data, error = get_transcription_result_url(audio_url)

            if data:
                # speaker_labels = data.get('speaker_labels', [])
                global utterances
                utterances = data.get('utterances', [])

                transcript_text = ""
                for utterance in utterances:
                    speaker = utterance['speaker']
                    text = utterance['text']
                    transcript_text += f"Speaker {speaker}: {text}\n"

                # Save transcript text to a file
                transcript_file_id = fs.put(transcript_text.encode('utf-8'), filename="transcript.txt")

                # Return the IDs of the saved audio file and transcript file
                return jsonify({'audio_file_id': str(audio_file_id), 'transcript_file_id': str(transcript_file_id)}), 200
            elif error:
                return jsonify({'error': str(error)}), 500

    elif 'pdfFile' in request.files:
        # If PDF file is uploaded
        file = request.files['pdfFile']
        if file:
            # Save the PDF file to MongoDB using GridFS
            pdf_file_id = fs.put(file, filename=file.filename)
            return jsonify({'pdf_file_id': str(pdf_file_id)}), 200

    return jsonify({'error': 'No file uploaded or unsupported file format'}), 400



@app.route('/getTranscript', methods=['POST'])
def gettranscipt():
    data = request.json
    transcript_file_id = data.get('transcript_file_id')
    pdf_file_id = data.get('pdf_file_id')

    if transcript_file_id:
        # Fetch the transcript text from MongoDB using GridFS
        transcript_text = fs.get(ObjectId(transcript_file_id)).read().decode('utf-8')
       
        # Convert the transcript text to PDF
        pdf_filename = transcript_file_id + ".pdf"
        pdf_buffer = BytesIO()
        pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        paragraphs = [Paragraph(f"Speaker {utterance['speaker']}: {utterance['text']}", styles["BodyText"]) for utterance in utterances]
        story = paragraphs

        pdf.build(story)

        #Reset buffer position to start
        pdf_buffer.seek(0)

        # Send the PDF file as a response
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(pdf_buffer.getvalue())
            temp_file.flush()
            response = send_file(temp_file.name, as_attachment=True, mimetype='application/pdf')
            response.headers["Content-Disposition"] = f"attachment; filename={pdf_filename}"
            return response
        
    elif pdf_file_id:
        # Fetch the PDF file from MongoDB using GridFS
        pdf_file = fs.get(ObjectId(pdf_file_id))
        pdf_filename = pdf_file.filename

        # Send the PDF file as a response
        response = make_response(pdf_file.read())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename={pdf_filename}"
        return response


@app.route('/getSummary', methods=['POST'])
def getsummary():
    data = request.json
    transcript_file_id =  data.get('transcript_file_id')
    pdf_file_id = data.get('pdf_file_id')


    if transcript_file_id:
        # Fetch the transcript text from MongoDB using GridFS
        transcript_text = fs.get(ObjectId(transcript_file_id)).read().decode('utf-8')
        # print(transcript_text)
        print("Executed till here")

        # Extract financial sentences and generate summary
        all_financial_sentences = extract_financial_sentences(transcript_text)
        print(all_financial_sentences)
        
        pdf_path = generate_pdf(tempfile.mktemp(suffix='.pdf'), [(1, all_financial_sentences)], "Meta")
        print("This is my received pdf_path: "+pdf_path)
        # Store the PDF file in MongoDB
        with open(pdf_path, 'rb') as pdf_file:
            summary_id = fs.put(pdf_file, filename="summary.pdf")

        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()

        # Check if the PDF content is not empty
        if pdf_content:
            response = make_response(pdf_content)
            response.headers["Content-Disposition"] = "attachment; filename=summary.pdf"
            response.headers["Summary-ID"] = str(summary_id)
            return response
        else:
            return jsonify({"error": "Empty PDF content."})
        
    elif pdf_file_id:
        # Fetch the PDF file from MongoDB using GridFS
        pdf_file_gridfs = fs.get(ObjectId(pdf_file_id))
        print("PDF file fetched from MongoDB:", pdf_file_gridfs.filename)

        pdf_content = pdf_file_gridfs.read()

        

        # Extract text from the PDF file
        extracted_text = extract_text_from_pdf(pdf_content)
        print("Text extracted from PDF:", extracted_text)

        all_financial_sentences = extract_financial_sentences(extracted_text)
        print(all_financial_sentences)
        
        pdf_path = generate_pdf(tempfile.mktemp(suffix='.pdf'), [(1, all_financial_sentences)], "Meta")
        print("This is my received pdf_path: "+pdf_path)
        # Store the PDF file in MongoDB
        with open(pdf_path, 'rb') as pdf_file:
            summary_id = fs.put(pdf_file, filename="summary.pdf")

        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()

        # Check if the PDF content is not empty
        if pdf_content:
            response = make_response(pdf_content)
            response.headers["Content-Disposition"] = "attachment; filename=summary.pdf"
            response.headers["Summary-ID"] = str(summary_id)
            return response
        else:
            return jsonify({"error": "Empty PDF content."})

    else:
        return jsonify({"error": "Empty PDF summary content."})


def extract_text_from_pdf(pdf_content):
    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
    text = ""
    for page_number in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_number].extract_text()
    return text


@app.route('/timeline', methods=['POST'])
def timeline():
    # Receive data from the request
    data = request.json
    transcript_id = data.get('transcript_file_id')
    pdf_id = data.get('pdf_file_id')
    target_word = ''

    if transcript_id :
        # Handle the case where only transcript_id is provided
        # Fetch the transcript from the database
        transcript_content = fs.get(ObjectId(transcript_id)).read().decode('utf-8')

        # Perform any processing specific to transcript analysis
        # For example, you can analyze the sentiment, extract keywords, etc.

        # Prepare and return the response
        # Analyze the text for tense distribution and highlighting
        highlighted_past, percent_past, highlighted_present, percent_present, highlighted_future, percent_future = separate_and_highlight_tenses(transcript_content, target_word)

        # Plot graph for tense distribution
        plot_url = plot_graph(percent_past, percent_present, percent_future)

        # Prepare and return the response
        response_data = {
            "highlighted_past": highlighted_past,
            "percent_past": percent_past,
            "highlighted_present": highlighted_present,
            "percent_present": percent_present,
            "highlighted_future": highlighted_future,
            "percent_future": percent_future,
            "plot_url": plot_url,
            "pdf_id": pdf_id
        }
        return jsonify(response_data), 200

    elif pdf_id :
        # Handle the case where only pdf_id is provided
        # Fetch the PDF from the database
        pdf_content = fs.get(ObjectId(pdf_id)).read()

        # Extract text from PDF
        extracted_text = extract_text_from_pdf(pdf_content)

        # Analyze the text for tense distribution and highlighting
        highlighted_past, percent_past, highlighted_present, percent_present, highlighted_future, percent_future = separate_and_highlight_tenses(extracted_text, target_word)

        # Plot graph for tense distribution
        plot_url = plot_graph(percent_past, percent_present, percent_future)

        # Prepare and return the response
        response_data = {
            "highlighted_past": highlighted_past,
            "percent_past": percent_past,
            "highlighted_present": highlighted_present,
            "percent_present": percent_present,
            "highlighted_future": highlighted_future,
            "percent_future": percent_future,
            "plot_url": plot_url,
            "pdf_id": pdf_id
        }
        return jsonify(response_data), 200

    else:
        # Return an error if both transcript_id and pdf_id are missing or if both are provided
        return jsonify({"error": "Exactly one of transcript_id or pdf_id must be provided."}), 400


    


def poll(transcript_id):
    # Poll - Keep polling the Assembly AI's API to see when the transcription is done
    # combine transcript endpoint with a slash in between with the transcript_id
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    # We have used get because when you send the data to an api, you use post request and when you gain some info you use get request
    polling_response = requests.get(polling_endpoint, headers=headers)
    # what a polling response looks like
    return polling_response.json()

def get_transcription_result_url(audio_url):
    transcript_id = transcribe(audio_url)
    while True:
        data = poll(transcript_id)
        if data['status']=='completed':
            return data, None
        elif data['status']=="error":  
            return data, data['error']
        # print(data)
        
        print('The Earnings Call is under process...')
        time.sleep(30)
        

        
print("Hello! This is backend")

if __name__ == '__main__':
    app.run(debug=True)