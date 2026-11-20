
/* ========================================
   CALLIQ AI — MAIN CONTROL MODULE
======================================== */

const analyzeBtn = document.getElementById("analyzeBtn");
const audioInput = document.getElementById("audioInput");
const loading = document.getElementById("loading");
const message = document.getElementById("message");
const fileName = document.getElementById("fileName");
const resultContent = document.getElementById("resultContent");
const historyContent = document.getElementById("historyContent");


// ========================================
// ҚАУІПСІЗ МӘТІН
// ========================================

function escapeHtml(value) {
    return String(value ?? "Нақтылау қажет")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}


function formatTime(seconds) {

    const s = Math.max(
        0,
        Math.floor(Number(seconds) || 0)
    );

    return String(Math.floor(s / 60)).padStart(2, "0")
        + ":" +
        String(s % 60).padStart(2, "0");
}


async function fetchJSON(url, options) {

    const response = await fetch(url, options);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.error || "Сервер қатесі"
        );
    }

    return data;
}


// ========================================
// СТАТИСТИКА
// ========================================

async function loadStats() {

    const calls = await fetchJSON("/api/calls");

    document.getElementById("totalCalls").textContent =
        calls.length;

    document.getElementById("agreements").textContent =
        calls.filter(c =>
            c.agreement &&
            ![
                "Нақтылау қажет",
                "Жоқ",
                "Міндеттеме алынбаған"
            ].includes(c.agreement)
        ).length;

    document.getElementById("waiting").textContent =
        calls.filter(c =>
            String(c.status || "").includes("күтілуде")
        ).length;

    document.getElementById("complaints").textContent =
        calls.filter(c =>
            c.validation?.complaint_signal === true ||
            (
                c.complaint &&
                c.complaint !== "Нақтылау қажет" &&
                c.complaint !== "Шағым айтылмады"
            )
        ).length;
}


// ========================================
// ДИАЛОГТЫ КӨРСЕТУ
// ========================================

function renderDialogue(dialogue) {

    if (!Array.isArray(dialogue) || !dialogue.length) {

        return `
            <p>Сөйлеушілерге бөлінген диалог жоқ.</p>
        `;
    }

    return dialogue.map(turn => {

        const isManager = turn.role === "Менеджер";
        const isCustomer = turn.role === "Клиент";

        const background = isManager
            ? "#e6f4ea"
            : isCustomer
                ? "#e7effc"
                : "#f1f3f5";

        return `
            <div style="
                display:flex;
                justify-content:${isManager ? "flex-end" : "flex-start"};
                margin-bottom:14px;
            ">

                <div style="
                    background:${background};
                    padding:16px;
                    border-radius:12px;
                    max-width:85%;
                ">

                    <strong>
                        ${escapeHtml(turn.role)}
                    </strong>

                    <small>
                        ${formatTime(turn.start)}
                        -
                        ${formatTime(turn.end)}
                    </small>

                    <p style="margin-top:8px;">
                        ${escapeHtml(turn.text)}
                    </p>

                </div>

            </div>
        `;

    }).join("");
}


// ========================================
// AI НӘТИЖЕСІН ТЕКСЕРУ
// ========================================

function renderValidation(validation) {

    validation = validation || {};

    const warnings = Array.isArray(validation.warnings)
        ? validation.warnings
        : [];

    return `
        <div style="
            padding:16px;
            background:#fff7e8;
            border-radius:12px;
            margin-top:20px;
        ">

            <strong>AI нәтижесін тексеру</strong>

            <p>
                Нәтижені жауапты қызметкер тексеруі қажет.
            </p>

            ${
                warnings.length
                    ? warnings.map(w => `
                        <p>• ${escapeHtml(w)}</p>
                    `).join("")
                    : "<p>Қосымша автоматты ескерту жоқ.</p>"
            }

        </div>
    `;
}


// ========================================
// SMART CALL CARD
// ========================================

