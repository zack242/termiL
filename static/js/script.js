// Globals
let mute = false; // Mute/Unmute Flag to track audio state
let typingDelay = 25; // Delay between typing sounds

// Initialize button click
$("#initialize").click(function () {
  $(this)
    .parent()
    .fadeOut(500, function () {
      $(".interface-container").fadeIn();
      waveformVisualizer();
      const prompt =
        "Welcome to A.M.I., your crypto market guide, offering Full Analysis, DEX Check, Bundle Check, and soon, the OG Status Check. Plus, share your CA or chat with me for tailored insights.";
      typeMessage("system", prompt);
    });
});

const phrases = [
  "Oh, it's you,",
  "A.M.I",
  "Automated Market Intelligence",
  "Welcome back to the future of trading.",
  "Dive into Solana's depths,",
  "With AI at your command.",
  "A.M.I. - Your edge, coming soon.",
];

const writer = GlitchedWriter.create("#welcome", "neo");
writer.endless(false);
writer.queueWrite(phrases, 3000, 3000, false);
// writer.addCallback('step', playTypingSound());

function waveformVisualizer() {
  const audioContext = new window.AudioContext();

  // setup canvas
  const canvas = document.querySelector("#waveform");

  // setup audio element
  const audioElement = document.querySelector("#ambient-soundscape-2");

  // create source from html5 audio element
  const source = audioContext.createMediaElementSource(audioElement);

  // attach oscilloscope
  const scope = new Oscilloscope(source);

  // reconnect audio output to speakers
  source.connect(audioContext.destination);

  // customize drawing options
  const ctx = canvas.getContext("2d");
  ctx.lineWidth = 4;
  ctx.strokeStyle = "#4AF626";

  // start default animation loop
  scope.animate(ctx);

  // play
  playSound("ambient-soundscape-2");
}

function getLocation() {
  navigator.geolocation.getCurrentPosition(function (position) {
    yourFunction(position.coords.latitude, position.coords.longitude);
  });
}

function toggleMute() {
  mute = !mute;
  document.getElementById("mute").innerHTML = mute ? "Unmute" : "Mute";
}

async function typeMessage(type, message) {
  var element = document.createElement("div");
  element.classList.add("chat-message");

  if (type == "system") element.classList.add("muted");

  document.getElementById("chat-messages").append(element);

  element.innerHTML = "";
  for (const char of message) {
    element.innerHTML += char;
    playTypingSound();
    await new Promise((resolve) => setTimeout(resolve, typingDelay));
  }
}

// Description: Mute/Unmute the speific sound file in the audio element
// Parameters: ID of the audio element (#id)
function playSound(id, volume = 0.1) {
  if (!mute) {
    var audio = document.getElementById(id);
    audio.muted = false;
    audio.play();
    audio.volume = volume;
  }
}

// Description: Play the typing sounds using a randomizer that picks one of the three sound files, on loop
function playTypingSound() {
  if (!mute) {
    const audioId = "text-streaming-" + (Math.floor(Math.random() * 3) + 1);
    playSound(audioId, 0.1);
  }
}

// Description: Handles chat nessage submission, and replu backs
var chatForm = document.getElementById("input-form");
chatForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  var formData = new FormData(chatForm);
  var chat_input = chatForm.elements["chat_input"].value;
  chatForm.elements["chat_input"].value = "";
  typeMessage("interloper", "You: " + chat_input);

  try {
    const response = await fetch("/completion", {
      method: "POST",
      body: formData,
    });
    const reader = response.body.getReader();
    let text = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      text += new TextDecoder().decode(value);
    }
    await typeMessage("terminal", "Terminal: " + text);
  } catch (error) {
    console.error(error);
  }
});
