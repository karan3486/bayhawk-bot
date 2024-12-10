var task = '';
function toggleBlur() {
    const chatContainer = document.getElementById("chat-container");
    if (chatContainer.style.filter === "blur(4px)") {
      chatContainer.style.filter = "none";
    } else {
      chatContainer.style.filter = "blur(4px)";
    }
  }
  
  function showSpinner() {
    document.getElementById('chat-container').style.backgroundImage = '';
    document.getElementById("spinner").style.display = "block";
  }
  
  // Hide spinner
  function hideSpinner() {
      debugger;
  //   document.getElementById('chat-container').style.backgroundImage = 'url("images/bayhawk.png")';
  document.getElementById('chat-container').style.backgroundImage = "url('static/images/bayhawk.png')";
  
    document.getElementById("spinner").style.display = "none";
  }
  function toggleButton() {
    const input = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");
    const audioButton = document.getElementById("gen-button");

    if(task!=''){
        sendButton.classList.add('hidden');
        audioButton.classList.remove('hidden');
        input.setAttribute('disabled', true);
        
    }
    else{
        sendButton.classList.remove('hidden');
        audioButton.classList.add('hidden');
        input.removeAttribute('disabled');
    }
  }
async function sendFacultyMessage() {
    toggleBlur();
    const messageInput = document.getElementById("message-input");
    const chatContainer = document.getElementById("chat-container");
  
    // Get the message text and clear the input
    const messageText = messageInput.value.trim();
    
  
    if (messageText === "") return; // Do nothing if the message is empty

  
    // Create a new user message bubble
    const userMessage = document.createElement("div");
    userMessage.className = "flex justify-end";
    userMessage.innerHTML = `<div class="chat-bubble user-bubble">${messageText}</div>`;
    chatContainer.appendChild(userMessage);
  
    // Scroll to the latest message
    chatContainer.scrollTop = chatContainer.scrollHeight;
    debugger;
    showSpinner();
    if(task){
      subMessage(task);
      toggleBlur();
      hideSpinner();
      return
    }
    messageInput.value = "";
  
    // Send the question to the server and get the response
    try {
      const response = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: messageText}),
      });
      const data = await response.json();
  
      // Create a new bot message bubble with the response
      const botMessage = document.createElement("div");
      botMessage.className = "flex";
      const converter = new showdown.Converter();
      const html = converter.makeHtml(data.answer);
      // botMessage.innerHTML = `<div class="chat-bubble bot-bubble">${html}</div>`;
      botMessage.innerHTML = `<div class="chat-bubble bot-bubble">${html}</div>`;
      chatContainer.appendChild(botMessage);
  
      // Scroll to the latest message
      chatContainer.scrollTop = chatContainer.scrollHeight;
      sendData(user.name,user.email,'User',messageText);
      sendData(user.name,user.email,'Bot',data.answer);
    } catch (error) {
      console.error("Error fetching bot response:", error);
    } finally {
      // Hide spinner once the response is received
      hideSpinner();
      toggleBlur();
      isRecord = false;
    }
  }
  
  document.getElementById('uploadButton').addEventListener('click', function() {
    document.getElementById('fileInput').click();
  });
  document.getElementById('fileInput').addEventListener('change', function(event) {
    const file = event.target.files[0]; // Get the selected file
    console.log('Selected file:', file);
    addMessage(file.name)
    subMessage(task);
  });

  function addMessage(text, isUser = true, audioUrl = false,isdefault = false,isSubmenu = false){
    debugger;
    // const messageInput = document.getElementById("message-input");
    const chatContainer = document.getElementById("chat-container");
    if(isUser){
      const userMessage = document.createElement("div");
      userMessage.className = "flex justify-end";
      userMessage.innerHTML = `<div class="chat-bubble user-bubble">${text}</div>`;
      chatContainer.appendChild(userMessage);
    }
    if(!isUser && !audioUrl && !isdefault){
      const botMessage = document.createElement("div");
      botMessage.className = "flex";
      const converter = new showdown.Converter();
      html = text
      if(text.answer){
        html = converter.makeHtml(text.answer);
      }
      
      botMessage.innerHTML = `<div class="chat-bubble bot-bubble">${html}</div>`;
      chatContainer.appendChild(botMessage);
      
    }
      debugger;
      if(isdefault){
        const botMessage = document.createElement("div");
        botMessage.className = 'chat-bubble-auto bot-bubble-auto'
        // botMessage = `<div class="chat-bubble bot-bubble">${text}</div>`;
        botMessage.innerHTML = text
        chatContainer.appendChild(botMessage);
      }
      if(isSubmenu){
  
      }
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
  }

  function ShowFileUpload(elem){
    debugger
    // toogleEscalate();
    const menu = elem.querySelector(".opt-title-fac"); // Select the <p> tag with the class 'opt-title'
    const menuValue = menu.textContent.trim();
    task = menuValue;
    addMessage(menuValue);
    debugger;
    if(menuValue=='MCQ Generator' || menuValue=='PPT Creator'){
      addMessage('Please UPLOAD the file or enter URL or TYPE below.',false,false,false,false)
    }
    else if(menuValue=='Syllabus Designer'){
      subMessage(task)
      document.getElementById("message-input").removeAttribute('disabled')
    }
    else{
        addMessage('Please type your query below.',false,false,false,false)
    }
    
    
  }

  function subMessage(task){
    debugger
    
     const chatContainer = document.getElementById("chat-container");
     const botMessage = document.createElement("div");
      botMessage.className = "chat-bubble-auto-fac bot-bubble-auto-fac";
      let msg = '';
      if(task=='MCQ Generator'){
        addMessage('Please enter the details and Click on Generate Button.',false,false,false,false)
        msg = MCQ
      }
      else if(task=='PPT Creator'){
        addMessage('Please enter the details and Click on Generate Button.',false,false,false,false)
        msg = PPT
      }
      else if(task=='Syllabus Designer'){
        debugger;
        addMessage('Please provide the below details and type Course info and, Click on Generate Button.',false,false,false,false)
        msg = Syllabus
      }
  
      botMessage.innerHTML = msg;
      chatContainer.appendChild(botMessage);
      chatContainer.scrollTop = chatContainer.scrollHeight;
      toggleButton();

  
  }

  async function GenerateMCQ(){
    addMessage('Generate MCQs.')
    const fileInput = document.getElementById('fileInput');
    const no_questions = document.getElementById('no-questions').value;
    const level = document.getElementById('level');
    const input_txt = document.getElementById('message-input');
    
    const formData = new FormData();
    // Get the selected value
    const level_mcq = level.value;
    const file = fileInput.files[0];
    
    if (!file) {
      if(input_txt.value){
        formData.append('text_input', input_txt.value); 
        
      }else{
        alert('Please upload a file Or type URL.');
      }
    }
    else{
    formData.append('file', file); 
  }

    formData.append('no_questions', no_questions); // Attach additional data
    formData.append('level_mcq', level_mcq); 
    input_txt.value='';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Upload successful:', result);
            addMessage('Here is your MCQ Generated.',false,false,false,false)
            const chatContainer = document.getElementById("chat-container");
            const botMessage = document.createElement("div");
            botMessage.className = "chat-bubble-auto-fac bot-bubble-auto-fac";
            botMessage.innerHTML = `<div class="flex">
          <div class="main-menu default">
          <a class="link-url" href="${result.textpath}" target="_blank">Download Text</a>
        </div>
          <div class="main-menu default">
            <a class="link-url" href="${result.pdfpath}" target="_blank">Download PDF</a>
          </div>
          <div class="main-menu default">
            <a class="link-url" href="${result.html_path}" target="_blank">View</a>
          </div>
          </div>`;
            chatContainer.appendChild(botMessage);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            toggleButton();
            hideSpinner();
            task = ''
            toggleButton()
        } else {
            console.error('Upload failed:', response.statusText);
            alert('Need more context to create the file. Try again!');
            hideSpinner();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the file.');
    }
  }

  async function GeneratePPT(){
    addMessage('Generate PPT.')
    const fileInput = document.getElementById('fileInput');
    const no_slides = document.getElementById('no-slides').value;
    const input_txt = document.getElementById('message-input');
    // const level = document.getElementById('level');
    
    // Get the selected value
    // const level_mcq = level.value;
    const file = fileInput.files[0];
    const formData = new FormData();
    // Attach the file
    formData.append('no_slides', no_slides); // Attach additional data

    if (!file) {
        if(input_txt.value){
          formData.append('text_input', input_txt.value); 

        }else{
          alert('Please upload a file Or type URL.');
        }
    }
    else{
      formData.append('file', file); 
    }

    
    // formData.append('level_mcq', level_mcq); 

    input_txt.value='';
    try {
        const response = await fetch('/generate_ppt', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Upload successful:', result);
            addMessage('Here is your PPT Generated.',false,false,false,false)
            const chatContainer = document.getElementById("chat-container");
            const botMessage = document.createElement("div");
            botMessage.className = "chat-bubble-auto-fac bot-bubble-auto-fac";
            botMessage.innerHTML = `<div class="flex">
          <div class="main-menu default">
          <a class="link-url" href="${result.ppt_path}" target="_blank">Download PPTX</a>
        </div>
          </div>`;
            chatContainer.appendChild(botMessage);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            toggleButton();
            hideSpinner();
            task=''
            toggleButton()
        } else {
            console.error('Upload failed:', response.statusText);
            alert('Need more context to create the file. Try again!');
            hideSpinner();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the file.');
    }
  }

  async function GenerateSyllabus(){
    addMessage('Generate Syllabus.')
    const no_session = document.getElementById('no-session').value;
    const hr_session = document.getElementById('hr-session').value;
    const month_session = document.getElementById('month-session').value;
    const course_info = document.getElementById('message-input').value;
    addMessage(course_info)
    

    const formData = new FormData();
    formData.append('no_session', no_session); // Attach the file
    formData.append('hr_session', hr_session); // Attach additional data
    formData.append('month_session', month_session); 
    formData.append('course_info', course_info); 
    document.getElementById('message-input').value = '';

    try {
        const response = await fetch('/generate_syllabus', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Upload successful:', result);
            addMessage('Here is your syllabus Generated.',false,false,false,false)
            const chatContainer = document.getElementById("chat-container");
            const botMessage = document.createElement("div");
            botMessage.className = "chat-bubble-auto-fac bot-bubble-auto-fac";
            botMessage.innerHTML = `<div class="flex">
          <div class="main-menu default">
          <a class="link-url" href="${result.syllabus_path}" target="_blank">View Syllabus</a>
        </div>
          </div>`;
            chatContainer.appendChild(botMessage);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            // toggleButton();
            hideSpinner();
            task='';
            toggleButton();
        } else {
            console.error('Upload failed:', response.statusText);
            alert('Need more context to create the file.Try again!');
            hideSpinner();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the file.');
    }
  }

function Generate(){
  debugger;
  showSpinner();
  try{

    if(task=='MCQ Generator'){
        GenerateMCQ();
    }
    else if(task=='PPT Creator'){
        GeneratePPT();
    }
    else if(task=='Syllabus Designer'){
      GenerateSyllabus();
  }
  } catch(error){
    hideSpinner();
    alert('Error:', error);
    
  }
}
const MCQ = `<div class="flex">
          <div class="main-menu default" id="opt-admission">
             <input style="border-radius: 6px;outline: none;background-color: #cde6ff;width: 9rem;" type="number" placeholder="Number of Questions" id="no-questions" >
          </div>
          <div class="main-menu default" id="opt-financial">
            <select id="level" name="level">
              <option value="Easy" {% if language == "Easy" %}selected{% endif %}>Easy</option>
              <option value="Medium" {% if language == "Medium" %}selected{% endif %}>Medium</option>
              <option value="Hard" {% if language == "Hard" %}selected{% endif %}>Hard</option>
            </select>
          </div>
          </div>`;

const PPT = `<div class="flex">
          <div class="main-menu default">
             <input style="border-radius: 6px;outline: none;background-color: #cde6ff;width: 9rem;" type="number" placeholder="Number of Slides" id="no-slides" >
          </div>
          </div>`;

const Syllabus = `<div class="flex">

          <div class="main-menu default">
             <input style="border-radius: 6px;outline: none;background-color: #cde6ff;width: 9rem;" type="number" placeholder="Session per Week" id="no-session" >
          </div>
          <div class="main-menu default">
             <input style="border-radius: 6px;outline: none;background-color: #cde6ff;width: 9rem;" type="number" placeholder="Hours per Session" id="hr-session" >
          </div>
          </div>
          <div class="flex">
          <div class="main-menu default">
             <input style="border-radius: 6px;outline: none;background-color: #cde6ff;width: 10rem;" type="number" placeholder="Semester total months" id="month-session" >
          </div>
          </div>
          `;