function showResult(call) {

    if (!call) return;

    resultContent.classList.remove("empty");

    const fields = [

        ["Қоңырау тақырыбы", call.topic],
        ["Қысқаша мазмұны", call.summary],
        ["Клиент сұранысы", call.customer_request],
        ["Бюджет", call.budget],
        ["Келісім және міндеттеме", call.agreement],
        ["Орындау мерзімі", call.deadline],
        ["Мәртебесі", call.status],
        ["Клиент шағымы", call.complaint],
        ["Басшыға белгі", call.flag],
        ["Сөйлеушілер саны", call.speaker_count ?? 0],

        [
            "Өңдеу уақыты",

            call.processing_time != null
                ? call.processing_time + " секунд"
                : "Нақтылау қажет"
        ]
    ];

    resultContent.innerHTML = `

        <div style="
            margin-bottom:20px;
            padding:18px;
            background:#e8f1ff;
            border-radius:12px;
        ">

            <h3>Қоңырау #${escapeHtml(call.id)}</h3>

            <p>${escapeHtml(call.created_at)}</p>

        </div>

        <div style="
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
            gap:14px;
        ">

            ${fields.map(([label, value]) => `

                <div style="
                    background:#f4f7fb;
                    padding:16px;
                    border-radius:12px;
                ">

                    <small>
                        ${escapeHtml(label)}
                    </small>

                    <p style="margin-top:8px;">

                        <strong>
                            ${escapeHtml(value)}
                        </strong>

                    </p>

                </div>

            `).join("")}

        </div>

        ${renderValidation(call.validation)}

        <div style="margin-top:25px;">

            <h3>Қоңырау аудиосы</h3>

            ${
                call.filename
                    ? `
                        <audio
                            controls
                            preload="metadata"
                            style="width:100%;margin-top:12px;"
                            src="/audio/${encodeURIComponent(call.filename)}">
                        </audio>
                    `
                    : "<p>Аудиофайл жоқ.</p>"
            }

        </div>

        <div style="margin-top:25px;">

            <h3>Клиент пен менеджер диалогы</h3>

            <div style="margin-top:16px;">

                ${renderDialogue(call.dialogue)}

            </div>

        </div>

        <details style="margin-top:25px;">

            <summary style="cursor:pointer;">
                Толық транскрипция
            </summary>

            <p style="margin-top:15px;line-height:1.8;">

                ${escapeHtml(call.transcription)}

            </p>

        </details>

    `;

    document.getElementById("result").scrollIntoView({
        behavior: "smooth"
    });
}


// ========================================
// ҚОҢЫРАУЛАР ТАРИХЫ
// ========================================

async function loadHistory() {

    const calls = await fetchJSON("/api/calls");

    if (!calls.length) {

        historyContent.innerHTML =
            "<p>Әзірге қоңыраулар жоқ.</p>";

        return calls;
    }

    historyContent.innerHTML = calls.map(call => `

        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            flex-wrap:wrap;
            gap:15px;
            padding:18px;
            margin-bottom:12px;
            background:#f4f7fb;
            border-radius:12px;
        ">

            <div>

                <strong>
                    #${escapeHtml(call.id)}
                    · ${escapeHtml(call.topic)}
                </strong>

                <p>
                    ${escapeHtml(call.created_at)}
                </p>

                <small>
                    ${escapeHtml(call.status)}
                </small>

            </div>

            <div style="display:flex;gap:10px;">

                <button
                    type="button"
                    onclick="openCall(${Number(call.id)})">

                    Ашу

                </button>

                <button
                    type="button"
                    style="background:#a83232;color:white;"
                    onclick="removeCall(${Number(call.id)})">

                    Жою

                </button>

            </div>

        </div>

    `).join("");

    return calls;
}


// ========================================
// САҚТАЛҒАН КАРТОЧКАНЫ АШУ
// ========================================

async function openCall(id) {

    try {

        const call = await fetchJSON(
            `/api/calls/${id}`
        );

        showResult(call);

    } catch (error) {

        alert(error.message);
    }
}


// ========================================
// ҚОҢЫРАУДЫ ЖОЮ
// ========================================

async function removeCall(id) {

    const confirmed = confirm(
        "Қоңырау мен аудионы жоюды растайсыз ба?"
    );

    if (!confirmed) return;

    try {

        await fetchJSON(`/api/calls/${id}`, {

            method: "DELETE"

        });

        resultContent.classList.add("empty");

        resultContent.textContent =
            "Талдау нәтижесі осы жерде көрсетіледі.";

        await Promise.all([

            loadStats(),
            loadHistory(),
            loadTasks()

        ]);

    } catch (error) {

        alert(error.message);
    }
}


// ========================================
// ДАЙЫН АУДИОФАЙЛДЫ ТАҢДАУ
// ========================================

