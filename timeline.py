from flask import Flask, render_template, request
import PyPDF2
import spacy
from termcolor import colored
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def get_tense(sentence):
    doc = nlp(sentence)
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]

    if 'be' in verbs and 'will' in sentence.lower():
        return 'future'
    elif 'VBD' in [token.tag_ for token in doc]:
        return 'past'
    elif 'VBP' in [token.tag_ for token in doc] or 'VBZ' in [token.tag_ for token in doc]:
        return 'present'
    elif 'MD' in [token.tag_ for token in doc] and 'will' in sentence.lower():
        return 'future'
    else:
        return 'unknown'

def highlight_semantics(sentences, target_word):
    highlighted_sentences = []

    for sentence in sentences:
        doc = nlp(sentence)
        highlighted_sentence = sentence

        for token in doc:
            if token.lemma_.lower() == target_word.lower():
                highlighted_sentence = highlighted_sentence.replace(
                    token.text,
                    colored(token.text, 'red', attrs=['bold'])
                )

        highlighted_sentences.append(highlighted_sentence)

    return highlighted_sentences

# ... (previous functions remain unchanged)
def separate_and_highlight_tenses(text, target_word):
    past_tense_sentences = []
    present_tense_sentences = []
    future_tense_sentences = []

    doc = nlp(text)
    sentences = [sent.text.replace('\n', ' ') for sent in doc.sents]

    for sentence in sentences:
        tense = get_tense(sentence)
        if tense == 'past':
            past_tense_sentences.append(sentence)
        elif tense == 'present':
            present_tense_sentences.append(sentence)
        elif tense == 'future':
            future_tense_sentences.append(sentence)

    highlighted_past = highlight_semantics(past_tense_sentences, target_word)
    highlighted_present = highlight_semantics(present_tense_sentences, target_word)
    highlighted_future = highlight_semantics(future_tense_sentences, target_word)

    total_sentences = len(past_tense_sentences) + len(present_tense_sentences) + len(future_tense_sentences)
    percent_past = (len(past_tense_sentences) / total_sentences) * 100
    percent_present = (len(present_tense_sentences) / total_sentences) * 100
    percent_future = (len(future_tense_sentences) / total_sentences) * 100

    return (
        highlighted_past, percent_past,
        highlighted_present, percent_present,
        highlighted_future, percent_future
    )

def plot_graph(percent_past, percent_present, percent_future):
    labels = ['Past Tense', 'Present Tense', 'Future Tense']
    percentages = [percent_past, percent_present, percent_future]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, percentages, color=['blue', 'green', 'orange'])
    plt.title('Distribution of Tenses')
    plt.xlabel('Tense')
    plt.ylabel('Percentage')
    plt.ylim(0, 100)

    # Convert plot to base64 for embedding in HTML
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return plot_url


def index():
    if request.method == 'POST':
        pdf_path = request.form['pdf_path']
        target_word = request.form['target_word']

        highlighted_past, percent_past, highlighted_present, percent_present, highlighted_future, percent_future = separate_and_highlight_tenses(pdf_path, target_word)

        plot_url = plot_graph(percent_past, percent_present, percent_future)

        return render_template('result.html', 
                               highlighted_past=highlighted_past, percent_past=percent_past,
                               highlighted_present=highlighted_present, percent_present=percent_present,
                               highlighted_future=highlighted_future, percent_future=percent_future,
                               plot_url=plot_url)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
