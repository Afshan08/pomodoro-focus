// Initialize variables (these will be set from global variables defined in HTML)
let timeLeft;
let timer;
let isRunning = false;
let SHORT_BREAK_DURATION;
let LONG_BREAK_DURATION;
let FOCUS_DURATION;
let sessions = 0;
let audio = new Audio("../static/clock-alarm.mp3");

let timerStartTime = null;
let currentSessionType = 'pomodoro'; // default session type

// Play/pause utility
function playSound() {
    audio.currentTime = 0;
    audio.play();
}

function stopSound() {
    audio.pause();
    audio.currentTime = 0;
}

// Mode switching


async function switchMode(mode) {
    if (isRunning && timerStartTime && currentSessionId) {
        // Await cancellation of current running session before switching mode
        await sendTimerData('cancelled');
    }

    stopSound();
    clearInterval(timer);
    isRunning = false;
    timerStartTime = null;
    currentSessionId = null;  // Reset session ID whenF switching mode

    if (mode === 'focus') {
        timeLeft = FOCUS_DURATION;
        currentSessionType = 'pomodoro';
    } else if (mode === 'short-break') {
        timeLeft = SHORT_BREAK_DURATION;
        currentSessionType = 'short_break';
    } else if (mode === 'long-break') {
        timeLeft = LONG_BREAK_DURATION;
        currentSessionType = 'long_break';
    }

    setBodyClass(mode);
    setActiveMode(mode);
    updateDisplay();
}

// Visual updates
function updateDisplay() {
    let minutes = Math.floor(timeLeft / 60);
    let seconds = timeLeft % 60;
    document.getElementById("timer").textContent =
        `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function setBodyClass(mode) {
    document.body.classList.remove('focus-mode', 'short-break-mode', 'long-break-mode');
    if (mode) {
        document.body.classList.add(`${mode}-mode`);
    }
}

function setActiveMode(mode) {
    document.querySelectorAll(".buttons").forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`${mode}-btn`).classList.add('active');
}

// Timer logic
function startTimer() {
    if (isRunning) return; // prevent double starts

    stopSound();
    clearInterval(timer);
    isRunning = true;
    timerStartTime = new Date();

    updateDisplay();
    startCountDown();
}


async function resetTimer() {
    if (isRunning && timerStartTime && currentSessionId) {
        // await sendTimerData('cancelled');
    }
    stopSound();
    clearInterval(timer);
    isRunning = false;
    timeLeft = FOCUS_DURATION;
    updateDisplay();
    setBodyClass('focus');
    setActiveMode('focus');
    currentSessionId = null; // Reset session ID on reset
}


function startCountDown() {
    // Removed guard clause to allow countdown to start even if isRunning is true

    isRunning = true;
    timer = setInterval(() => {
        if (timeLeft > 0) {
            timeLeft--;
            updateDisplay();
        } else {
            playSound();
            clearInterval(timer);
            
            alert("Time's up!");
            isRunning = false;
            sendTimerData('completed');
            timerStartTime = null;
        }
    }, 1000);
    
}

let currentSessionId = null;

function sendTimerData(status) {
    if (!isAuthenticated || !timerStartTime) {
        return;
    }

    const endTime = new Date();
    const durationSeconds = Math.floor((endTime - timerStartTime) / 1000);
    const durationMinutes = Math.floor(durationSeconds / 60);

    let data = {
        session_id: currentSessionId,
        session_type: currentSessionType,
        status: status,
        duration_minutes: durationMinutes,
        start_time: timerStartTime.toISOString(),
        end_time: endTime.toISOString()
    };

    fetch('/api/timer_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            console.error('Failed to send timer data');
            return null;
        }
        return response.json();
    })
    .then(data => {
        if (data) {
            currentSessionId = data.session_id;
            console.log("Session ID:", currentSessionId);
        }
    })
    .catch(error => {
        console.error('Error sending timer data:', error);
    });
}

function startTimer() {
    if (isRunning) return; // prevent double starts

    stopSound();
    clearInterval(timer);
    isRunning = true;
    timerStartTime = new Date();

    updateDisplay();
    startCountDown();

    // Send inprogress status when timer starts
    sendTimerData('inprogress');
    
}

function resetTimer() {
    stopSound();
    clearInterval(timer);
    isRunning = false;
    timeLeft = FOCUS_DURATION;
    updateDisplay();
    setBodyClass('focus');
    setActiveMode('focus');
    currentSessionId = null; // Reset session ID on reset
}

function startCountDown() {
    isRunning = true;
    timer = setInterval(() => {
        if (timeLeft > 0) {
            timeLeft--;
            updateDisplay();
        } else {
            playSound();
            clearInterval(timer);
            
            alert("Time's up!");
            isRunning = false;
            sendTimerData('completed');
            timerStartTime = null;
            currentSessionId = null; // Reset session ID after completion
        }
    }, 1000);
}

window.addEventListener('beforeunload', (event) => {
    if (isRunning && timerStartTime && currentSessionId) {
        sendTimerData('cancelled');
    }
});

async function shortBreak() {
    stopSound();
    clearInterval(timer);
    isRunning = false;

    setBodyClass('short-break');
    setActiveMode('short-break');
    timeLeft = SHORT_BREAK_DURATION;
    console.log("SHORT_BREAK_DURATION:", SHORT_BREAK_DURATION);
    console.log("timeLeft for short break:", timeLeft);
    updateDisplay();

    // Start the short break timer session
    timerStartTime = new Date();
    currentSessionType = 'short_break';
    currentSessionId = null;
    await sendTimerData('inprogress');
    shortBreak();
}

async function longBreak() {
    stopSound();
    clearInterval(timer);
    isRunning = false;

    setBodyClass('long-break');
    setActiveMode('long-break');
    timeLeft = LONG_BREAK_DURATION;
    updateDisplay();

    // Start the long break timer session
    timerStartTime = new Date();
    currentSessionType = 'long_break';
    currentSessionId = null;
    await sendTimerData('inprogress');
}

// Initialization on page load
window.onload = function () {
    SHORT_BREAK_DURATION = Number(short_break_duration);
    LONG_BREAK_DURATION = Number(long_break_duration);
    FOCUS_DURATION = Number(focus_session);
    timeLeft = FOCUS_DURATION;

    updateDisplay();
};

// Button bindings
document.getElementById('focus').addEventListener('click', () => switchMode('focus'));
document.getElementById('short-break-btn').addEventListener('click', () => switchMode('short-break'));
document.getElementById('long-break-btn').addEventListener('click', () => switchMode('long-break'));
document.getElementById('start').addEventListener('click', startTimer);
