from flask import Flask, request, jsonify
import logging
import PyPDF2
import os
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Initialize the Flask app
app = Flask(__name__)

# Temporary storage for PDF content
pdf_content = ""


@app.route('/')
def index():
    return "Welcome to the PDF Assistant API!"

@app.route('/upload', methods=['POST'])
def upload_pdf():
    global pdf_content
    file = request.files.get('file')

    if not file or not file.filename.endswith('.pdf'):
        return jsonify({"error": "Please upload a valid PDF file."}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_pdf:
            file.save(temp_pdf.name)
            temp_pdf.close()

            with open(temp_pdf.name, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                pdf_content = "".join([page.extract_text() for page in pdf_reader.pages])

        os.unlink(temp_pdf.name)
        return jsonify({"message": "PDF uploaded successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    global pdf_content
    if not pdf_content:
        return jsonify({"error": "No PDF content available. Please upload a PDF first."}), 400

    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({"error": "Please provide a question."}), 400

    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Only answer questions based on the provided PDF content."
                },
                {
                    "role": "user", 
                    "content": f"The following is content from a PDF document:\n{pdf_content}\n\nBased on this content, answer the question:\n{question}\nIf the question is unrelated to the document, respond with 'This question is outside the context of the uploaded document.'"
                }
            ],
            model="gpt-4o",
        )

        answer = chat_completion.choices[0].message.content.strip()
        return jsonify({"answer": answer}), 200

    except Exception as e:
        logging.error("An error occurred", exc_info=True)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=5555)