audioInput.addEventListener("change", () => {

    const file = audioInput.files[0];

    fileName.textContent = file
        ? file.name
        : "";
});


// ========================================
// ДАЙЫН АУДИОФАЙЛДЫ ТАЛДАУ
// ========================================

analyzeBtn.addEventListener("click", async () => {

    const file = audioInput.files[0];

    const consent =
        document.getElementById("consent");

    if (!file) {

        message.textContent =
            "Алдымен аудиофайлды таңдаңыз.";

        return;
    }

    if (!consent.checked) {

        message.textContent =
            "Қатысушылардың келісімін растаңыз.";

        return;
    }

    if (file.size > 25 * 1024 * 1024) {

        message.textContent =
            "Файл көлемі 25 МБ-тан аспауы тиіс.";

        return;
    }

    analyzeBtn.disabled = true;
    consent.disabled = true;
    loading.hidden = false;

    message.textContent = "";

    try {

        const formData = new FormData();

        formData.append("audio", file);
        formData.append("consent", "true");

        const data = await fetchJSON(
            "/api/analyze",
            {
                method: "POST",
                body: formData
            }
        );

        if (!data.call) {

            throw new Error(
                data.error || "Талдау нәтижесі алынбады."
            );
        }

        showResult(data.call);

        audioInput.value = "";
        fileName.textContent = "";
        consent.checked = false;

        message.textContent =
            "Талдау сәтті аяқталды!";

        await Promise.all([

            loadStats(),
            loadHistory(),
            loadTasks()

        ]);

    } catch (error) {

        message.textContent =
            "Қате: " + error.message;

        console.error(error);

    } finally {

        analyzeBtn.disabled = false;
        consent.disabled = false;
        loading.hidden = true;
    }
});


// ========================================
// LIVE AUDIO CAPTURE
// ========================================

