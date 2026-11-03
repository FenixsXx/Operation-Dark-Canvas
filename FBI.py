from weasyprint import HTML

# Il tuo codice HTML completo del dossier 447-GN
html_content = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>DOSSIER OPERATIVO 447-GN — OPERAZIONE MAREGGIATA</title>
<style>
  @page { size: A4; margin: 2cm; }
  * { box-sizing: border-box; }
  body { font-family: "Times New Roman", Times, serif; font-size: 11pt; line-height: 1.45; color: #000; background: #fff; margin: 0; padding: 0; }
  .page { width: 210mm; min-height: 297mm; padding: 20mm; margin: 0 auto; background: #fff; position: relative; }
  .fbi-banner { background: #0f0f0f; color: #fff; text-align: center; padding: 14px 8px; font-family: Arial, Helvetica, sans-serif; letter-spacing: 2px; border-bottom: 4px solid #b22222; }
  .fbi-banner h1 { margin: 0; font-size: 18pt; font-weight: 900; text-transform: uppercase; }
  .fbi-banner h2 { margin: 4px 0 0 0; font-size: 10pt; font-weight: 400; text-transform: uppercase; letter-spacing: 1px; }
  .classification { background: #b22222; color: #fff; text-align: center; font-family: Arial, sans-serif; font-size: 10pt; font-weight: bold; padding: 6px; letter-spacing: 1px; text-transform: uppercase; }
  .doc-meta { font-family: "Courier New", Courier, monospace; font-size: 9pt; margin: 12px 0; padding: 8px; border: 1px solid #000; background: #f5f5f5; }
  .doc-meta table { width: 100%; border-collapse: collapse; }
  .doc-meta td { padding: 2px 6px; border: none; font-family: "Courier New", monospace; font-size: 9pt; }
  .section { margin-top: 24px; }
  .section-title { font-family: Arial, sans-serif; font-size: 14pt; font-weight: bold; text-transform: uppercase; border-bottom: 3px solid #000; padding-bottom: 4px; margin-bottom: 12px; letter-spacing: 0.5px; }
  .sub-section { font-family: Arial, sans-serif; font-size: 12pt; font-weight: bold; text-transform: uppercase; border-bottom: 2px solid #333; padding-bottom: 3px; margin-top: 18px; margin-bottom: 10px; }
  .sub-sub { font-family: Arial, sans-serif; font-size: 11pt; font-weight: bold; margin-top: 14px; margin-bottom: 6px; text-transform: uppercase; }
  p { margin: 6px 0; text-align: justify; }
  table.data-table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 9.5pt; }
  table.data-table th { background: #d9d9d9; border: 1.5px solid #000; padding: 5px 6px; text-align: left; font-family: Arial, sans-serif; font-size: 8.5pt; text-transform: uppercase; font-weight: bold; }
  table.data-table td { border: 1px solid #000; padding: 5px 6px; vertical-align: top; font-family: "Courier New", monospace; }
  table.data-table td:first-child { font-weight: bold; background: #f0f0f0; }
  .evidence-box { border: 2px solid #000; padding: 10px; margin: 12px 0; background: #fafafa; }
  .evidence-label { font-family: Arial, sans-serif; font-size: 9pt; font-weight: bold; text-transform: uppercase; background: #000; color: #fff; display: inline-block; padding: 2px 8px; margin-bottom: 6px; }
  .cover { text-align: center; padding-top: 100px; }
  .cover h1 { font-family: Arial, sans-serif; font-size: 26pt; border: none; margin-bottom: 10px; }
  .cover-box { border: 3px solid #000; padding: 30px 40px; display: inline-block; margin: 20px auto; text-align: left; }
  .cover-box td { font-family: "Courier New", monospace; font-size: 11pt; padding: 4px 8px; border: none; }
  .cover-box td:first-child { font-weight: bold; text-align: right; }
  ul.compact { margin: 4px 0; padding-left: 20px; }
  ul.compact li { margin-bottom: 3px; }
</style>
<base target="_blank">
</head>
<body>
<div class="page">

<div class="cover">
<div class="fbi-banner" style="margin-bottom:40px;">
<h1>Federal Bureau of Investigation</h1>
<h2>Divisione Investigativa — Reati contro la Persona<br>Unità Liaison Internazionale, Sede di Roma</h2>
</div>
<div class="classification" style="margin:0 auto 30px auto; width:80%;">CLASSIFICAZIONE: RISERVATO — USO UFFICIALE</div>
<div class="cover-box">
<table>
<tr><td>CASO N.:</td><td>447-GN</td></tr>
<tr><td>OPERAZIONE:</td><td>MAREGGIATA</td></tr>
<tr><td>TIPOLOGIA:</td><td>OMICIDIO PREMEDITATO / STAGING POST-MORTEM</td></tr>
<tr><td>VITTIMA:</td><td>Nathaniel Cross, M, 48 anni, cittadino USA</td></tr>
<tr><td>LUOGO:</td><td>Palazzo Doria, Salita Santa Caterina 14, Genova — Sala Blu</td></tr>
<tr><td>DATA FATTO:</td><td>3 ottobre 2026, ore 23:00 (±15 min)</td></tr>
<tr><td>DATA DOSSIER:</td><td>6 ottobre 2026</td></tr>
<tr><td>AGENTI:</td><td>J. Carver (8847) — M. Vance (8851)</td></tr>
<tr><td>PM:</td><td>Dott. Federico Damiani, Tribunale di Genova</td></tr>
</table>
</div>
<h1 style="font-size:22pt; margin-top:30px; border:none;">DOSSIER OPERATIVO COMPLETO</h1>
<p style="font-family:Arial,sans-serif; font-size:10pt; margin-top:20px;">
Il presente dossier integra rapporti di sopralluogo, referti medico-legali,<br>
analisi criminalistiche, tracciati telematici, interrogatori FD-302 e prove digitali.<br>
Tutti i reperti sono catalogati con fascette 447-SE-01 ÷ 447-SE-22.
</p>
</div>

</div><div class="page">
<div class="classification">RISERVATO — USO UFFICIALE — 447-GN</div>
<div class="doc-meta">
<table>
<tr><td><strong>DOCUMENTO:</strong> DOSSIER INTEGRATO 447-GN</td><td><strong>BATES:</strong> 447-GN-DOSS-001</td></tr>
<tr><td><strong>REDATTO DA:</strong> Agente Speciale J. Carver (8847)</td><td><strong>DATA:</strong> 6 ottobre 2026</td></tr>
<tr><td><strong>VERIFICATO DA:</strong> Agente Speciale M. Vance (8851)</td><td><strong>PAGINA:</strong> 1 di 12</td></tr>
</table>
</div>

<div class="section">
<div class="section-title">Sezione I — Sintesi Operativa e Quadro Indiziario</div>

<div class="sub-section">1.1 Riassunto del Fatto</div>
<p>
Nella serata del <strong>3 ottobre 2026</strong>, nel corso di un'allerta rossa mareggiata sul Golfo di Genova, il Prof. <strong>Nathaniel Cross</strong> (48 anni, coordinatore scientifico del progetto NATO Nettuno) è stato ucciso con un colpo di arma da fuoco alla tempia sinistra all'interno della <em>Sala Blu</em>, safe room situata al terzo piano di Palazzo Doria (Salita Santa Caterina 14, Genova). Il decesso è avvenuto alle ore <strong>23:00 ± 15 minuti</strong>.
</p>
<p>
La scena è stata sottoposta a <strong>staging post-mortem</strong> finalizzato a simulare un suicidio: il cadavere è stato riposizionato in posizione semiseduta/prona sulla scrivania, l'arma (Glock 19 matr. GNN447US) è stata collocata nella mano destra della vittima, ed è stata redatta una lettera digitale di natura autolesionistica sul tablet personale della vittima. L'ipotesi suicidiaria è stata <strong>esclusa in modo inequivocabile</strong> sulla base dei seguenti elementi:
</p>
<ul class="compact">
<li><strong>Discordanza dell'ipostasi:</strong> livor mortis fissato in posizione dorsale (supina), incompatibile con il ritrovamento in posizione prona sulla scrivania;</li>
<li><strong>Bruciatura da contatto palmare anomala</strong> sulla mano destra, incompatibile con una presa naturale di autoinflizione;</li>
<li><strong>Assenza di GSR</strong> (residui da sparo) su entrambe le mani della vittima;</li>
<li><strong>Traiettoria balistica destra-sinistra</strong> con inclinazione discendente, biomeccanicamente incompatibile con autoinflizione da parte di un soggetto destrimane;</li>
<li><strong>Presenza di DNA salivare estraneo</strong> (Matteo Rinaldi) sul bordo interno di un bicchiere in cristallo;</li>
<li><strong>Via di accesso clandestina</strong> attraverso il condotto di ventilazione secondario, con fibra tessile (EV-04) e impronta di suola (EV-05) riconducibili a Matteo Rinaldi.</li>
</ul>

<div class="sub-section">1.2 Soggetti Coinvolti e Qualificazione</div>
<table class="data-table">
<tr><th style="width:18%">Soggetto</th><th style="width:20%">Ruolo Presunto</th><th>Valutazione Investigativa</th></tr>
<tr>
<td>MATTEO RINALDI</td>
<td>INDAGATO / PRESUNTO OMICIDA</td>
<td>
Ingegnere elettronico senior, progetto Nettuno. Figlio naturale non riconosciuto della vittima. Movente: vendetta per paternità negata + annientamento della figura paterna prima del riconoscimento testamentario (EV-08). Alibi palestra/metropolitana smontato da scontrino parcheggio (EV-06), video prestanome, DNA su bicchiere (EV-01), fibra cappotto (EV-04), impronta suola (EV-05), layout tastiera IT-IT, citazione Dante dalla sua bio Instagram. Mancino; traiettoria destra-sinistra compatibile.
</td>
</tr>
<tr>
<td>PRIYA SHARMA</td>
<td>SOGGETTO BETA / SLEEPER AGENT SVR</td>
<td>
Analista FBI liaison infiltrata. Movente: protezione della rete di ricatto fotografico (relazione Cross-Brennan) e recupero del tablet prima che le autorità acquisissero il materiale. Tentativo di accesso con badge clonato alle 23:45 (log NVR). Alterazione log NVR alle 01:05 da IP camera 322 Grand Hotel Savoia. Messaggio cifrato alle 20:30 a handler russo (San Pietroburgo). Rinuncia anomala all'avvocato. Non accusata di omicidio.
</td>
</tr>
<tr>
<td>ISABELLA CROSS</td>
<td>SOGGETTO GAMMA / OCCULTATRICE</td>
<td>
Moglie della vittima. Relazione extraconiugale con Kyle Brennan. Movente non omicidiario ma occultativo: temeva la scoperta del tradimento. Ha trovato il corpo alle 22:10 ma non ha chiamato il 112. Ha omesso la verità per ~2h 45min, rifugiandosi presso Brennan. Alibi teatrale parzialmente confermato (ingresso D4) ma posto vuoto durante il secondo atto.
</td>
</tr>
<tr>
<td>KYLE BRENNAN</td>
<td>TESTIMONE / AMANTE</td>
<td>
Marine statunitense, addetto sicurezza progetto Nettuno. Ha scoperto il corpo alle 00:45 su chiamata di Isabella (22:12). Ritardo psicomotorio per abuso di alcol; chiamata 112 alle 01:23. Non indagato per omicidio.
</td>
</tr>
</table>
</div>

</div><div class="page">
<div class="classification">RISERVATO — USO UFFICIALE — 447-GN</div>
<div class="doc-meta">
<table>
<tr><td><strong>DOCUMENTO:</strong> DOSSIER INTEGRATO 447-GN</td><td><strong>BATES:</strong> 447-GN-DOSS-002</td></tr>
<tr><td><strong>REDATTO DA:</strong> Agente Speciale J. Carver (8847)</td><td><strong>DATA:</strong> 6 ottobre 2026</td></tr>
<tr><td><strong>VERIFICATO DA:</strong> Agente Speciale M. Vance (8851)</td><td><strong>PAGINA:</strong> 2 di 12</td></tr>
</table>
</div>

<div class="section">
<div class="section-title">Sezione II — Timeline Cronologica Integrata (3 ottobre 2026)</div>
<p style="font-size:9pt; font-family:Arial,sans-serif; margin-bottom:10px;">
Fonti: tabulati telefonici, log NVR (backup cloud), GPS veicolo GE-AB-447, scontrini, testimonianze, referto autoptico, analisi forense.
</p>
<table class="data-table">
<tr><th style="width:8%">ORA</th><th style="width:46%">AZIONI / SPOSTAMENTI SOGGETTI</th><th style="width:46%">EVENTI OGGETTIVI / RISCONTRI</th></tr>
<tr><td>19:45</td><td>—</td><td>Allerta rossa mareggiata sul Golfo di Genova; isolamento centro storico.</td></tr>
<tr><td>20:15</td><td>Isabella esce da Palazzo Doria direzione Teatro Carlo Felice (cappotto cammello, biglietto D4).</td><td>Ascensore registra discesa dal terzo piano. Portiere conferma orario.</td></tr>
<tr><td>20:30</td><td>Priya Sharma (Grand Hotel Savoia) invia messaggio cifrato a handler russo.</td><td>Dump forense: ordine di recupero tablet entro le 24:00 per eliminare materiale di ricatto.</td></tr>
<tr><td>20:45</td><td>Rinaldi lascia appartamento via Cecchi (jeans, Timberland 44, cappotto loden nero). Ha con sé Glock 19.</td><td>Video condominio rileva uscita. Telefono Rinaldi SPENTO/OFFLINE da qui in poi.</td></tr>
<tr><td>21:00</td><td>Isabella occupa posto palco D4; smartphone in modalità aereo.</td><td>Inizio spettacolo Teatro Carlo Felice.</td></tr>
<tr><td>21:15</td><td>Isabella abbandona palco durante intervallo.</td><td>Posto D4 vuoto al controllo biglietti secondo atto. <strong>INIZIO BUCO TEMPORALE ALIBI.</strong></td></tr>
<tr><td>21:30</td><td>Rinaldi parcheggia al Marina Park.</td><td>Scontrino EV-06 timbrato 22:15:07 (pagamento 4 ore). Nessuna transazione ATM o metropolitana.</td></tr>
<tr><td>21:45</td><td>Isabella avvistata dal barista mentre sale su taxi direzione Castelletto.</td><td>Tassista conferma consegna all'ingresso di Salita Santa Caterina.</td></tr>
<tr><td>22:10</td><td>Isabella entra in Palazzo Doria (scale interne, nessuna chiamata ascensore). Trova il corpo del marito. <strong>NON CHIAMA IL 112.</strong></td><td>—</td></tr>
<tr><td>22:12</td><td>Isabella chiama Kyle Brennan da numero anonimo (45 sec).</td><td>Tabulato telefonico: chiamata in uscita verso +393204478812.</td></tr>
<tr><td>22:15</td><td>Rinaldi raggiunge Palazzo Doria dal vicolo laterale; entra tramite condotto ventilazione secondario (griglia forzata dall'interno).</td><td>—</td></tr>
<tr><td>22:25</td><td>Isabella esce da Palazzo Doria e raggiunge a piedi l'abitazione di Brennan in via del Campo.</td><td>Smartphone aggancia cella Via del Campo (permanenza fino alle 23:58).</td></tr>
<tr><td>22:30</td><td>Rinaldi entra nella Sala Blu. Cross è solo, in stato di elevata agitazione.</td><td>—</td></tr>
<tr><td>22:45</td><td>Confronto verbale Rinaldi-Cross.</td><td>Bozza email al notaio (testamento/riconoscimento paternità) visibile sul monitor terminale fisso.</td></tr>
<tr><td>23:00</td><td><strong>Rinaldi impugna Glock 19 con MANO SINISTRA e spara un colpo singolo alla tempia sinistra di Cross.</strong></td><td>Traiettoria destra-sinistra, angolazione discendente 15°. Proiettile 9×19mm si confica nel pannello acustico parete nord.</td></tr>
<tr><td>23:05</td><td>Rinaldi posiziona l'arma nella mano destra di Cross (simulazione post-mortem).</td><td>Bruciatura da contatto sul palmo destro anomala; assenza GSR sui polpastrelli vittima.</td></tr>
<tr><td>23:15</td><td>Rinaldi accede al tablet (già sbloccato). Cancella cronologia test paternità; redige lettera di suicidio digitale.</td><td>Layout tastiera IT-IT; citazione Dante («Lasciate ogne speranza») dalla bio Instagram di Rinaldi.</td></tr>
<tr><td>23:30</td><td>Rinaldi versa whisky e beve un sorso dal bicchiere di Cross.</td><td>Deposito DNA salivare (EV-01) sovrapposto alle impronte della vittima.</td></tr>
<tr><td>23:45</td><td>Priya Sharma si presenta al portone di Palazzo Doria.</td><td>Tentativo accesso Sala Blu con <strong>BADGE CLONATO</strong> fallito (sistema in blocco totale). Log NVR registra tentativo.</td></tr>
<tr><td>23:47</td><td>—</td><td>Timestamp di sistema lettera digitale su tablet.</td></tr>
<tr><td>23:50</td><td>Rinaldi esce dalla Sala Blu attraverso il condotto di ventilazione.</td><td>Fibra di lana nera (EV-04) si incastra nella griglia metallica.</td></tr>
<tr><td>23:52</td><td>Rinaldi calca il terrazzo del terzo piano.</td><td>Impronta parziale di suola esagonale, taglia 44 (EV-05).</td></tr>
<tr><td>00:00</td><td>Rinaldi raggiunge parcheggio Marina Park ed esce con veicolo GE-AB-447.</td><td>Telecamera privata ristorante «Il Marinajo» registra uscita compatibile con VW Golf grigia.</td></tr>
<tr><td>00:30</td><td>Ingresso in palestra FitActive di Luca Greco con badge magnetico di Rinaldi.</td><td>Video sorveglianza interna smonta alibi (Greco presenta neo pigmentato assente in Rinaldi).</td></tr>
<tr><td>01:05</td><td>Priya Sharma ritorna a Palazzo Doria. Accede al sistema NVR e <strong>ALTERA I LOG</strong> cancellando tentativo delle 23:45; tenta di sottrarre il tablet.</td><td>Kyle Brennan (già presente, corpo scoperto alle 00:45) la sorprende. Sharma simula arrivo appena avvenuto.</td></tr>
<tr><td>01:23</td><td>—</td><td><strong>CHIAMATA AL 112</strong> da parte di Kyle Brennan. Arrivo Volante e ambulanza 118.</td></tr>
</table>
</div>

</div><div class="page">
<div class="classification">RISERVATO — USO UFFICIALE — 447-GN</div>
<div class="doc-meta">
<table>
<tr><td><strong>DOCUMENTO:</strong> DOSSIER INTEGRATO 447-GN</td><td><strong>BATES:</strong> 447-GN-DOSS-003</td></tr>
<tr><td><strong>REDATTO DA:</strong> Agente Speciale J. Carver (8847)</td><td><strong>DATA:</strong> 6 ottobre 2026</td></tr>
<tr><td><strong>VERIFICATO DA:</strong> Agente Speciale M. Vance (8851)</td><td><strong>PAGINA:</strong> 3 di 12</td></tr>
</table>
</div>

<div class="section">
<div class="section-title">Sezione III — Rapporto di Sopralluogo e Scena del Crimine</div>

<div class="sub-section">3.1 Dati Generali</div>
<table class="data-table">
<tr><td style="width:25%">LOCALITÀ</td><td>Palazzo Doria, Salita Santa Caterina 14, Genova — Piano terzo, unità immobiliare "Sala Blu"</td></tr>
<tr><td>DATA SOPRALLUOGO</td><td>4 ottobre 2026, ore 01:45 — 03:15</td></tr>
<tr><td>ORA RILEVAMENTO CADAVERE</td><td>4 ottobre 2026, ore 00:45 (dichiarata da Kyle Brennan)</td></tr>
<tr><td>ORA ARRIVO VOLANTE</td><td>4 ottobre 2026, ore 01:23</td></tr>
<tr><td>ORA COSTATAZIONE DECESSO</td><td>4 ottobre 2026, ore 01:31 (Dott. Paolo Ferrante, 118)</td></tr>
<tr><td>AGENTI</td><td>J. Carver (8847), M. Vance (8851), Dir. Indagini Preliminari Dott. Luca Ferraris</td></tr>
<tr><td>CONDIZIONI AMBIENTALI</td><td>Temperatura 22°C, umidità 65%; allerta rossa mareggiata attiva; isolamento centro storico</td></tr>
</table>

<div class="sub-section">3.2 Descrizione Locale — Sala Blu</div>
<p>
La Sala Blu è ubicata al terzo piano dell'immobile. Destinata a ufficio direzionale, presenta pavimentazione in parquet, pareti rivestite con pannelli acustici di colore blu, controsoffitto con faretti ad incasso. Dimensioni interne: circa <strong>5,40 m (est-ovest) × 4,20 m (nord-sud)</strong>; altezza interna 2,70 m. Superficie calpestabile ~32 m².
</p>
<p>
Porta principale in legno blindato con serratura a cilindro elettronico e lettore biometrico. Card reader esterno per accesso con tessera magnetica. Sistema di allarme volumetrico e perimetrale attivo. Finestra a bilico in alluminio sulla parete sud con accesso al terrazzo esterno (~12 m²).
</p>

<div class="sub-section">3.3 Planimetria Tecnica</div>
<div class="evidence-box">
<div class="evidence-label">Fig. 1 — Planimetria Tecnica Sala Blu (Scala 1:50)</div>
<div style="border: 2px dashed #000; padding: 30px; text-align: center; background: #eee; font-family: 'Courier New', monospace;">
[SEGNAPOSTO GRAFICO: Planimetria Sala Blu — Rif. 447-GN-0003]<br>
Indicare: Scrivania, Poltrona, Griglia di ventilazione (nord),<br>
Pannello acustico con foro proiettile (est), Finestra a bilico (sud).
</div>
</div>

</div>
</div>
</body>
</html>
"""

# Salva il file HTML e genera il PDF
with open('dossier_447_gn.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

HTML(filename='dossier_447_gn.html').write_pdf('dossier_447_gn.pdf')
print("PDF generato con successo: dossier_447_gn.pdf")