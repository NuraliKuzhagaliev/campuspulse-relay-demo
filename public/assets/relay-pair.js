// This browser page is served by RELAY after actual Google consent. No inline
// script/CSP exception, token value, or automatic desktop grant is used.
const approve=document.getElementById('approve');
if(approve)approve.addEventListener('click',async()=>{
 approve.disabled=true;
 try{
  const response=await fetch('/api/auth/pair/approve',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Relay-CSRF':approve.dataset.csrf},body:JSON.stringify({pairing_id:approve.dataset.pair})});
  document.getElementById('result').textContent=response.ok?'Connected. Return to RELAY. / Подключено. Вернитесь в RELAY. / Қосылды. RELAY-ге оралыңыз.':'Not connected; restart pairing. / Не подключено; повторите подключение. / Қосылмады; қосылымды қайталаңыз.';
 }catch{document.getElementById('result').textContent='Connection unavailable. / Подключение недоступно. / Қосылым қолжетімсіз.';approve.disabled=false;}
});
