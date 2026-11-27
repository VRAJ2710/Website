/* chat108saferxA: sticky desk tabs offset and reading-progress bar for the v3 home preview. No network, no storage. */
(function(){
"use strict";
if(window.__v8a)return;window.__v8a=1;
var D=document,bar=D.querySelector(".v8-prog i");
var tabs=D.querySelector(".v8-tabs"),hdr=D.querySelector("header.site");
function stick(){if(!tabs||!hdr)return;var c=window.getComputedStyle(hdr),t=0;if(c.position==="sticky"||c.position==="fixed")t=(parseFloat(c.top)||0)+hdr.offsetHeight;tabs.style.setProperty("--v8-top",Math.max(0,Math.round(t))+"px");tabs.classList.add("v8-stick");}
stick();window.addEventListener("resize",stick,{passive:true});
var rm=window.matchMedia?window.matchMedia("(prefers-reduced-motion: reduce)"):null;
if(!bar||(rm&&rm.matches))return;
var busy=false;
function upd(){busy=false;var h=D.documentElement,max=h.scrollHeight-h.clientHeight,y=window.pageYOffset||h.scrollTop||0;var p=max>0?Math.min(1,Math.max(0,y/max)):0;bar.style.transform="scaleX("+p.toFixed(4)+")";}
function on(){if(busy)return;busy=true;window.requestAnimationFrame(upd);}
window.addEventListener("scroll",on,{passive:true});
window.addEventListener("resize",on,{passive:true});
upd();
})();