(() => {

    const el = id => document.getElementById(id);

    const consent = el("recordConsent");

    if (!consent) return;

    const start = el("startRecord");
    const stop = el("stopRecord");
    const send = el("analyzeRecord");
    const discard = el("deleteRecord");

    const status = el("recordStatus");
    const indicator = el("recordingIndicator");

    const preview = el("recordPreview");
    const player = el("recordedAudio");

    let stream;
    let recorder;
    let context;
    let timer;
    let url;
    let blob;

    let busy = false;
    let cancelled = false;


    // БАТЫРМАЛАРДЫ БАСҚАРУ

    function controls() {

        const active =
            recorder?.state === "recording";

        start.disabled =
            !consent.checked ||
            busy ||
            active ||
            !!blob ||
            analyzeBtn.disabled;

        stop.disabled = !active;

        send.disabled =
            !consent.checked ||
            !blob ||
            busy ||
            active ||
            analyzeBtn.disabled;

        discard.disabled = busy || active;
    }


    // МИКРОФОНДЫ БОСАТУ

    function release() {

        clearInterval(timer);

        stream?.getTracks().forEach(track => {

            track.stop();

        });

        stream = null;

        if (context) {

            context.close().catch(() => {});

            context = null;
        }

        el("audioLevel").value = 0;
    }


    // ЖАЗБАНЫ ТАЗАРТУ

    function clearRecording() {

        player.pause();

        player.removeAttribute("src");

        player.load();

        if (url) {

            URL.revokeObjectURL(url);
        }

        url = null;
        blob = null;

        preview.hidden = true;

        el("recordTimer").textContent = "00:00";

        indicator.textContent =
            "Жазба басталған жоқ";
    }


    // ҚАТЫСУШЫЛАР КЕЛІСІМІ

    consent.addEventListener("change", () => {

        if (!consent.checked) {

            cancelled = true;

            if (recorder?.state === "recording") {

                busy = true;

                recorder.stop();
            }

            release();

            clearRecording();

            status.textContent =
                "Келісім расталмаған. Жазба жойылды.";
        }

        controls();
    });


    // ЖАЗУДЫ БАСТАУ

    start.addEventListener("click", async () => {

        if (
            !consent.checked ||
            busy ||
            blob ||
            analyzeBtn.disabled
        ) return;

        busy = true;
        cancelled = false;

        controls();

        try {

            if (
                !navigator.mediaDevices?.getUserMedia ||
                !window.MediaRecorder
            ) {

                throw new Error(
                    "Браузер микрофонды қолдамайды."
                );
            }

            stream =
                await navigator.mediaDevices.getUserMedia({

                    audio: true

                });

            if (!consent.checked || cancelled) {

                release();

                return;
            }

            const mime = [

                "audio/webm;codecs=opus",
                "audio/webm",
                "audio/ogg;codecs=opus"

            ].find(type =>
                MediaRecorder.isTypeSupported(type)
            );

            if (!mime) {

                throw new Error(
                    "Chrome немесе Edge браузерін қолданыңыз."
                );
            }

            recorder = new MediaRecorder(stream, {

                mimeType: mime

            });

            const chunks = [];

            recorder.ondataavailable = event => {

                if (event.data.size) {

                    chunks.push(event.data);
                }
            };


            // ЖАЗУ КЕЗІНДЕГІ ҚАТЕ

            recorder.onerror = () => {

                cancelled = true;

                release();

                status.textContent =
                    "Аудио жазу кезінде қате шықты.";

                controls();
            };


            // ЖАЗУ АЯҚТАЛҒАНДА

            recorder.onstop = () => {

                release();

                busy = false;

                if (!cancelled && consent.checked) {

                    blob = new Blob(chunks, {

                        type: recorder.mimeType

                    });

                    if (
                        blob.size &&
                        blob.size <= 25 * 1024 * 1024
                    ) {

                        url = URL.createObjectURL(blob);

                        player.src = url;

                        preview.hidden = false;

                        indicator.textContent =
                            "Жазба аяқталды";

                        status.textContent =
                            "Аудионы тыңдап, тексеріңіз.";

                    } else {

                        clearRecording();

                        status.textContent =
                            "Жазба бос немесе 25 МБ-тан үлкен.";
                    }
                }

                controls();
            };


            // ДЫБЫС ДЕҢГЕЙІ

            context = new AudioContext();

            const analyser =
                context.createAnalyser();

            context
                .createMediaStreamSource(stream)
                .connect(analyser);

            const samples =
                new Float32Array(analyser.fftSize);

            recorder.start(250);

            const began = performance.now();

            indicator.textContent =
                "● Жазылып жатыр";

            status.textContent =
                "Микрофон қосулы";


            // ЖАЗБА ТАЙМЕРІ

            timer = setInterval(() => {

                const seconds = Math.floor(
                    (performance.now() - began) / 1000
                );

                const minutes = String(
                    Math.floor(seconds / 60)
                ).padStart(2, "0");

                const secs = String(
                    seconds % 60
                ).padStart(2, "0");

                el("recordTimer").textContent =
                    `${minutes}:${secs}`;

                analyser.getFloatTimeDomainData(
                    samples
                );

                const rms = Math.sqrt(

                    samples.reduce(
                        (sum, value) =>
                            sum + value * value,
                        0
                    ) / samples.length

                );

                el("audioLevel").value =
                    Math.min(100, rms * 300);


                // Демонстрациялық шектеу: 2 минут

                if (
                    seconds >= 120 &&
                    recorder.state === "recording"
                ) {

                    busy = true;

                    recorder.stop();

                    controls();
                }

            }, 100);

        } catch (error) {

            release();

            status.textContent =
                error.message;

        } finally {

            busy = false;

            controls();
        }
    });


    // ЖАЗУДЫ ТОҚТАТУ

    stop.addEventListener("click", () => {

        if (recorder?.state === "recording") {

            busy = true;

            recorder.stop();

            release();

            controls();
        }
    });


    // ЖАЗБАНЫ ЖОЮ

    discard.addEventListener("click", () => {

        clearRecording();

        status.textContent =
            "Жазба жойылды";

        consent.checked = false;

        controls();
    });


    // AI ТАЛДАУҒА ЖІБЕРУ

    send.addEventListener("click", async () => {

        if (
            !blob ||
            !consent.checked ||
            busy ||
            analyzeBtn.disabled
        ) return;

        busy = true;

        analyzeBtn.disabled = true;
        consent.disabled = true;

        controls();

        loading.hidden = false;

        status.textContent =
            "AI аудионы өңдеуде...";

        try {

            const formData = new FormData();

            const filename =
                blob.type.includes("ogg")
                    ? "recording.ogg"
                    : "recording.webm";

            formData.append(
                "audio",
                blob,
                filename
            );

            formData.append(
                "consent",
                "true"
            );

            const data = await fetchJSON(
                "/api/analyze",
                {
                    method: "POST",
                    body: formData
                }
            );

            if (!data.call) {

                throw new Error(
                    data.error || "Талдау қатесі"
                );
            }

            showResult(data.call);

            clearRecording();

            consent.checked = false;

            status.textContent =
                "Талдау сәтті аяқталды!";

            await Promise.all([

                loadStats(),
                loadHistory(),
                loadTasks()

            ]);

        } catch (error) {

            status.textContent =
                error.message;

        } finally {

            busy = false;

            analyzeBtn.disabled = false;
            consent.disabled = false;
            loading.hidden = true;

            controls();
        }
    });


    // БАТЫРМАЛАРДЫ СИНХРОНДАУ

    new MutationObserver(controls).observe(

        analyzeBtn,

        {
            attributes: true,
            attributeFilter: ["disabled"]
        }

    );


    // САЙТ ЖАБЫЛҒАНДА МИКРОФОНДЫ ӨШІРУ

    window.addEventListener("pagehide", () => {

        cancelled = true;

        release();

        if (url) {

            URL.revokeObjectURL(url);
        }
    });

    controls();

})();


