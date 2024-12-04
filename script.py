import os

# Define the file structure
file_structure = {
    "app.py": "# Main application file",
    "config.py": "import os\nfrom dotenv import load_dotenv\n\nload_dotenv()\n\nclass Config:\n    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')\n",
    ".env": "OPENAI_API_KEY=your_openai_api_key",
    "templates/index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <div class="container">
        <h1>Document-Based Chatbot</h1>
        <input type="text" id="question" placeholder="Ask a question...">
        <button onclick="askQuestion()">Ask</button>
        <div id="response"></div>
    </div>
    <script>
        async function askQuestion() {
            const question = document.getElementById("question").value;
            const responseDiv = document.getElementById("response");
            const response = await fetch("/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });
            const data = await response.json();
            responseDiv.innerHTML = `<p>Answer: ${data.answer}</p>`;
        }
    </script>
</body>
</html>""",
    "static/styles.css": """body {
    font-family: Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
}

.container {
    text-align: center;
}

#question {
    width: 100%;
    padding: 8px;
    margin: 10px 0;
}""",
    "data/sample.pdf": "",  # Placeholder for sample PDF
    "data/urls.txt": "https://example.com\nhttps://another-url.com",
    "requirements.txt": """Flask
langchain
dotenv
PyPDF2
openai
faiss-cpu
requests
youtube_transcript_api"""
}

# Function to create directories and files with content
def create_structure(structure):
    for path, content in structure.items():
        # Create directory if not exists
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Write content to the file
        with open(path, "w") as file:
            file.write(content)

# Create the file structure
create_structure(file_structure)
print("Project structure created successfully.")
