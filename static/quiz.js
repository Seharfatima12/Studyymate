// Quiz: pick a subject, answer 4 questions, see the score (saved when logged in)
document.addEventListener("DOMContentLoaded", () => {
  const box = document.getElementById("quizBox"), tabs = document.querySelectorAll("#quizTabs .plan-tab");
  tabs.forEach(t => t.addEventListener("click", () => {
    tabs.forEach(x => x.classList.toggle("active", x === t));
    load(t.dataset.key);
  }));

  async function load(key) {
    const qs = await (await fetch("/api/quiz/" + key)).json();
    let i = 0, score = 0;
    function show() {
      if (i >= qs.length) return finish();
      const q = qs[i];
      box.innerHTML = `<p class="plan-subtitle">Question ${i + 1} of ${qs.length}</p><h2></h2><div class="opts"></div>`;
      box.querySelector("h2").textContent = q.q;
      const opts = box.querySelector(".opts");
      q.options.forEach((text, n) => {
        const b = document.createElement("button");
        b.className = "opt"; b.textContent = text;
        b.addEventListener("click", () => {
          opts.querySelectorAll("button").forEach((o, k) => {
            o.disabled = true;
            if (k === q.answer) o.classList.add("right");
          });
          if (n === q.answer) score++; else b.classList.add("wrong");
          const next = document.createElement("button");
          next.className = "btn btn-primary"; next.textContent = i + 1 < qs.length ? "Next question" : "See score";
          next.addEventListener("click", () => { i++; show(); });
          box.appendChild(next);
        });
        opts.appendChild(b);
      });
    }
    async function finish() {
      let saved = false;
      try { saved = (await (await fetch(`/api/quiz/${key}/score`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ score }) })).json()).saved; } catch (e) {}
      const msg = score === qs.length ? "Perfect score!" : score >= qs.length / 2 ? "Good work. Revise the missed ones." : "Keep practising. Check the study plan.";
      box.innerHTML = `<h2>You scored ${score}/${qs.length}</h2><p class="plan-subtitle">${msg}</p>
        <p class="plan-subtitle">${saved ? "Score saved to your dashboard." : 'Log in to save your scores.'}</p>
        <button class="btn btn-primary" id="again">Try again</button>`;
      document.getElementById("again").addEventListener("click", () => load(key));
    }
    show();
  }

  const want = new URLSearchParams(location.search).get("subject");
  const tab = want && document.querySelector(`#quizTabs [data-key="${want}"]`);
  if (tab) tab.click();
});
