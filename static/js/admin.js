
// Global Init
let schedules = {};
let timers = {};
let timerCountdowns = {};
let activeCount = 0;
let selectedDays = {};
let robotRunning = false;

// 1. Initialize data structure to avoid undefined errors
for (let i = 1; i <= 10; i++) { selectedDays[i] = []; }

// Day Selection Logic (Global Delegation)
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('day-chip')) {
        const chip = e.target;
        const container = chip.parentElement;
        const boxIdStr = container.id.replace('days-box', '');
        const boxId = parseInt(boxIdStr);
        const day = parseInt(chip.dataset.day);

        // Initialize if missing
        if (!selectedDays[boxId]) selectedDays[boxId] = [];

        if (selectedDays[boxId].includes(day)) {
            selectedDays[boxId] = selectedDays[boxId].filter(d => d !== day);
            chip.classList.remove('active');
        } else {
            selectedDays[boxId].push(day);
            chip.classList.add('active');
        }
    }
});

// Clock
function updateClock() {
    const now = new Date();
    document.getElementById('clock-main').textContent =
        `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
    const days = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
    document.getElementById('date-display').textContent = `${days[now.getDay()]} ${now.getDate()}/${now.getMonth() + 1}/${now.getFullYear()}`;
}
setInterval(updateClock, 1000);
updateClock();

// Logger
function addLog(message) {
    const terminal = document.getElementById('terminal-output');
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="log-time">${timeStr}</span> > ${message}`;
    terminal.appendChild(entry);
    terminal.scrollTop = terminal.scrollHeight;
}

// Status
function setStatus(text, color) {
    document.getElementById('status-text').textContent = text;
    const dot = document.querySelector('.status-dot');
    dot.style.background = color;
    dot.style.boxShadow = `0 0 10px ${color}`;
}

// API Functions

async function openBox(boxId) {
    addLog(`جاري فتح الصندوق ${boxId}...`);
    setStatus('فتح...', 'var(--warning)');
    try {
        const res = await fetch('/open_box', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ box: boxId }) });
        const data = await res.json();

        if (res.ok) {
            addLog(data.status);
            setStatus('نشط', 'var(--success)');

            // تحديث المخزون في الواجهة
            loadSchedules();

            // عرض تحذير إذا كان المخزون منخفضاً
            if (data.warning_message) {
                addLog(`⚠️ ${data.warning_message}`);

                // إظهار تنبيه بصري (يمكن تحسينه بـ SweetAlert أو Modal)
                const confirmBuy = confirm(`${data.warning_message}\nهل تريد شراء الدواء الآن؟`);
                if (confirmBuy && data.pharmacy_url) {
                    window.open(data.pharmacy_url, '_blank');
                }
            }
        } else {
            addLog(`❌ ${data.status}`);
            setStatus('خطأ', 'var(--danger)');
            if (data.error === 'low_stock') {
                alert("⚠️ المخزون نفد! يرجى إعادة التعبئة.");
            }
        }
    } catch (e) { addLog('خطأ في الاتصال'); setStatus('خطأ', 'var(--danger)'); }
}

