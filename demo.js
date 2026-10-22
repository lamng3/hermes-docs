// Shows recorded Hermes benchmark runs (demo-data.json, exported by demo_data.py). Nothing is computed here.
(function () {
  var root = document.getElementById("demo");
  if (!root) return;
  var el = function (id) { return document.getElementById(id); };
  var data, q = 0, system = 0;
  var LABEL = { "algebra-agent": "algebra agent", prover: "prover", uniqgen: "UniQGen", "training-free": "training-free" };

  var STEP_LIMIT = 15; // max_steps in the planners' configs: one model call per step
  // What happened, in a sentence, before the raw query or error.
  function explain(r) {
    if (/did not build a query that runs/.test(r.error)) return "No query. The agent used all " + STEP_LIMIT + " steps without building one that runs, so it scores 0.";
    if (r.error) return "The query it wrote would not run, so it scores 0. The engine said:";
    if (r.f === 0 && r.llm_calls >= STEP_LIMIT) return "Used all " + STEP_LIMIT + " steps and ended on a query that returns the wrong rows (F 0). Its query:";
    if (r.f === 1) return "Correct: the same rows as the reference query. Its query:";
    if (r.f === 0) return "Wrong: the rows do not overlap the reference answer (F 0). Its query:";
    return "Partly right: some of the reference rows (F " + r.f + "). Its query:";
  }

  function renderQuestion() {
    var item = data.questions[q], name = data.systems[system], r = item.systems[name];
    Array.prototype.forEach.call(el("tabs").children, function (b, i) { b.setAttribute("aria-selected", i === system ? "true" : "false"); });
    el("sparql").textContent = explain(r) + (r.error ? "\n\n" + r.error : "\n\n" + r.sparql);
    el("scores").innerHTML = "<span>F <b></b></span><span>precision <b></b></span><span>recall <b></b></span><span>LLM calls <b></b></span><span>seconds <b></b></span>";
    var b = el("scores").querySelectorAll("b");
    [r.f, r.precision, r.recall, r.llm_calls, r.seconds].forEach(function (v, i) { b[i].textContent = v; });
  }

  fetch("demo-data.json").then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    d.questions.forEach(function (item, i) {
      var o = document.createElement("option");
      o.value = i; o.textContent = item.question;
      el("question").appendChild(o);
    });
    el("question").onchange = function () { q = +el("question").value; renderQuestion(); };
    d.systems.forEach(function (name, i) {
      var b = document.createElement("button");
      b.className = "tab"; b.setAttribute("role", "tab"); b.textContent = LABEL[name] || name;
      b.onclick = function () { system = i; renderQuestion(); };
      el("tabs").appendChild(b);
    });
    d.board.forEach(function (row) {
      var div = document.createElement("div");
      div.className = "bar" + (row.system === "official" ? " official" : "");
      div.innerHTML = "<span></span><i></i><b></b>";
      div.children[0].textContent = row.run;
      div.children[0].title = row.run + (row.system === "official" ? " (official, from the benchmark)" : "");
      div.children[1].style.setProperty("--w", Math.round(row.f * 100) + "%");
      div.children[2].textContent = row.f.toFixed(2);
      el("board").appendChild(div);
    });
    renderQuestion();
  });
})();
