from flask import Flask, render_template, request, jsonify,send_file
from config import Config
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
# from openai import OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader, UnstructuredURLLoader,SeleniumURLLoader
from langchain.memory import SimpleMemory
import os
from utility import transcribe_audio, generate_tts
import os
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate ,MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain,create_history_aware_retriever
from langchain.chains import create_retrieval_chain

app = Flask(__name__)
app.config.from_object(Config)

from langchain_astradb import AstraDBVectorStore
ASTRA_DB_API_ENDPOINT=app.config['ASTRA_DB_API_ENDPOINT']
ASTRA_DB_APPLICATION_TOKEN=app.config['ASTRA_DB_TOKEN']
ASTRA_DB_KEYSPACE="default_keyspace"


# Initialize embedding model and LLM
embedding_model = OpenAIEmbeddings(api_key=app.config['OPENAI_API_KEY'])
llm = ChatOpenAI(model = 'ft:gpt-3.5-turbo-0125:personal:sfbu:AZOUcptb',api_key=app.config['OPENAI_API_KEY'])

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
    pdf_loader = PyPDFLoader(file_path="data/studenthandbook.pdf")
    docs.extend(pdf_loader.load())
    transcript = get_youtube_docs(youtube_urls)
    if transcript:
        docs.append(transcript)
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
    '''You are an academic support assistant for San Francisco Bay University (SFBU). Your primary role is to help students,
    staff, and visitors by providing clear, accurate information about the university's resources, policies, and services. 
    Be concise, professional, and ensure your answers are specific to SFBU. You can interact with user for cross questions to clarify the query with further sub query. 
    Reply with html format in bullet points or sub bullet points if required.
    Avoid providing unrelated or speculative information. Do not provide any other unrelated data that are not related to sfbu.
    Your responses should be concise and strictly related to the provided context'''
    "Use the following pieces of retrieved context to answer the question "
    "If any unrelated question is asked Or you don't know the answer,reply with: I'm sorry, I can only assist with SFBU support-related queries."
    
    "\n\n"
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
history_aware_retriever = create_history_aware_retriever(llm,vectorstore.as_retriever(search_type="mmr",search_kwargs={'k': 5, 'fetch_k': 50}),contextualize_q_prompt)
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
def get_reply(question):
    global chat_history
    inputs = {
        "system":system_prompt,
        "question": question,
        "chat_history": chat_history
    }
    # response = qa_chain.invoke(inputs)
    # chat_history.append((question, response['answer']))
    response = rag_chain.invoke({"input": question, "chat_history": chat_history})
    chat_history.extend(
    [
        HumanMessage(content=question),
        AIMessage(content=response["answer"]),
    ]
)
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