async function setTimer(boxId) {
    const hours = parseInt(document.getElementById(`box${boxId}-hours`).value);
    const minutes = parseInt(document.getElementById(`box${boxId}-minutes`).value) || 0;
    const medicineName = document.getElementById(`box${boxId}-name`).value;




    const stock = parseInt(document.getElementById(`box${boxId}-stock`).value) || 0;
    const dose = parseInt(document.getElementById(`box${boxId}-dose`).value) || 1;
    const threshold = parseInt(document.getElementById(`box${boxId}-threshold`).value) || 5;
    const pharmacy = document.getElementById(`box${boxId}-pharmacy`).value;

    if (selectedDays[boxId].length === 0) { addLog(`❌ اختر يوماً واحداً على الأقل`); return; }

    schedules[boxId] = { hour: hours, minute: minutes, enabled: true };

    try {
        await fetch('/api/schedules', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                box: boxId,
                hour: hours,
                minute: minutes,
                enabled: true,
                days: selectedDays[boxId],
                medicine_name: medicineName,
                stock_count: stock,
                dose_per_dispense: dose,
                low_stock_threshold: threshold,
                pharmacy_url: pharmacy
            })
        });

        addLog(`✅ تم حفظ جدولة الصندوق ${boxId}`);
        checkStockStatus(boxId); // فحص المخزون بعد الحفظ
        calculateNextSchedule(boxId);
        document.getElementById(`timer-display-${boxId}`).classList.add('active');

        if (timers[boxId]) clearInterval(timers[boxId]);

        // متغير لمنع الاستدعاء المتكرر
        let isDispensing = false;

        timers[boxId] = setInterval(async () => {
            if (timerCountdowns[boxId] > 0 && !isDispensing) {
                timerCountdowns[boxId]--;
                updateTimerDisplay(boxId);

                if (timerCountdowns[boxId] <= 0 && !isDispensing) {
                    // منع الاستدعاء المتكرر
                    isDispensing = true;
                    addLog(`🔔 حان موعد الجرعة للصندوق ${boxId}!`);

                    try {
                        await openBox(boxId);
                    } catch (e) {
                        addLog(`❌ خطأ في فتح الصندوق ${boxId}`);
                    }

                    // انتظار ثم إعادة حساب الموعد التالي
                    setTimeout(() => {
                        calculateNextSchedule(boxId);
                        isDispensing = false;  // إعادة تفعيل المؤقت
                    }, 3000);
                }
            }
        }, 1000);
    } catch (e) { addLog('خطأ في الحفظ'); }
}

function calculateNextSchedule(boxId) {
    const now = new Date();
    const currentDay = now.getDay();
    const targetHour = schedules[boxId].hour;
    const targetMinute = schedules[boxId].minute;

    // إذا لم تكن هناك أيام محددة
    if (!selectedDays[boxId] || selectedDays[boxId].length === 0) {
        timerCountdowns[boxId] = 0;
        updateTimerDisplay(boxId);
        addLog(`⚠️ لا توجد أيام محددة للصندوق ${boxId}`);
        return;
    }

    let nextDate = null;

    // البحث عن الموعد التالي (حتى 8 أيام للأمام)
    for (let i = 0; i <= 7; i++) {
        const checkDay = (currentDay + i) % 7;

        if (selectedDays[boxId].includes(checkDay)) {
            const candidateDate = new Date();
            candidateDate.setDate(candidateDate.getDate() + i);
            candidateDate.setHours(targetHour, targetMinute, 0, 0);

            // إذا كان الموعد في المستقبل
            if (candidateDate > now) {
                nextDate = candidateDate;
                break;
            }
        }
    }

    // إذا لم نجد موعد في الأيام القادمة، نبحث من أول الأسبوع
    if (!nextDate) {
        for (let i = 1; i <= 7; i++) {
            const checkDay = (currentDay + i) % 7;

            if (selectedDays[boxId].includes(checkDay)) {
                nextDate = new Date();
                nextDate.setDate(nextDate.getDate() + i);
                nextDate.setHours(targetHour, targetMinute, 0, 0);
                break;
            }
        }
    }

    if (nextDate) {
        timerCountdowns[boxId] = Math.max(1, Math.floor((nextDate - now) / 1000));
        const days = ['أحد', 'إثنين', 'ثلاثاء', 'أربعاء', 'خميس', 'جمعة', 'سبت'];
        addLog(`⏰ الجرعة التالية للصندوق ${boxId}: يوم ${days[nextDate.getDay()]} الساعة ${String(targetHour).padStart(2, '0')}:${String(targetMinute).padStart(2, '0')}`);
    } else {
        timerCountdowns[boxId] = 0;
        addLog(`⚠️ لم يتم العثور على موعد تالي للصندوق ${boxId}`);
    }

    updateTimerDisplay(boxId);
}

