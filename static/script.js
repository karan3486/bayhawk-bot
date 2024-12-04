
function toggleButton() {
      const input = document.getElementById("message-input");
      const sendButton = document.getElementById("send-button");
      const audioButton = document.getElementById("audio-button");

      if (input.value.trim() !== "") {
        // Show the "Send" button and hide the "Audio Record" button
        sendButton.classList.remove("hidden");
        audioButton.classList.add("hidden");
      } else {
        // Show the "Audio Record" button and hide the "Send" button
        sendButton.classList.add("hidden");
        audioButton.classList.remove("hidden");
      }
    }

// Show spinner
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
// Function to send a message
function handleEnter(event) {
  // debugger;
  if (event.key === "Enter") {
    sendMessage();
  }
}
function addMessage(text, isUser = true, audioUrl = false) {
  // const messageInput = document.getElementById("message-input");
  const chatContainer = document.getElementById("chat-container");
  if(isUser){
    const userMessage = document.createElement("div");
    userMessage.className = "flex justify-end";
    userMessage.innerHTML = `<div class="chat-bubble user-bubble">${text}</div>`;
    chatContainer.appendChild(userMessage);
  }
  if(!isUser && !audioUrl){
    const botMessage = document.createElement("div");
    botMessage.className = "flex";
    botMessage.innerHTML = `<div class="chat-bubble bot-bubble">${text.answer}</div>`;
    chatContainer.appendChild(botMessage);
    
  }
  if(audioUrl){
      // Create the main container for the bot message
          const botMessage = document.createElement("div");
          botMessage.className = "flex bot-audio";

          // Create the chat bubble container
          const chatBubble = document.createElement("div");
          chatBubble.className = "chat-bubble bot-bubble";

          // Create the audio player
          const audioPlayer = createAudioPlayer(audioUrl);

          // Append the audio player to the chat bubble
          chatBubble.appendChild(audioPlayer);

          // Append the chat bubble to the bot message container
          botMessage.appendChild(chatBubble);

          // Add the bot message to the chat container
          chatContainer.appendChild(botMessage);

    }
  chatContainer.scrollTop = chatContainer.scrollHeight;
  

  // const messageDiv = document.createElement("div");
  // messageDiv.className = `message ${isUser ? "user" : "bot"}`;

  // if (text) {
  //   messageDiv.textsContent = text; // Add text if provided
  // }

  // if (audioUrl) {
  //   const audioPlayer = createAudioPlayer(audioUrl);
  //   messageDiv.appendChild(audioPlayer); // Add audio player if audio URL is provided
  // }

  // messagesContainer.appendChild(messageDiv);
  // messageDiv.scrollIntoView({ behavior: "smooth" });
}

async function sendMessage() {
  toggleBlur();
  toggleButton();
  const messageInput = document.getElementById("message-input");
  const chatContainer = document.getElementById("chat-container");

  // Get the message text and clear the input
  const messageText = messageInput.value.trim();
  messageInput.value = "";

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

  // Send the question to the server and get the response
  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: messageText , isRecord: isRecord}),
    });
    const data = await response.json();

    // Create a new bot message bubble with the response
    const botMessage = document.createElement("div");
    botMessage.className = "flex";
    botMessage.innerHTML = `<div class="chat-bubble bot-bubble">${data.answer}</div>`;
    chatContainer.appendChild(botMessage);

    const audioDiv = document.querySelector('.flex.bot-audio');
    // Check if the element exists and remove it
    if (audioDiv) {
        audioDiv.remove();
        console.log('Element removed successfully!');
    } else {
        console.log('Element not found!');
    }

    // Add and autoplay the bot's audio response
    if (data.audio_url) {
      const audioUrl = data.audio_url;
      addMessage("", false, audioUrl); // Add audio to bot's chat section
    }

    // Scroll to the latest message
    chatContainer.scrollTop = chatContainer.scrollHeight;
  } catch (error) {
    console.error("Error fetching bot response:", error);
  } finally {
    // Hide spinner once the response is received
    hideSpinner();
    toggleBlur();
    toggleButton();
    isRecord = false;
  }
}

let isRecording = false;
let progress = 0;
let timer = 0;
let timerInterval;
let progressInterval;
let mediaRecorder;
let audioChunks = [];
var isRecord = false;

