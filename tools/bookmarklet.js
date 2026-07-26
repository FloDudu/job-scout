/*
 * LinkedIn job offer capture bookmarklet.
 *
 * Install: create a new Firefox bookmark, paste the single-line script
 * below (everything starting with "javascript:") as the URL. Open a
 * LinkedIn job posting, click the bookmark - it downloads a text file
 * named ODE_<date>_<title>.txt in TITRE/ENTREPRISE/LOCALISATION/
 * DESCRIPTION format, consumed by job_scout.parser.parse_offer().
 *
 * Known limitation: the LOCALISATION regex looks for a bullet
 * character (\u2022) as separator, but LinkedIn's job header typically
 * uses a middle dot (·) instead, so this field is usually empty.
 * Left as-is rather than patched - the regex would still be fragile
 * for many location formats even fixed (see job_scout.enrichment,
 * which extracts location/work_mode/salary from the description via
 * an LLM call instead of relying on this field).
 */
javascript:(function(){try{const fullText=document.body.innerText;const titleParts=document.title.split('|').map(s=>s.trim());const title=titleParts[0]||'';const company=titleParts[1]||'';let jobLocation='';const locMatch=fullText.match(/\u2022\s*([^\n\u2022]+,\s*[A-Z]{2}(?:\s*\([^)]+\))?)/);if(locMatch)jobLocation=locMatch[1].trim();const startMarkers=['propos de l offre d emploi','About the job'];const endMarkers=['Share this opportunity','Partager cette offre','Plus d offres d emploi','More jobs you might like','Activer une alerte emploi','Job alert for'];const normalized=fullText.replace(/[\u2019']/g,' ').replace(/\u00e0/g,'a');let start=-1;for(const m of startMarkers){const idx=normalized.indexOf(m);if(idx!=-1){start=idx+m.length;break;}}let end=normalized.length;for(const m of endMarkers){const idx=normalized.indexOf(m,start==-1?0:start);if(idx!=-1&&idx<end)end=idx;}const description=start!=-1?fullText.slice(start,end).trim():'[Repere non trouve]';const content='TITRE: '+title+'\nENTREPRISE: '+company+'\nLOCALISATION: '+jobLocation+'\n\nDESCRIPTION:\n'+description;const safeName=(title||'offre').replace(/[^a-z0-9]+/gi,'_').slice(0,60);const stamp=new Date().toISOString().slice(0,10);const blob=new Blob([content],{type:'text/plain;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='ODE_'+stamp+'_'+safeName+'.txt';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);}catch(err){alert('Erreur: '+err.message);}})();