function updateTimerDisplay(boxId) {
    const total = timerCountdowns[boxId];
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = total % 60;
    document.getElementById(`countdown-${boxId}`).textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

async function loadMode() {
    addLog('جاري وضع التحميل...');
    setStatus('تحميل', 'var(--primary)');
    try {
        const res = await fetch('/load_mode', { method: 'POST' });
        const data = await res.json();
        addLog(data.status);
        setStatus('نشط', 'var(--success)');
    } catch (e) { addLog('خطأ'); }
}

async function goZero() {
    addLog('جاري المعايرة...');
    setStatus('معايرة', 'var(--accent)');
    try {
        const res = await fetch('/go_zero', { method: 'POST' });
        const data = await res.json();
        addLog(data.status);
        setStatus('نشط', 'var(--success)');
    } catch (e) { addLog('خطأ'); }
}

function emergencyStop() {
    addLog('🚨 إيقاف طوارئ!');
    setStatus('متوقف', 'var(--danger)');
    fetch('/robot/stop', { method: 'POST' });
}

async function toggleRobot() {
    const btn = document.getElementById('robot-toggle-btn');
    const text = document.getElementById('robot-toggle-text');
    const svg = btn.querySelector('svg');

    if (!robotRunning) {
        try {
            addLog('⏳ جاري تشغيل الروبوت...');
            const res = await fetch('/robot/start', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'started') {
                robotRunning = true;
                addLog('🤖 الروبوت يعمل الآن');
                setStatus('الروبوت يعمل', 'var(--warning)');
                // Update button to show stop
                btn.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                svg.innerHTML = '<rect x="6" y="6" width="12" height="12"></rect>';
                svg.setAttribute('stroke', '#ef4444');
                text.textContent = 'إيقاف الروبوت';
                text.style.color = '#ef4444';
            } else {
                addLog('❌ فشل تشغيل الروبوت: ' + (data.message || 'غير متصل'));
            }
        } catch (e) { addLog('❌ خطأ في الاتصال بالروبوت'); }
    } else {
        try {
            await fetch('/robot/stop', { method: 'POST' });
            robotRunning = false;
            addLog('⏹️ تم إيقاف الروبوت');
            setStatus('نشط', 'var(--success)');
            // Update button to show start
            btn.style.borderColor = 'rgba(16, 185, 129, 0.3)';
            svg.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
            svg.setAttribute('stroke', '#10b981');
            text.textContent = 'تشغيل الروبوت';
            text.style.color = '#10b981';
        } catch (e) { addLog('❌ خطأ في إيقاف الروبوت'); }
    }
}

async function loadSchedules() {
    try {
        const res = await fetch('/api/schedules');
        const data = await res.json();
        let activeCount = 0;

        for (let boxId in data) {
            // Populate data always (even if disabled)
            if (data[boxId].hour !== null) {
                document.getElementById(`box${boxId}-hours`).value = data[boxId].hour;
                document.getElementById(`box${boxId}-minutes`).value = data[boxId].minute || 0;
            }

            document.getElementById(`box${boxId}-name`).value = data[boxId].medicine_name || '';

            // تعبئة بيانات المخزون
            document.getElementById(`box${boxId}-stock`).value = data[boxId].stock_count ?? 0;
            document.getElementById(`box${boxId}-dose`).value = data[boxId].dose_per_dispense ?? 1;
            document.getElementById(`box${boxId}-threshold`).value = data[boxId].low_stock_threshold ?? 5;
            document.getElementById(`box${boxId}-pharmacy`).value = data[boxId].pharmacy_url || 'https://kuludonline.com/';

            // فحص حالة المخزون وتحديث الواجهة دائماً
            checkStockStatus(boxId);

            selectedDays[boxId] = data[boxId].days || [];
            const container = document.getElementById(`days-box${boxId}`);

            // Reset chips first
            container.querySelectorAll('.day-chip').forEach(c => c.classList.remove('active'));

            selectedDays[boxId].forEach(day => {
                const chip = container.querySelector(`[data-day="${day}"]`);
                if (chip) chip.classList.add('active');
            });

            // If enabled, correct the state
            if (data[boxId].enabled && data[boxId].hour !== null) {
                activeCount++;
                schedules[boxId] = { hour: data[boxId].hour, minute: data[boxId].minute, enabled: true };
                calculateNextSchedule(boxId);
                document.getElementById(`timer-display-${boxId}`).classList.add('active');

                // Start timer logic
                if (timers[boxId]) clearInterval(timers[boxId]);

                let isDispensing = false;
                timers[boxId] = setInterval(async () => {
                    if (timerCountdowns[boxId] > 0 && !isDispensing) {
                        timerCountdowns[boxId]--;
                        updateTimerDisplay(boxId);

                        if (timerCountdowns[boxId] <= 0 && !isDispensing) {
                            isDispensing = true;
                            addLog(`🔔 حان موعد الجرعة للصندوق ${boxId}!`);
                            try {
                                await openBox(boxId);
                            } catch (e) {
                                addLog(`❌ خطأ في فتح الصندوق ${boxId}`);
                            }
                            setTimeout(() => {
                                calculateNextSchedule(boxId);
                                isDispensing = false;
                            }, 3000);
                        }
                    }
                }, 1000);
            }
        }

        document.getElementById('active-count').textContent = activeCount;
    } catch (e) { addLog('خطأ في تحميل الجداول'); }
}

// Theme
function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    if (html.getAttribute('data-theme') === 'light') {
        html.removeAttribute('data-theme'); icon.textContent = '🌙'; localStorage.setItem('theme', 'dark');
    } else {
        html.setAttribute('data-theme', 'light'); icon.textContent = '☀️'; localStorage.setItem('theme', 'light');
    }
}