// ========================================
// CALLIQ AI — TASK TRACKER
// ========================================

let tasksLoading = false;
let taskActionBusy = false;


async function loadTasks() {

    const container =
        document.getElementById("tasksContent");

    if (!container || tasksLoading) return;

    tasksLoading = true;

    try {

        const tasks = await fetchJSON("/api/tasks");

        if (!Array.isArray(tasks)) {

            throw new Error(
                "Тапсырмалар форматы қате"
            );
        }


        // МІНДЕТТЕМЕЛЕР СТАТИСТИКАСЫ

        document.getElementById("taskReview").textContent =
            tasks.filter(t =>
                t.status === "review"
            ).length;

        document.getElementById("taskPending").textContent =
            tasks.filter(t =>
                t.status === "pending" &&
                t.display_status !== "Мерзімі өтті"
            ).length;

        document.getElementById("taskOverdue").textContent =
            tasks.filter(t =>
                t.display_status === "Мерзімі өтті"
            ).length;

        document.getElementById("taskCompleted").textContent =
            tasks.filter(t =>
                t.status === "completed"
            ).length;


        // ЕНГІЗІЛГЕН МЕРЗІМДЕРДІ САҚТАУ

        const draftDates = {};

        container.querySelectorAll(
            'input[type="datetime-local"]'
        ).forEach(input => {

            draftDates[input.id] = input.value;

        });


        // ТАПСЫРМАЛАР БОС БОЛСА

        if (!tasks.length) {

            container.innerHTML = `

                <div class="task-empty">

                    <h3>
                        Әзірге міндеттемелер жоқ
                    </h3>

                    <p>
                        AI менеджердің нақты уәдесін анықтағанда,
                        тапсырма осы жерде пайда болады.
                    </p>

                </div>
            `;

            return;
        }


        // МІНДЕТТЕМЕ КАРТОЧКАЛАРЫ

        container.innerHTML = tasks.map(task => {

            let statusClass = "task-review";

            if (
                task.display_status === "Мерзімі өтті"
            ) {

                statusClass = "task-overdue";

            } else if (
                task.display_status === "Мерзімі жақындады"
            ) {

                statusClass = "task-urgent";

            } else if (
                task.status === "pending"
            ) {

                statusClass = "task-pending";

            } else if (
                task.status === "completed"
            ) {

                statusClass = "task-completed";
            }

            let actions = "";


            // РАСТАУДЫ ҚАЖЕТ ЕТЕТІН ТАПСЫРМА

            if (task.status === "review") {

                actions = `

                    <div class="task-confirm">

                        <label for="taskDue${Number(task.id)}">
                            Орындау мерзімін растаңыз
                        </label>

                        <input
                            type="datetime-local"
                            id="taskDue${Number(task.id)}">

                        <button
                            type="button"
                            class="task-primary"
                            onclick="confirmTask(${Number(task.id)})">

                            Міндеттемені растау

                        </button>

                    </div>
                `;


            // ОРЫНДАЛЫП ЖАТҚАН ТАПСЫРМА

            } else if (task.status === "pending") {

                actions = `

                    <button
                        type="button"
                        class="task-complete-btn"
                        onclick="completeTask(${Number(task.id)})">

                        ✓ Орындалды

                    </button>
                `;


            // АЯҚТАЛҒАН ТАПСЫРМА

            } else if (task.status === "completed") {

                actions = `

                    <p class="task-success-text">
                        ✓ Міндеттеме орындалды
                    </p>
                `;
            }


            // ТАПСЫРМА ДЕРЕКТЕРІ

            return `

                <article class="task-card">

                    <div class="task-header">

                        <small>

                            TASK #${Number(task.id)}
                            · CALL #${Number(task.call_id)}

                        </small>

                        <span class="task-badge ${statusClass}">

                            ${escapeHtml(task.display_status)}

                        </span>

                    </div>

                    <h3>

                        ${escapeHtml(task.title)}

                    </h3>

                    <div class="task-details">

                        <div>

                            <small>
                                Клиент бюджеті
                            </small>

                            <strong>
                                ${escapeHtml(task.budget)}
                            </strong>

                        </div>

                        <div>

                            <small>
                                Әңгімедегі мерзім
                            </small>

                            <strong>
                                ${escapeHtml(task.original_deadline)}
                            </strong>

                        </div>

                        <div>

                            <small>
                                Расталған мерзім
                            </small>

                            <strong>
                                ${
                                    task.due_at
                                        ? escapeHtml(
                                            task.due_at
                                                .replace("T", " ")
                                                .slice(0, 16)
                                          )
                                        : "Расталмаған"
                                }
                            </strong>

                        </div>

                    </div>

                    ${actions}

                    <button
                        type="button"
                        class="task-open-call"
                        onclick="openCall(${Number(task.call_id)})">

                        Қоңырау карточкасын ашу →

                    </button>

                </article>

            `;

        }).join("");


        // ЕНГІЗІЛГЕН МЕРЗІМДЕРДІ ҚАЙТАРУ

        Object.entries(draftDates).forEach(
            ([id, value]) => {

                const input =
                    document.getElementById(id);

                if (input) {

                    input.value = value;
                }
            }
        );

    } catch (error) {

        container.textContent =
            "Қате: " + error.message;

        console.error(error);

    } finally {

        tasksLoading = false;
    }
}


