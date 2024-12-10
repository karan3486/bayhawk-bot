from flask import Flask, render_template, request, jsonify,send_file,render_template_string
from config import Config
# from openai import OpenAI
import os
from utility import transcribe_audio, generate_tts
import os
from langchain.schema import AIMessage, HumanMessage
from database import db
from utils.utility import *
from utils.load_data import *

app = Flask(__name__)
app.config.from_object(Config)

# from langchain_astradb import AstraDBVectorStore
# ASTRA_DB_API_ENDPOINT=app.config['ASTRA_DB_API_ENDPOINT']
# ASTRA_DB_APPLICATION_TOKEN=app.config['ASTRA_DB_TOKEN']
# ASTRA_DB_KEYSPACE="default_keyspace"
db.create_table()

 
# Initialize embedding model and LLM
chat_history_old=[]
chat_history = []

def get_reply(question):
    global chat_history
    global chat_history_old
    inputs = {
        "system":system_prompt,
        "question": question,
        "chat_history": chat_history
    }
    res_new =history_aware_retriever.invoke({"input": question, "chat_history": chat_history})
    
    inputs_old = {
        "system":system_prompt,
        "question": question,
        "chat_history": chat_history_old
    }
    # response = qa_chain.invoke(inputs_old)
    # chat_history_old.append((question, response['answer']))
    # res = question_answer_chain.invoke({"input": question, "chat_history": chat_history})
    
    response = rag_chain.invoke({"input": question, "chat_history": chat_history})
    # temp = vectorstore.as_retriever(search_kwargs={'k': 3}).invoke(question)
    # temp = vectorstore.as_retriever(search_type="similarity_score_threshold",search_kwargs={'score_threshold': 0.5}).invoke(question)
    # temp2 = vectorstore.max_marginal_relevance_search_with_score_by_vector().invoke(question)
    "Here are some current events at SFBU:\n\n- **Tai Chi Tuesdays:** Every Tuesday, 12:00PM - 1:00PM, Student Success Hub.\n- **Fireside Chat:** Learn “why” and “how” to adopt the AI Explorer mindset with experts from Ahura.ai, December 3, 3:00PM - 5:00PM.\n- **Toastmasters Meeting:** Every Wednesday, 12:00PM - 1:00PM, Student Success Hub Multi-Purpose Room.\n- **Wellness Wednesdays: Yoga:** Every Wednesday, 12:00PM - 1:00PM, Student Success Hub.\n- **IEEE Meeting:** Every Thursday, 12:00PM - 1:00PM.\n- **SFBU's 40th Anniversary Celebration:** December 7, 3:00PM - 5:00PM, 161 Mission Falls Lane, Fremont, CA 94539.\n- **Weekly Wellness Workshop:** Every week, 12:00PM - 1:00PM.\n\nFor more events, visit [SFBU Events](https://www.sfbu.edu/events)."

    chat_history.extend(
    [
        HumanMessage(content=question),
        AIMessage(content=response["answer"]),
    ]
)   
    if len(chat_history)>=6:
        chat_history = chat_history[2:]
    return response

# def moderate(input):
#     moderation = llm.moderations.create(input=input)
#     res = handle_moderation_response(moderation)
#     return res

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/faculty')
def sfbu():
    return render_template('index_faculty.html')

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get("question")
    isRecord = request.json.get("isRecord")
    language = request.json.get("language")
    if language and language.lower()!='english':
        question =  Langtranslate(question,'English')
    
    try:
        response = get_reply(question)
        print(vectorstore.as_retriever(search_type="mmr",search_kwargs={'k': 5, 'fetch_k': 50}).invoke(question))
        answer = response['answer']
        if language and language.lower()!='english':
            answer = Langtranslate(answer,language)
        
        if isRecord:
            tts_audio_path = generate_tts(response['answer'])
            return jsonify({"answer": response['answer'],"audio_url": f"/audio/{os.path.basename(tts_audio_path)}"})
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return jsonify({"error": "Error during retrieval"}), 500
    return jsonify({"answer": answer})

@app.route("/transcribe", methods=["POST"])
def transcribe():
    audio_file = request.files["audio"]
    transcription = transcribe_audio(audio_file)
    if transcription.startswith("Error"):
        return jsonify({"error": transcription}), 400
    reply = get_reply(transcription)
    tts_audio_path = generate_tts(reply['answer'])
    return jsonify({
        "transcription": transcription,
        "reply": reply,
        "audio_url": f"/audio/{os.path.basename(tts_audio_path)}"
    })

@app.route("/translate", methods=["POST"])
def translate():
    audio_file = request.files["audio"]
    transcription = transcribe_audio(audio_file)
    if transcription.startswith("Error"):
        return jsonify({"error": transcription}), 400
    # reply = get_reply(transcription)
    # tts_audio_path = generate_tts(reply['answer'])
    return jsonify({
        "transcription": transcription,
        "reply": '',
        "audio_url": ""
    })

@app.route("/audio/<filename>")
def audio(filename):
    return send_file(f"./static/audio/{filename}")


