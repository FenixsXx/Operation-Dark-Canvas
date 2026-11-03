async function showHostAddress() {
	try {
		const joinUrl = await window.pywebview.api.get_join_url();
		if (!joinUrl) return;

		const banner = document.createElement('aside');
		banner.style.cssText = 'position:fixed;z-index:1100;top:8px;right:10px;display:flex;align-items:center;gap:8px;max-width:calc(100vw - 20px);padding:8px 10px;border:1px solid #3c5974;border-radius:7px;background:#101b2bf5;color:#dce8f4;font:12px system-ui,sans-serif;box-shadow:0 4px 18px #0008';
		const label = document.createElement('span');
		label.textContent = 'Giocatori sulla stessa rete:';
		const link = document.createElement('a');
		link.href = joinUrl;
		link.textContent = joinUrl;
		link.style.cssText = 'color:#8de8ff;text-decoration:underline';
		link.title = 'Apri l’indirizzo della partita';
		const copyButton = document.createElement('button');
		copyButton.type = 'button';
		copyButton.textContent = 'Copia';
		copyButton.style.cssText = 'padding:4px 8px;border:1px solid #405674;border-radius:5px;background:#142237;color:#dce8f4;cursor:pointer';
		copyButton.addEventListener('click', async () => {
			try {
				await navigator.clipboard.writeText(joinUrl);
				copyButton.textContent = 'Copiato';
			} catch (error) {
				copyButton.textContent = 'Seleziona il link';
			}
		});
		banner.append(label, link, copyButton);
		document.body.append(banner);
	} catch (error) {
		console.error('Impossibile mostrare l’indirizzo LAN:', error);
	}
}

if (window.pywebview?.api) {
	showHostAddress();
} else {
	window.addEventListener('pywebviewready', showHostAddress, { once: true });
}