const progressBar = document.querySelector(".progress");
const counter = document.querySelector(".counter-btn");
const soundWave = document.querySelector(".sound-wave");
const timerDisplay = document.querySelector(".timer");
const recordingInterface = document.querySelector(".recording-interface");
const micButton = document.querySelector(".mic-btn");
const messagesContainer = document.querySelector(".messages");
let count = 0;
// function showLoader() {
//   let loaderDiv = document.querySelector(".loading-gif");
//   loaderDiv.style.display = "block";
// }

// // Function to remove the loader
// function removeLoader() {
//   let loaderDiv = document.querySelector(".loading-gif");
//   loaderDiv.style.display = "none";
// }

// Function to create an audio player element
function createAudioPlayer(audioUrl) {
  debugger;
  const audioPlayer = document.createElement("div");
  audioPlayer.className = "audio-player";

  // Create the play button
  const playBtn = document.createElement("button");
  playBtn.className = "play-btn";
  playBtn.innerHTML = `
<svg width="12" height="12" viewBox="0 0 24 24" fill="white">
<path d="M8 5v14l11-7z"/>
</svg>
`;

  // Create the timer display
  const timerDisplay = document.createElement("span");
  timerDisplay.className = "audio-timer";
  timerDisplay.textContent = "0:00";

  // Create the duration display
  const durationDisplay = document.createElement("span");
  durationDisplay.className = "audio-duration";
  durationDisplay.textContent = "/0:00";

  // Create the progress slider
  const progressSlider = document.createElement("input");
  progressSlider.type = "range";
  progressSlider.className = "progress-slider";
  progressSlider.min = 0;
  progressSlider.max = 100;
  progressSlider.value = 0;

  // Initialize audio
  const audio = new Audio(audioUrl);

  // Autoplay audio when loaded
  audio.addEventListener("loadedmetadata", () => {
    audio.play(); // Start playing as soon as metadata is loaded
    playBtn.innerHTML = `
<svg width="12" height="12" viewBox="0 0 24 24" fill="white">
  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
</svg>
`;
    const duration = Math.floor(audio.duration);
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    durationDisplay.textContent = ` / ${minutes}:${seconds
      .toString()
      .padStart(2, "0")}`;
    progressSlider.max = duration;
  });

  // Update the timer and progress slider during playback
  audio.addEventListener("timeupdate", () => {
    const currentTime = Math.floor(audio.currentTime);
    const minutes = Math.floor(currentTime / 60);
    const seconds = currentTime % 60;
    timerDisplay.textContent = `${minutes}:${seconds
      .toString()
      .padStart(2, "0")}`;
    progressSlider.value = audio.currentTime;
  });

  // Update audio playback position when slider is adjusted
  progressSlider.addEventListener("input", () => {
    audio.currentTime = progressSlider.value;
  });

  // Reset the play button and timer when audio ends
  audio.addEventListener("ended", () => {
    playBtn.innerHTML = `
<svg width="12" height="12" viewBox="0 0 24 24" fill="white">
  <path d="M8 5v14l11-7z"/>
</svg>
`;
    timerDisplay.textContent = "0:00";
    progressSlider.value = 0;
  });

  // Play/pause toggle on button click
  playBtn.addEventListener("click", () => {
    if (audio.paused) {
      audio.play();
      playBtn.innerHTML = `
  <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
  </svg>
`;
    } else {
      audio.pause();
      playBtn.innerHTML = `
  <svg width="12" height="12" viewBox="0 0 24 24" fill="white">
    <path d="M8 5v14l11-7z"/>
  </svg>
`;
    }
  });

  // Append elements to the audio player
  audioPlayer.appendChild(playBtn);
  audioPlayer.appendChild(timerDisplay);
  audioPlayer.appendChild(durationDisplay);
  audioPlayer.appendChild(progressSlider);

  return audioPlayer;
}

// Function to add a message to the chat UI

// Start recording audio
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: true,
    });

    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.start(100);
    isRecording = true;
    progress = 0;
    timer = 0;
    // micButton.classList.add("hidden");
    recordingInterface.classList.remove("hidden");
    startProgressAndTimer();
    soundWave.classList.add("active");
  } catch (err) {
    console.error("Error accessing microphone:", err);
    alert("Microphone access is required to record audio.");
  }
}