# Endpoint to add a conversation
@app.route('/add_conversation', methods=['POST'])
def add_conversation():
    # Get data from the request
    data = request.json
    name = data.get('name')
    email = data.get('email', None)  # Email can be optional
    message_type = data.get('type')  # 'Bot' or 'User'
    content = data.get('content')

    # Validate required fields
    if not all([name, message_type, content]):
        return jsonify({'error': 'Missing required fields: name, type, and content are mandatory.'}), 400

    # Insert the data into the database
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO conversation (name, email, type, content)
        VALUES (?, ?, ?, ?)
        ''', (name, email, message_type, content))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Conversation added successfully!'}), 201
    except Exception as e:
        return jsonify({'error': f'Failed to add conversation: {str(e)}'}), 500

@app.route('/mailtoAdmin', methods=['POST'])
def mailToAdmin():
    email = request.json.get("email")    
    try:
        startMailSending(email)
    except Exception as e:
        print(f"Error during mail sending: {e}")
    return jsonify({"status": 'mail send'})

@app.route('/mailtoVisitor', methods=['POST'])
def mailToVisitor():
    email = request.json.get("email")
    name = request.json.get("name")    
    try:
        sendMailtoGuest(name,email)
    except Exception as e:
        print(f"Error during mail sending: {e}")
    return jsonify({"status": 'mail send'})


@app.route('/generate', methods=['POST'])
def generate_mcqs():
    if 'file' in request.files:
            file = request.files['file']

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Extract text from the uploaded file
                text = extract_text_from_file(file_path)
    else:
        text_input = request.form['text_input']
        if 'http'in text_input:
            text = url_to_text(text_input)
        else:
            text = text_input

    if text:
            num_questions = int(request.form['no_questions'])
            level_mcq = str(request.form['level_mcq'])
            mcqs = Question_mcqs_generator(text, num_questions,level_mcq)

            # Save the generated MCQs to a file
            txt_filename = f"generated_mcqs.txt"
            pdf_filename = f"generated_mcqs.pdf"
            save_mcqs_to_file(mcqs, txt_filename)
            create_pdf(mcqs, pdf_filename)

            # Display and allow downloading
            text = f'/download/{txt_filename}'
            pdf = f'/download/{pdf_filename}'
            # return render_template('results.html', mcqs=mcqs, txt_filename=txt_filename, pdf_filename=pdf_filename)
            rendered_html = render_template('mcq_template.html', mcqs=mcqs, txt_filename=txt_filename, pdf_filename=pdf_filename)

            # Save the rendered HTML to a file
            html_file_path = os.path.join('templates', 'mcq_result.html')
            with open(html_file_path, 'w') as html_file:
                html_file.write(rendered_html)
            return jsonify({'textpath': text,'pdfpath':pdf,"html_path": f"/view/{os.path.basename(html_file_path)}"}), 200
    return "Invalid file format"

@app.route('/generate_ppt', methods=['POST'])
def generate_ppt():
    try:
        # Parse user input
        if 'file' in request.files:
            file = request.files['file']

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Extract text from the uploaded file
                text = extract_text_from_file(file_path)
        else:
            text_input = request.form['text_input']
            if 'http'in text_input:
                text = url_to_text(text_input)
            else:
                text = text_input




        # Use OpenAI to generate content
        no_slides = int(request.form['no_slides'])
        generated_content = getPPTContent(text,no_slides)
        # Parse content into slides (custom parsing logic can be added)
        slides = generated_content.split("\n\n")

        # Create a PowerPoint presentation
        try:
            filename = 'generated_presentation.pptx'
            savePPTFile(slides,filename)
        except Exception as e:
            print(e)

        # Return the path to the frontend
        return jsonify({"ppt_path": f'/download/{filename}'})

    except Exception as e:
        # Save the presentation
        return jsonify({"error": str(e)}), 500

@app.route('/generate_syllabus', methods=['POST'])
def generate_syllabus():
    try:
        # Use OpenAI to generate content
        no_session = request.form['no_session']
        hr_session = request.form['hr_session']
        month_session = request.form['month_session']
        course_info = request.form['course_info']
        syllabus = getSyllabus(course_info,no_session,hr_session,month_session)
        sections = [section.strip() for section in syllabus.split('##') if section.strip()]

        rendered_html = render_template('syllabus_template.html', sections=sections)
            # Save the rendered HTML to a file
        html_file_path = os.path.join('templates', 'syllabus_result.html')
        with open(html_file_path, 'w') as html_file:
            html_file.write(rendered_html)
        # Return the path to the frontend
        return jsonify({"syllabus_path": f"/view/{os.path.basename(html_file_path)}"})

    except Exception as e:
        # Save the presentation
        return jsonify({"error": str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
    return send_file(file_path, as_attachment=True)

@app.route('/view/<filename>')
def view_html(filename):
    # Serve the generated HTML file
    return render_template(f'{filename}')

def sendMailtoGuest(recipient_name,email):
    with app.app_context():
        with open('templates/mailTemplate.html', 'r') as file:
            template = file.read()

        # Render the template with the recipient's name
        rendered_template = render_template_string(template, name=recipient_name)
        send_email(rendered_template,email,'Welcome to San francisco bay university!',True)

if __name__ == '__main__':
    app.run(debug=True,port=4000)
#torch                    2.5.1


