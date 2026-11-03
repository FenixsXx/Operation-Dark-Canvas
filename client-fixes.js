function updateServerClock(serverNow) {
	const serverTime = Date.parse(serverNow || '');
	if (Number.isFinite(serverTime)) window.serverClockOffsetMs = serverTime - Date.now();
}

function serverNowMs() {
	return Date.now() + (window.serverClockOffsetMs || 0);
}

const originalShowToast = showToast;
showToast = function (message) {
	if (String(message).includes('DEADLINE RAGGIUNTA')) {
		message = 'Tempo scaduto: le bozze verranno valutate così come sono.';
	}
	return originalShowToast(message);
};

const originalGuideClick = guideButton.onclick;
guideButton.onclick = function () {
	originalGuideClick?.();
	const body = document.getElementById('modalBody');
	if (body) {
		body.innerHTML = body.innerHTML.replace(
			'Alla scadenza non si possono più inviare richieste, note o teorie.',
			'Alla scadenza non si possono più inviare richieste, note o teorie; le bozze non consegnate verranno valutate così come sono.',
		);
	}
};

const originalApplyStateData = applyStateData;
applyStateData = function (data) {
	updateServerClock(data?.serverNow);
	return originalApplyStateData(data);
};

let caseCountdownSetupPromise = null;
setupCaseCountdown = async function () {
	if (document.getElementById('caseCountdown')?.dataset.startedAt === window.gameStartedAt) return;
	if (caseCountdownSetupPromise) return caseCountdownSetupPromise;
	caseCountdownSetupPromise = (async () => {
	try {
		let startedAt = window.gameStartedAt;
		let duration = Number(window.gameDurationSeconds || 172800);
		if (!startedAt) {
			const response = await fetch(STATE_ENDPOINT);
			if (!response.ok) throw new Error('Timer non disponibile.');
			const data = await response.json();
			updateServerClock(data.serverNow);
			startedAt = data.gameStartedAt;
			duration = Number(data.gameDurationSeconds || duration);
			window.gameStartedAt = startedAt || null;
			window.gameDurationSeconds = duration;
		}
		if (!startedAt) return;

		const clock = document.getElementById('clock');
		if (!clock) return;
		const startedTime = Date.parse(startedAt);
		if (!Number.isFinite(startedTime)) throw new Error('Timestamp di avvio non valido.');
		let timer = document.getElementById('caseCountdown');
		if (!timer) {
			timer = document.createElement('span');
			timer.id = 'caseCountdown';
			timer.className = 'font-mono text-xs text-amber-300';
			clock.before(timer);
		}
		timer.dataset.startedAt = startedAt;
		const updateCountdown = () => {
			if (!timer.isConnected) {
				clearInterval(window.caseCountdownDisplayTimer);
				window.caseCountdownDisplayTimer = null;
				return;
			}
			const elapsedGameSeconds = Math.max(0, (serverNowMs() - startedTime) / 1000 * GAME_TIME_SCALE);
			const remaining = Math.max(0, duration - elapsedGameSeconds);
			const hours = Math.floor(remaining / 3600);
			const minutes = Math.floor(remaining % 3600 / 60);
			const seconds = Math.floor(remaining % 60);
			timer.textContent = `DEADLINE ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
		};
		updateCountdown();
		if (window.caseCountdownDisplayTimer) clearInterval(window.caseCountdownDisplayTimer);
		window.caseCountdownDisplayTimer = setInterval(updateCountdown, 1000);
	} catch (error) {
		setConnectionStatus(false);
		showToast(error.message || 'Countdown non disponibile.');
	}
	})();
	try {
		await caseCountdownSetupPromise;
	} finally {
		caseCountdownSetupPromise = null;
	}
};

formatRemainingTime = function (startedAt, durationSeconds) {
	if (!startedAt) return 'In attesa dell’avvio del Director';
	const startedTime = Date.parse(startedAt);
	if (Number.isNaN(startedTime)) return 'Timer non disponibile';
	const elapsedGameSeconds = (serverNowMs() - startedTime) / 1000 * GAME_TIME_SCALE;
	const remaining = Math.max(0, Number(durationSeconds || 172800) - elapsedGameSeconds);
	const hours = Math.floor(remaining / 3600);
	const minutes = Math.floor(remaining % 3600 / 60);
	const seconds = Math.floor(remaining % 60);
	return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
};

reveal = function (target) {
	const rule = warrants[target];
	if (!rule) {
		showToast(`Approvato: ${target}`);
		return;
	}
	if (rule[3] === 'INTERVIEW') {
		const person = rule[0].replace(/^Interrogatorio\s*[·-]\s*/, '');
		showToast(`Interrogatorio autorizzato: apri il dossier di ${person}.`);
		return;
	}
	showToast(`Approvato: ${rule[0]}`);
};

const baseOpenApp = securedMasterOpenApp;
openApp = function (app) {
	if (app === 'masterSolution' && currentUser?.[3] !== 'DIRECTOR') {
		showToast('Accesso riservato al Director.');
		return undefined;
	}
	const element = baseOpenApp(app);
	if (!element) return undefined;
	if (app === 'resolution') {
		if (!element.querySelector('#resolutionForm')) openResolution();
		wireResolutionForm();
	}
	if (app === 'directorResolutions') drawDirectorResolutions(element);
	if (mobileViewport.matches && history.state?.app !== app) history.pushState({ app }, '', location.href);
	return element;
};

const originalWireResolutionForm = wireResolutionForm;
wireResolutionForm = function () {
	originalWireResolutionForm();
	const form = document.querySelector('#resolutionForm');
	const field = form?.elements.evidence;
	if (!field || field.tagName === 'TEXTAREA') return;
	const label = field.closest('label');
	if (!label) return;
	label.innerHTML = 'Catena probatoria<textarea class="field min-h-24" name="evidence" required placeholder="Indica le evidence pertinenti e il loro valore."></textarea>';
};

const originalDrawWarrants = drawWarrants;
drawWarrants = function (element) {
	originalDrawWarrants(element);
	const body = element?.querySelector('#body-warrants');
	if (!body) return;
	body.querySelectorAll('div').forEach(div => {
		if (!div.childElementCount && div.textContent.includes('Costo operativo indicativo:')) div.remove();
	});
	const intro = body.querySelector('p');
	if (intro && !intro.nextElementSibling?.classList.contains('evidence-count-note')) {
		const note = document.createElement('div');
		note.className = 'evidence-count-note mb-3 rounded border border-cyan-900 bg-cyan-950/30 p-3 text-xs text-cyan-200';
		note.textContent = 'Ogni richiesta indica il numero di reperti che può rendere disponibili.';
		intro.after(note);
	}
	body.querySelectorAll('#warrantTarget option[value]').forEach(option => {
		const target = option.value;
		const warrant = warrants[target];
		if (!warrant) return;
		option.textContent = warrant[3] === 'INTERVIEW'
			? warrant[0]
			: `${warrant[0]} · ${(evidenceByWarrant[target] || []).length} prove`;
	});
};

drawHistory = function (element) {
	const historyElement = element?.querySelector('#history');
	if (!historyElement) return;
	historyElement.innerHTML = (state.requests || []).map(request => {
		const count = (evidenceByWarrant[request.target] || []).length;
		const detail = request.requestKind === 'INTERVIEW' ? 'Interrogatorio' : `${count} prove`;
		return `<article class="card text-xs"><div class="flex justify-between gap-3"><b>${esc(warrants[request.target]?.[0] || request.target)}</b><span>${esc(request.status)}</span></div><div class="mt-1 text-slate-400">${detail}</div></article>`;
	}).join('') || '<span class="text-slate-500">Nessuna richiesta.</span>';
};

const proofDeliveryStorageKeyOriginal = proofDeliveryStorageKey;
proofDeliveryState = function () {
	return JSON.parse(localStorage.getItem(proofDeliveryStorageKeyOriginal()) || '{"initialDownloaded":false,"approved":[],"pendingEmail":[]}');
};
saveProofDelivery = function (delivery) {
	localStorage.setItem(proofDeliveryStorageKeyOriginal(), JSON.stringify(delivery));
};
decryptEvidencePackage = async function (kind, ids = []) {
	try {
		const response = await fetch('/api/evidence');
		const data = await response.json().catch(() => ({}));
		if (!response.ok) throw new Error(data.error || 'Pacchetto prove non disponibile.');
		const allowed = data.evidence || [];
		const selected = kind === 'initial'
			? allowed
			: allowed.filter(item => ids.includes(item.id));
		if (!selected.length) throw new Error('Nessuna evidence autorizzata nel pacchetto richiesto.');
		const packageData = {
			case: '447-GN',
			exportedAt: data.serverNow || new Date(serverNowMs()).toISOString(),
			evidence: selected,
		};
		const blob = new Blob([JSON.stringify(packageData, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const anchor = document.createElement('a');
		anchor.href = url;
		anchor.download = kind === 'initial' ? '447-GN-pacchetto-prove.json' : `447-GN-${ids.join('-')}.json`;
		document.body.append(anchor);
		anchor.click();
		anchor.remove();
		setTimeout(() => URL.revokeObjectURL(url), 1000);

		const delivery = proofDeliveryState();
		if (kind === 'initial') delivery.initialDownloaded = true;
		selected.forEach(item => {
			if (!delivery.approved.includes(item.id)) delivery.approved.push(item.id);
			delivery.pendingEmail = delivery.pendingEmail.filter(id => id !== item.id);
		});
		saveProofDelivery(delivery);
		if (windows.get('briefing')) drawBriefing(windows.get('briefing'));
		if (windows.get('proof')) drawProof(windows.get('proof'));
		showToast(`Pacchetto prove scaricato (${selected.length} reperti).`);
	} catch (error) {
		showToast(error.message || 'Download del pacchetto prove non riuscito.');
	}
};

let boardRenderDepth = 0;
let boardNeedsRedraw = false;
function boardHintsReadKey() {
	const savedSession = JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
	return `dark_canvas_seen_hints_${currentUser?.[2] || 'anonymous'}_${savedSession?.version || 'pending'}`;
}
function seenBoardHintIds() {
	return new Set(JSON.parse(localStorage.getItem(boardHintsReadKey()) || '[]'));
}
function updateBoardHintBadge() {
	const seen = seenBoardHintIds();
	const unread = currentUser?.[3] === 'DIRECTOR'
		? 0
		: (sharedCaseData.hints || []).filter(hint => !seen.has(String(hint.id))).length;
	document.querySelectorAll('[data-open="board"]').forEach(button => {
		button.querySelector('.hintBadge')?.remove();
		if (unread) button.insertAdjacentHTML('beforeend', `<span class="hintBadge ml-1 rounded bg-amber-400 px-1.5 py-0.5 text-[10px] text-slate-950">${unread}</span>`);
	});
}
function markBoardHintsRead() {
	const seen = seenBoardHintIds();
	(sharedCaseData.hints || []).forEach(hint => seen.add(String(hint.id)));
	localStorage.setItem(boardHintsReadKey(), JSON.stringify([...seen]));
	updateBoardHintBadge();
}
function boardInputIsActive(element) {
	const active = document.activeElement;
	return Boolean(element?.querySelector('#boardForm')?.contains(active)
		&& active.matches('input, textarea, select, [contenteditable="true"]'));
}

const originalReadSharedCaseData = readSharedCaseData;
readSharedCaseData = async function () {
	const before = JSON.stringify(sharedCaseData);
	const previousHintIds = new Set((sharedCaseData.hints || []).map(hint => String(hint.id)));
	await originalReadSharedCaseData();
	const after = JSON.stringify(sharedCaseData);
	const hints = sharedCaseData.hints || [];
	const newHints = hints.filter(hint => hint.id != null && !previousHintIds.has(String(hint.id)));
	if (currentUser?.[3] !== 'DIRECTOR') {
		const seen = seenBoardHintIds();
		const unreadNewHints = newHints.filter(hint => !seen.has(String(hint.id)));
		if (unreadNewHints.length) {
			const hint = unreadNewHints[unreadNewHints.length - 1];
			showToast(`Nuovo hint privato da ${hint.actorName}: ${hint.text}`);
		}
	}
	updateBoardHintBadge();
	if (before !== after) {
		const board = windows.get('board');
		if (board && !board.classList.contains('hidden') && boardRenderDepth === 0) {
			if (boardInputIsActive(board)) boardNeedsRedraw = true;
			else {
				boardNeedsRedraw = false;
				void drawBoard(board).catch(error => {
					setConnectionStatus(false);
					showToast(error.message || 'Aggiornamento bacheca non riuscito.');
				});
			}
		}
	} else if (boardNeedsRedraw) {
		const board = windows.get('board');
		if (board && !board.classList.contains('hidden') && !boardInputIsActive(board)) {
			boardNeedsRedraw = false;
			void drawBoard(board).catch(error => {
				setConnectionStatus(false);
				showToast(error.message || 'Aggiornamento bacheca non riuscito.');
			});
		}
	}
};

const originalDrawBoard = drawBoard;
drawBoard = async function (element) {
	boardRenderDepth += 1;
	try {
		await originalDrawBoard(element);
		markBoardHintsRead();
	} finally {
		boardRenderDepth -= 1;
	}
};

const originalDrawProfiles = drawProfiles;
function grecoIsUnlocked() {
	return currentUser?.[3] === 'DIRECTOR'
		|| (state.approved || []).includes('rinaldiGym')
		|| (state.foundEvidence || []).includes('EV-29');
}
drawProfiles = function (element) {
	originalDrawProfiles(element);
	if (grecoIsUnlocked()) return;
	const body = element?.querySelector('#body-records');
	const input = body?.querySelector('#profileSearch');
	const output = body?.querySelector('#profileResults');
	if (!input || !output) return;
	const filterGreco = () => {
		output.querySelector('[data-profile="Luca Greco"]')?.closest('article')?.remove();
		if (input.value.trim() && !output.children.length) {
			output.innerHTML = '<div class="py-8 text-center text-sm text-slate-500">Nessun profilo trovato.</div>';
		}
	};
	const previousInput = input.oninput;
	input.oninput = event => {
		previousInput?.call(input, event);
		filterGreco();
	};
};

const originalOpenDossierFinal = openDossier;
openDossier = async function (name) {
	if (name === 'Luca Greco' && !grecoIsUnlocked()) return;
	const allowedInterviews = new Set(['Matteo Rinaldi', 'Priya Sharma', 'Isabella Cross', 'Kyle Brennan']);
	if (allowedInterviews.has(name)) return originalOpenDossierFinal(name);

	const profile = profiles.find(item => item.name === name);
	const details = dossierDetails[name] || [];
	const modal = document.getElementById('modal');
	const body = document.getElementById('modalBody');
	modal.classList.add('forensic-modal', 'flex');
	modal.classList.remove('hidden');
	document.getElementById('modalTitle').textContent = `NCIC PERSON RECORD // ${name}`;
	body.innerHTML = `<div class="forensic-paper"><button class="forensic-close" aria-label="Chiudi documento">×</button><div class="forensic-head"><strong>FEDERAL BUREAU OF INVESTIGATION</strong><span>NCIC / VICAP DATABASE SYSTEM</span><span>PERSON OF INTEREST RECORD · CASE 447-GN</span></div><h1>${esc(name)}</h1><div class="forensic-meta"><div><b>STATUS</b><br>${esc(profile?.status || 'DA VERIFICARE')}</div><div><b>OCCUPAZIONE</b><br>${esc(details[6] || 'N/D')}</div><div><b>INDIRIZZO</b><br>${esc(details[5] || 'N/D')}</div><div><b>ETÀ</b><br>${esc(details[0] || 'N/D')}</div></div><h2>VALUTAZIONE INVESTIGATIVA</h2><p>${esc(details[7] || 'Nessun dato disponibile')}</p><div class="forensic-sign">Analista responsabile<br><b>FBI Records Division</b></div></div>`;
	body.querySelector('.forensic-close').onclick = () => {
		modal.classList.add('hidden');
		modal.classList.remove('flex', 'forensic-modal');
	};
};

const originalDirectorDashboard = directorDashboard;
directorDashboard = function () {
	const existingDashboard = document.getElementById('directorDashboard');
	const hintForm = existingDashboard?.querySelector('#hintForm');
	const focused = document.activeElement;
	const isEditingHint = hintForm?.contains(focused)
		&& focused.matches('input, textarea, select, [contenteditable="true"]');
	if (isEditingHint) {
		existingDashboard.dataset.refreshPending = 'true';
		return;
	}
	const selectedIds = new Set([...(existingDashboard?.querySelectorAll('.mandate-check:checked') || [])].map(input => input.value));
	originalDirectorDashboard();
	const dashboard = document.getElementById('directorDashboard');
	if (!dashboard) return;
	selectedIds.forEach(id => {
		const checkbox = [...dashboard.querySelectorAll('.mandate-check')].find(input => input.value === id);
		if (checkbox) checkbox.checked = true;
	});
	const selectButton = dashboard.querySelector('#approveSelected');
	if (selectButton && !dashboard.querySelector('#selectAllMandates')) {
		const label = document.createElement('label');
		label.className = 'mr-2 inline-flex items-center gap-2 text-xs text-slate-300';
		label.innerHTML = '<input id="selectAllMandates" type="checkbox"> Seleziona tutti';
		selectButton.before(label);
		label.querySelector('input').onchange = event => {
			dashboard.querySelectorAll('.mandate-check').forEach(input => { input.checked = event.target.checked; });
		};
	}
	const form = dashboard.querySelector('#hintForm');
	if (form && !form.querySelector('#directorHintTemplate')) {
		const template = document.createElement('select');
		template.id = 'directorHintTemplate';
		template.className = 'field';
		template.innerHTML = '<option value="">Seleziona un hint...</option><option value="autopsyLight">Autopsia · leggero</option><option value="autopsyMedium">Autopsia · intermedio</option><option value="autopsyStrong">Autopsia · forte</option>';
		form.querySelector('#hintText')?.before(template);
		template.onchange = () => {
			const hint = DIRECTOR_HINTS[template.value];
			if (hint) form.querySelector('#hintText').value = hint.text;
		};
	}
	if (!dashboard.dataset.refreshHandler) {
		dashboard.dataset.refreshHandler = 'true';
		dashboard.addEventListener('focusout', () => {
			setTimeout(() => {
				if (dashboard.dataset.refreshPending === 'true'
					&& !dashboard.querySelector('#hintForm')?.contains(document.activeElement)) {
					delete dashboard.dataset.refreshPending;
					directorDashboard();
				}
			}, 0);
		});
	}
	if (window.directorTimerInterval) clearInterval(window.directorTimerInterval);
	window.directorTimerInterval = setInterval(() => {
		const timer = document.getElementById('directorTimer');
		if (!timer) return;
		timer.textContent = formatRemainingTime(window.gameStartedAt, window.gameDurationSeconds);
		if (timer.textContent === '00:00:00') {
			clearInterval(window.directorTimerInterval);
			window.directorTimerInterval = null;
		}
	}, 1000);
};

if (typeof autopsyAccessibilityObserver !== 'undefined') autopsyAccessibilityObserver.disconnect();
if (typeof autopsyAgentViewObserver !== 'undefined') autopsyAgentViewObserver.disconnect();
function labelAutopsyTabs() {
	document.querySelectorAll('#body-autopsy [role="tabpanel"]').forEach(panel => {
		const tab = document.querySelector(`#${panel.id.replace('autopsy-panel-', 'autopsy-tab-')}`);
		if (tab) panel.setAttribute('aria-labelledby', tab.id);
	});
}
const originalDrawForensicAutopsy = drawForensicAutopsy;
drawForensicAutopsy = function (element) {
	originalDrawForensicAutopsy(element);
	labelAutopsyTabs();
};

const originalBallisticRenderer = renderBallisticReport;
renderBallisticReport = function (item) {
	let report = originalBallisticRenderer(item);
	if (item[0] !== 'EV-03') return report;
	report = report.replace(
		/<h2>RILIEVI MEDICO-LEGALI CORRELATI<\/h2>[\s\S]*?(?=<div class="forensic-page"><div class="forensic-page-marker">PAGINA 2 \/ 3)/,
		'</div>',
	);
	report = report.replace(
		/(<td>Punto di ingresso<\/td><td>Tempia sinistra<\/td><td>)Finestra temporale autoptica(?=<\/td>)/,
		'$1Rilievo medico-legale',
	);
	report = report.replace(
		/(<td>Punto di uscita<\/td><td>Regione parietale destra<\/td><td>)Finestra temporale autoptica(?=<\/td>)/,
		'$1Rilievo medico-legale',
	);
	return report;
};

updateBoardHintBadge();
