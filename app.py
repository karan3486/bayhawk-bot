from flask import Flask, render_template, request, jsonify,send_file
from config import Config
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
# from openai import OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader, UnstructuredURLLoader
from langchain.memory import SimpleMemory
import os
from utility import transcribe_audio, generate_tts
import os
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate ,MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain,create_history_aware_retriever
from langchain.chains import create_retrieval_chain
from langchain_core.documents import Document

app = Flask(__name__)
app.config.from_object(Config)

from langchain_astradb import AstraDBVectorStore
ASTRA_DB_API_ENDPOINT=app.config['ASTRA_DB_API_ENDPOINT']
ASTRA_DB_APPLICATION_TOKEN=app.config['ASTRA_DB_TOKEN']
ASTRA_DB_KEYSPACE="default_keyspace"


# Initialize embedding model and LLM
embedding_model = OpenAIEmbeddings(api_key=app.config['OPENAI_API_KEY'])
llm = ChatOpenAI(model = 'ft:gpt-4o-2024-08-06:personal:sfbu:AaYozmiq',temperature=0.4,api_key=app.config['OPENAI_API_KEY'])

def get_youtube_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtube':
        return parsed_url.path[1:]
    elif parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        return parse_qs(parsed_url.query).get('v', [None])[0]
    return None
youtube_urls = [
    'https://www.youtube.com/watch?v=kuZNIvdwnMc',
    # Add more URLs here if needed
]
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from langchain.schema import Document
def get_youtube_docs(youtube_urls):
    transcript = None
    for url in youtube_urls:
        youtube_id = get_youtube_id(url)
        if youtube_id:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
                transcript_text = " ".join([t['text'] for t in transcript])
                return Document(page_content=transcript_text, metadata={"source": f"YouTube video {youtube_id}"})
                print(f"Transcript for video ID {youtube_id} added.")
            except Exception as e:
                print(f"Could not retrieve transcript for video ID {youtube_id}: {e}")
        else:
            print(f"Invalid YouTube URL: {url}")
# Function to load documents
def load_documents():
    docs = []
    for filename in os.listdir('data'):
    # Check if the file is a PDF
        if filename.endswith(".pdf"):
            # Construct the full file path
            file_path = os.path.join('data', filename)
            
            # Load the PDF and extend the docs list
            pdf_loader = PyPDFLoader(file_path)
            docs.extend(pdf_loader.load())
        elif filename.endswith(".txt"):
            with open(os.path.join('data', filename), 'r', encoding='utf-8') as txt_file:
                # Read the text content and add it as a document
                content = txt_file.read()
                document = Document(
                    page_content=content,
                    metadata={"source": filename}
                )
                docs.append(document)
    with open('data/urls.txt', 'r') as file:
        urls = file.read().splitlines()
        loader = UnstructuredURLLoader(urls=urls)
        data = loader.load()
        # print(data)
        docs.extend(data)
    return docs

# Create vectorstore from documents
documents = load_documents()
vectorstore = FAISS.from_documents(documents, embedding_model)

# Use SimpleMemory instead of ConversationMemory
conversation_memory = SimpleMemory()
system_prompt = (
    '''As an academic support assistant for San Francisco Bay University (SFBU), your primary role is to help students, staff, and visitors by providing clear and accurate information about the university's resources, policies, and services.

- **Conciseness and Professionalism:** Ensure your responses are concise, professional, and specific to SFBU.
- **Contextual Relevance:** Use the provided context to answer queries. Avoid giving unrelated or speculative information. 
  - Note: Before responding, determine whether the user's query is explicitly related to SFBU's resources, policies, or services. If not, use the predefined response without further processing.
- **Limitation Acknowledgment:** If a question is unrelated to SFBU or if you do not know the answer, respond with: "I'm sorry, I can only assist with SFBU support-related queries." Refrain from further processing.
- **Query Clarification:** Feel free to ask follow-up questions to clarify any vague queries.

# Steps

0. **Check Query Relevance:** Determine whether the user's query is related to SFBU resources, policies, or services. If it is unrelated, use the predefined response and stop further processing.
1. **Analyze the Query:** Understand the user's question or request clearly. If the query seems vague, engage in clarifying questions.
2. **Contextual Reference:** Use relevant information from the given context to answer the question accurately.
3. **Response Construction:** Formulate your answer in a concise and professional manner.
4. **Handle Unknown or Irrelevant Queries:** 
   - If the query is unrelated, respond: "I'm sorry, I can only assist with SFBU support-related queries."
   - If the query is SFBU-related but cannot be answered, respond: "I'm sorry, I don't have the information you're looking for. Please contact SFBU support for further assistance."

# Output Format

- Responses should be in .md markdown format only content, concise, and specifically relevant to SFBU.
- If applicable, use one of the predefined responses as outlined above.

# Notes

- Maintain the primary focus on queries relating to SFBU resources, policies, and services.
- Avoid discussing topics not directly related to SFBU to ensure the information provided remains pertinent and accurate.
'''
"context:"
"{context}"
)

# chat_prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", system_prompt),
#         ("human", "{input}"),
#     ]
# )

# Create conversational retrieval chain
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    memory=conversation_memory
)
# question_answering_chain=create_stuff_documents_chain(llm, chat_prompt)
# rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answering_chain)
chat_history = []
retriever_prompt = (
    "Given a chat history and the latest user question which might reference context in the chat history,"
    "formulate a standalone question which can be understood without the chat history."
    "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
)
contextualize_q_prompt  = ChatPromptTemplate.from_messages(
    [
        ("system", retriever_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),


     ]
)
history_aware_retriever = create_history_aware_retriever(llm,vectorstore.as_retriever(search_kwargs={'k': 3}),contextualize_q_prompt)
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
chat_history_old=[]
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

def moderate(input):
    moderation = llm.moderations.create(input=input)
    res = handle_moderation_response(moderation)
    return res

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sfbu')
def sfbu():
    return render_template('index_2.html')

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get("question")
    isRecord = request.json.get("isRecord")
    # response = get_reply(question)
    # global chat_history
    # inputs = {
    #     "question": question,
    #     "chat_history": chat_history
    # }
    # moderate(question)
    
    try:
        response = get_reply(question)
        
        if isRecord:
            tts_audio_path = generate_tts(response['answer'])
            return jsonify({"answer": response['answer'],"audio_url": f"/audio/{os.path.basename(tts_audio_path)}"})
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return jsonify({"error": "Error during retrieval"}), 500
    return jsonify({"answer": response['answer']})

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

import json

def handle_moderation_response(moderation_output):
    # Extract moderation results
    result = moderation_output["results"][0]
    flagged = result["flagged"]
    categories = result["categories"]
    category_scores = result["category_scores"]
    
    if flagged:
        # Construct response for flagged content
        response = {
            "status": "error",
            "message": "Your input has been flagged for violating content policies.",
            "flagged_categories": [
                category for category, flagged in categories.items() if flagged
            ],
            "category_scores": {
                category: score for category, score in category_scores.items() if score > 0.5
            }
        }
    else:
        # Construct response for non-flagged content
        response = {
            "status": "success",
            "message": "Your input passed moderation checks.",
        }
    
    return json.dumps(response, indent=4)

if __name__ == '__main__':
    app.run(debug=False,port=5000)
#torch                    2.5.1