// Update progress bar and timer during recording
function startProgressAndTimer() {
  clearInterval(progressInterval);
  clearInterval(timerInterval);

  progressInterval = setInterval(() => {
    if (isRecording && progress < 100) {
      progress += 1;
      progressBar.style.width = `${progress}%`;
    }
  }, 100);

  timerInterval = setInterval(() => {
    if (isRecording) {
      timer++;
      const minutes = Math.floor(timer / 60);
      const seconds = timer % 60;
      timerDisplay.textContent = `${minutes}:${seconds
        .toString()
        .padStart(2, "0")}`;
    }
  }, 1000);
}

// Stop recording audio
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach((track) => track.stop());
  }

  isRecording = false;
  progress = 0;
  clearInterval(progressInterval);
  clearInterval(timerInterval);
  progressBar.style.width = "0%";
  soundWave.classList.remove("active");
//   micButton.classList.remove("hidden");
  recordingInterface.classList.add("hidden");
  timerDisplay.textContent = "0:00";
}

// Send the recorded audio to the backend server
async function sendAudioToServer() {
  toggleBlur();
  const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
  const formData = new FormData();
  showSpinner();
  debugger;
  formData.append("audio", audioBlob, "recording.webm");
  debugger; 

  try {
    // Send audio to the backend API
    const response = await fetch("/transcribe", {
      method: "POST",
      body: formData,
    });
    debugger

    if (!response.ok) {
      throw new Error("Failed to transcribe audio");
    }

    const data = await response.json();
    // Select all elements with the 'message bot' class
    const audioDiv = document.querySelector('.flex.bot-audio');

    // Check if the element exists and remove it
    if (audioDiv) {
        audioDiv.remove();
        console.log('Element removed successfully!');
    } else {
        console.log('Element not found!');
    }

    // Add transcription as a user message
    if (data.transcription) {
      addMessage(data.transcription, true); // Add user transcription
    }

    // Add bot reply as a text message
    if (data.reply) {
      addMessage(data.reply, false); // Add bot reply
    }

    // Add and autoplay the bot's audio response
    if (data.audio_url) {
      const audioUrl = data.audio_url;
      addMessage("", false, audioUrl); // Add audio to bot's chat section
    }
    hideSpinner();
    toggleBlur();
  } catch (err) {
    debugger;
    console.error("Error sending audio:", err);
    addMessage("Error: Failed to process your audio.", false);
    hideSpinner();
    toggleBlur();
  }
}
async function getAudioTranslate() {
  toggleBlur();
  const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
  const formData = new FormData();
  showSpinner();
  toggleButton();
  debugger;
  formData.append("audio", audioBlob, "recording.webm");
  debugger; 

  try {
    // Send audio to the backend API
    const response = await fetch("/translate", {
      method: "POST",
      body: formData,
    });
    debugger

    if (!response.ok) {
      throw new Error("Failed to transcribe audio");
    }

    const data = await response.json();
    // Select all elements with the 'message bot' class
    // const audioDiv = document.querySelector('.flex.bot-audio');

    // Check if the element exists and remove it
    // if (audioDiv) {
    //     audioDiv.remove();
    //     console.log('Element removed successfully!');
    // } else {
    //     console.log('Element not found!');
    // }

    // Add transcription as a user message
    if (data.transcription) {
      // addMessage(data.transcription, true); // Add user transcription
      document.getElementById('message-input').value = data.transcription
      
    }

    // Add bot reply as a text message
    // if (data.reply) {
    //   addMessage(data.reply, false); // Add bot reply
    // }

    // Add and autoplay the bot's audio response
    // if (data.audio_url) {
    //   const audioUrl = data.audio_url;
    //   addMessage("", false, audioUrl); // Add audio to bot's chat section
    // }
    hideSpinner();
    toggleBlur();
    toggleButton();

  } catch (err) {
    debugger;
    console.error("Error sending audio:", err);
    addMessage("Error: Failed to process your audio.", false);
    hideSpinner();
    toggleBlur();

  }
}

// Event listeners for recording and sending audio
document.querySelector(".cancel-btn").addEventListener("click", () => {
  stopRecording();
});

micButton.addEventListener("click", () => {
  startRecording();
});

document
  .querySelector(".send-btn")
  .addEventListener("click", async () => {
    recordingInterface.classList.add("hidden");
    // await sendAudioToServer();
    await getAudioTranslate();
    stopRecording();
    isRecord = true;
    count++;
    counter.textContent = `Hello, ${count}, ${count + 1}, ${count + 2}`;
  });
