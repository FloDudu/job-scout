/*
 * Job offer capture bookmarklet - LinkedIn and Wellfound.
 *
 * Install: create a new Firefox bookmark, paste the single-line script
 * below (everything starting with "javascript:") as the URL. Open a
 * LinkedIn or Wellfound job posting, click the bookmark - it downloads a
 * text file named ODE_<date>_<title>.txt in TITRE/ENTREPRISE/
 * LOCALISATION/URL/DESCRIPTION format, consumed by
 * job_scout.parser.parse_offer(). Any other site shows an alert instead
 * of downloading a garbled file.
 *
 * LinkedIn known limitation: the LOCALISATION regex looks for a bullet
 * character (•) as separator, but LinkedIn's job header typically
 * uses a middle dot (·) instead, so this field is usually empty.
 * Left as-is rather than patched - the regex would still be fragile for
 * many location formats even fixed (see job_scout.enrichment, which
 * extracts location/work_mode/salary from the description via an LLM
 * call instead of relying on this field).
 *
 * Wellfound: title/company/location come from document.title, which
 * Wellfound formats as "<title> at <company> • <loc1> • <loc2> ...".
 * The description is the text between the first standalone "Apply"
 * button (the one right under the job title, not followed by "now")
 * and the "Apply now" button at the end of the description - both
 * confirmed against a real posting, not guessed.
 */
javascript:(function(){try{const host=window.location.hostname;const fullText=document.body.innerText;const offerUrl=window.location.href;let title='',company='',jobLocation='',description='[Repere non trouve]';if(host.indexOf('linkedin.com')!==-1){const titleParts=document.title.split('|').map(s=>s.trim());title=titleParts[0]||'';company=titleParts[1]||'';const locMatch=fullText.match(/•\s*([^\n•]+,\s*[A-Z]{2}(?:\s*\([^)]+\))?)/);if(locMatch)jobLocation=locMatch[1].trim();const startMarkers=['propos de l offre d emploi','About the job'];const endMarkers=['Share this opportunity','Partager cette offre','Plus d offres d emploi','More jobs you might like','Activer une alerte emploi','Job alert for'];const normalized=fullText.replace(/[’']/g,' ').replace(/à/g,'a');let start=-1;for(const m of startMarkers){const idx=normalized.indexOf(m);if(idx!==-1){start=idx+m.length;break;}}let end=normalized.length;for(const m of endMarkers){const idx=normalized.indexOf(m,start===-1?0:start);if(idx!==-1&&idx<end)end=idx;}description=start!==-1?fullText.slice(start,end).trim():'[Repere non trouve]';}else if(host.indexOf('wellfound.com')!==-1){const atIdx=document.title.indexOf(' at ');title=atIdx!==-1?document.title.slice(0,atIdx):document.title;const rest=atIdx!==-1?document.title.slice(atIdx+4):'';const restParts=rest.split('•').map(s=>s.trim());company=restParts[0]||'';jobLocation=restParts.slice(1).join(', ');const startMatch=fullText.match(/Apply(?!\s+now)/);const endIdx=fullText.indexOf('Apply now');const startIdx=startMatch?startMatch.index+startMatch[0].length:-1;description=(startIdx!==-1&&endIdx!==-1&&endIdx>startIdx)?fullText.slice(startIdx,endIdx).trim():'[Repere non trouve]';}else{alert('Site non supporte pour la capture: '+host);return;}const content='TITRE: '+title+'\nENTREPRISE: '+company+'\nLOCALISATION: '+jobLocation+'\nURL: '+offerUrl+'\n\nDESCRIPTION:\n'+description;const safeName=(title||'offre').replace(/[^a-z0-9]+/gi,'_').slice(0,60);const stamp=new Date().toISOString().slice(0,10);const blob=new Blob([content],{type:'text/plain;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='ODE_'+stamp+'_'+safeName+'.txt';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);}catch(err){alert('Erreur: '+err.message);}})();
