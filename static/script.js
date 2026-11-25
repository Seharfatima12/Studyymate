/**
 * StudyMate – Frontend JavaScript
 * Handles chat interaction with the Flask backend
 */

document.addEventListener("DOMContentLoaded", () => {
    const chatMessages = document.getElementById("chatMessages");
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const clearBtn = document.getElementById("clearChat");
    const quickReplies = document.getElementById("quickReplies");

    // Only run chat logic on the chat page
    if (!chatMessages || !chatForm) return;

    // Current subject remembered across messages
    let currentSubject = (typeof initialSubject !== "undefined" && initialSubject)
        ? initialSubject
        : null;

    // ---------- Helper: Add message to UI ----------
    function addMessage(text, sender = "bot", chips = []) {
        const div = document.createElement("div");
        div.className = `message ${sender}`;
        if (sender === "user") div.textContent = text;   // never render user input as HTML
        else div.innerHTML = text;                       // bot HTML comes from our own backend
        if (chips.length) {
            const box = document.createElement("div");
            box.className = "chips";
            chips.forEach(c => {
                const b = document.createElement("button");
                b.className = "chip"; b.type = "button"; b.textContent = c;
                b.addEventListener("click", () => { box.remove(); sendMessage(c); });
                box.appendChild(b);
            });
            div.appendChild(box);
        }
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // ---------- Helper: Show typing indicator ----------
    function showTyping() {
        const div = document.createElement("div");
        div.className = "message bot typing";
        div.id = "typingIndicator";
        div.innerHTML = "StudyMate is typing<span class='dots'>...</span>";
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function hideTyping() {
        const el = document.getElementById("typingIndicator");
        if (el) el.remove();
    }

    // ---------- Send message to backend ----------
    async function sendMessage(message) {
        if (!message.trim()) return;

        // Show user message
        addMessage(message, "user");
        userInput.value = "";

        showTyping();

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: message,
                    subject: currentSubject
                })
            });

            const data = await response.json();
            hideTyping();

            // Update current subject if backend detected one
            if (data.subject) {
                currentSubject = data.subject;
            }

            addMessage(data.reply, "bot", data.chips || []);

        } catch (err) {
            hideTyping();
            addMessage("Sorry, something went wrong. Please try again.", "bot");
            console.error(err);
        }
    }

    // ---------- Form submit ----------
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        sendMessage(userInput.value);
    });

    // ---------- Quick reply buttons ----------
    if (quickReplies) {
        quickReplies.addEventListener("click", (e) => {
            if (e.target.classList.contains("quick-btn")) {
                const msg = e.target.getAttribute("data-msg");
                sendMessage(msg);
            }
        });
    }

    // ---------- Clear chat ----------
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            chatMessages.innerHTML = "";
            currentSubject = null;
            if (LOGGED_IN) fetch("/api/history", { method: "DELETE" });
            welcome();
        });
    }

    // ---------- Welcome + saved history ----------
    const hello = typeof userName !== "undefined" && userName ? `Salam, ${userName}!` : "Hello!";
    const welcome = () => addMessage(
        `${hello} Welcome to <b>StudyMate</b> – Your Personal Study Assistant.<br><br>` +
        "What subject do you want help with today?<br><br>" +
        "You can say:<br>• <i>I need help with Python</i><br>• <i>NLP topics</i><br>• <i>Java study plan</i><br>• <i>Maths tips</i>",
        "bot");

    async function start() {
        let saved = [];
        if (LOGGED_IN) {
            try { saved = (await (await fetch("/api/history")).json()).messages; } catch (e) {}
        }
        if (saved.length) {
            addMessage(`${hello} Your earlier chat is below.`, "bot");
            saved.forEach(m => addMessage(m.text, m.sender));
        } else {
            welcome();
        }
        if (currentSubject) sendMessage(`I need help with ${currentSubject}`);
    }
    start();
});