(function () {
    if (localStorage.getItem('theme') === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        document.getElementById('theme-icon').textContent = '☀️';
    }
})();

loadSchedules();
addLog('✅ النظام جاهز');

// Check Arduino connection on startup
async function checkArduinoStatus() {
    try {
        const res = await fetch('/robot/status');
        const data = await res.json();
        if (data.arduino_connected) {
            addLog('🔌 Arduino متصل وجاهز');
        } else {
            addLog('⚠️ Arduino غير متصل - الروبوت لن يتحرك');
        }
    } catch (e) {
        addLog('❌ خطأ في فحص اتصال Arduino');
    }
}
checkArduinoStatus();

// Auto Fullscreen on first interaction
function enterFullscreen() {
    const elem = document.documentElement;
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
    // Remove listener after first use
    document.removeEventListener('click', enterFullscreen);
    document.removeEventListener('touchstart', enterFullscreen);
}

// Check if not already in fullscreen
if (!document.fullscreenElement) {
    document.addEventListener('click', enterFullscreen, { once: true });
    document.addEventListener('touchstart', enterFullscreen, { once: true });
}

// Check Stock Status
function checkStockStatus(boxId) {
    const stock = parseInt(document.getElementById(`box${boxId}-stock`).value) || 0;
    const threshold = parseInt(document.getElementById(`box${boxId}-threshold`).value) || 5;
    const pharmacy = document.getElementById(`box${boxId}-pharmacy`).value;

    const warningEl = document.getElementById(`stock-warning-${boxId}`);
    const linkEl = document.getElementById(`pharmacy-link-${boxId}`);

    if (stock < threshold) {
        warningEl.style.display = 'flex';
        linkEl.href = pharmacy || 'https://kuludonline.com/';

        // إضافة تأثير بصري للصندوق نفسه عندما يكون المخزون منخفضا
        document.getElementById(`box${boxId}-stock`).style.borderColor = 'var(--danger)';
    } else {
        warningEl.style.display = 'none';
        document.getElementById(`box${boxId}-stock`).style.borderColor = 'var(--border-color)';
    }
}

// Add event listeners to input fields to update warning immediately
// Add event listeners to input fields to update warning immediately
document.querySelectorAll('input[type="number"], input[type="text"]').forEach(input => {
    input.addEventListener('change', (e) => {
        const match = e.target.id.match(/box(\d+)-/);
        if (match && (e.target.id.includes('stock') || e.target.id.includes('threshold') || e.target.id.includes('pharmacy'))) {
            checkStockStatus(parseInt(match[1]));
        }
    });

    // Also update on keyup for instant feedback
    input.addEventListener('keyup', (e) => {
        const match = e.target.id.match(/box(\d+)-/);
        if (match && (e.target.id.includes('stock') || e.target.id.includes('threshold'))) {
            checkStockStatus(parseInt(match[1]));
        }
    });
});

// Initialize tooltips/other

// Settings Functions
async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        document.getElementById('auth-toggle').checked = data.auth_enabled;
    } catch (e) {
        addLog("خطأ في تحميل الإعدادات");
    }
}

async function toggleAuthSettings() {
    const enabled = document.getElementById('auth-toggle').checked;
    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auth_enabled: enabled })
        });
        if (enabled) {
            addLog("✅ تم تفعيل نظام الكاميرا");
            setStatus('نظام آمن', 'var(--success)');
        } else {
            addLog("⚠️ تم تعطيل نظام الكاميرا");
            setStatus('نظام سريع', 'var(--warning)');
        }
    } catch (e) {
        addLog("خطأ في حفظ الإعدادات");
        // Revert
        document.getElementById('auth-toggle').checked = !enabled;
    }
}

// Init Settings
loadSettings();