// ========================================
// МІНДЕТТЕМЕНІ РАСТАУ
// ========================================

async function confirmTask(id) {

    if (taskActionBusy) return;

    const input =
        document.getElementById(`taskDue${id}`);

    if (!input) return;

    const dueAt = input.value;

    if (!dueAt) {

        alert("Орындау мерзімін таңдаңыз");

        return;
    }

    taskActionBusy = true;

    try {

        await fetchJSON(

            `/api/tasks/${id}/confirm`,

            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    due_at: dueAt

                })
            }
        );

        await loadTasks();

    } catch (error) {

        alert(error.message);

    } finally {

        taskActionBusy = false;
    }
}


// ========================================
// МІНДЕТТЕМЕНІ АЯҚТАУ
// ========================================

async function completeTask(id) {

    if (taskActionBusy) return;

    if (!confirm("Міндеттеме орындалды ма?")) {

        return;
    }

    taskActionBusy = true;

    try {

        await fetchJSON(

            `/api/tasks/${id}/complete`,

            {
                method: "POST"
            }
        );

        await loadTasks();

    } catch (error) {

        alert(error.message);

    } finally {

        taskActionBusy = false;
    }
}


// ========================================
// TASK TRACKER АВТОМАТТЫ ЖАҢАРТУ
// ========================================

setInterval(() => {

    const container =
        document.getElementById("tasksContent");

    if (
        !container ||
        taskActionBusy ||
        tasksLoading
    ) return;

    const editing = Array.from(

        container.querySelectorAll(
            'input[type="datetime-local"]'
        )

    ).some(input =>

        input === document.activeElement

    );

    if (!editing) {

        loadTasks();
    }

}, 30000);


// ========================================
// САЙТ АШЫЛҒАНДА ДЕРЕКТЕРДІ ЖҮКТЕУ
// ========================================

async function initializeDashboard() {

    try {

        const results = await Promise.all([

            loadStats(),
            loadHistory(),
            loadTasks()

        ]);

        const calls = results[1];

        console.log(

            "CALLIQ AI іске қосылды:",
            calls.length,
            "қоңырау"

        );

    } catch (error) {

        console.error(error);

        message.textContent =
            "Деректерді жүктеу қатесі: " + error.message;
    }
}

initializeDashboard();
