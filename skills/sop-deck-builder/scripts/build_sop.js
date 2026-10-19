#!/usr/bin/env node
/* SOP Deck Builder — parse an SOP text file and render an A4 PPTX.
   Usage: node build_sop.js --input sop.txt --out out.pptx [identity options] */
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");

// ---------- args ----------
const args = Object.fromEntries(process.argv.slice(2).reduce((a,v,i,arr)=>{
  if(v.startsWith("--")) a.push([v.slice(2), arr[i+1]]); return a;
},[]));
const INPUT = args.input, OUT = args.out || "SOP.pptx";
const BRAND_NAME = args["brand-name"] || "YOUR ORGANIZATION";
const TAGLINE = args.tagline || "A clear process, ready to use.";
const LOGO_LIGHT = args["logo-light"] || null;
const LOGO_DARK = args["logo-dark"] || null;
if(!INPUT){ console.error("Missing --input"); process.exit(1); }
const RAW = fs.readFileSync(INPUT, "utf8");

// ---------- design tokens ----------
const NAVY="1E2B4D", INK="0A0E27", TERRA="CF5B2B", PAPER="FAFAF7";
const MUTED="8A93A6", MUTED_D="6B7690", LINE="D8DCE6", CARD="F4F6FA", DASH="B8C0D0";
const PANEL_D="14203E", BORD_D="273458", TXT_D="D7DCE6", MUT_D="9AA5BC";
const DISP="Fraunces", SANS="Inter Tight", MONO="JetBrains Mono";
function readableFile(file){ if(!file) return null; try{ return fs.existsSync(file) ? file : null; }catch(e){ return null; } }
const MARK={white:readableFile(LOGO_LIGHT), navy:readableFile(LOGO_DARK)};
// Draw an approved image when supplied, otherwise a neutral geometric stand-in.
function drawMark(x,y,s,dark){
  const img = dark?MARK.white:MARK.navy;
  if(img){ S.addImage({path:img,x,y,w:s,h:s}); return; }
  S.addShape(p.ShapeType.ellipse,{x,y,w:s,h:s,fill:{color:dark?"FFFFFF":NAVY},line:{type:"none"}});
  S.addText("•",{x,y,w:s,h:s,fontFace:SANS,fontSize:Math.round(s*22),bold:true,color:dark?NAVY:"FFFFFF",align:"center",valign:"middle",margin:0});
}
const PW=8.27, PH=11.69, MX=0.55, CW=PW-1.1, TOP=1.05, BOT=PH-0.8;

// ---------- parsing ----------
function clean(s){ return (s||"").replace(/\r/g,"").replace(/[ \t]+/g," ").trim(); }
const lines = RAW.split("\n");

// metadata (line containing "SOP ID" and separators)
const META_KEYS=["SOP ID","Family","Category","Type","Status","Owner","Version","Date"];
let meta={};
const metaLine = lines.find(l=>/SOP ID/.test(l) && /·/.test(l));
if(metaLine){
  metaLine.split("·").forEach(chunk=>{
    const c=clean(chunk);
    const k=META_KEYS.find(key=>c.startsWith(key));
    if(k) meta[k]=clean(c.slice(k.length));
  });
}
// title line: "SOP X.X · Title — subtitle"
let title="[ SOP Title ]", subtitle="";
const tLine = lines.find(l=>/^\s*SOP\s+[\d.]+\s*·/.test(l) && !/SOP ID/.test(l));
if(tLine){
  let t=clean(tLine.replace(/^\s*SOP\s+[\d.]+\s*·\s*/,""));
  const m=t.split(/\s+[—–-]\s+/);
  title=m[0]; subtitle=m.slice(1).join(" — ");
}

// section splitter: headers like "00 · Name — Subtitle" or bare special headers
const SPECIAL=["Screenshot Non-Negotiables","Final Teaching Message"];
function isHeader(l){
  return /^\s*\d{2}\s*·\s*/.test(l) || SPECIAL.some(s=>clean(l).toLowerCase()===s.toLowerCase());
}
let sections=[], cur=null;
for(const l of lines){
  if(isHeader(l)){
    if(cur) sections.push(cur);
    const c=clean(l);
    let num="", name=c, sub="";
    const hm=c.match(/^(\d{2})\s*·\s*(.+)$/);
    if(hm){ num=hm[1]; const rest=hm[2]; const parts=rest.split(/\s+[—–-]\s+/); name=parts[0]; sub=parts.slice(1).join(" — "); }
    cur={num,name,sub,body:[]};
  } else if(cur){ cur.body.push(l); }
  else { /* preamble before first header (metadata/title) ignored */ }
}
if(cur) sections.push(cur);
const byNum = n => sections.find(s=>s.num===n);
const byName = re => sections.find(s=>re.test(s.name));
const SPECIAL_NAME = /Use Case|Demonstration|Test|Common Mistakes|Does Not Cover|Not Cover|Log|Final Teaching|Screenshot Non/i;
function byNameOrLegacyNumber(re,num){
  const named = byName(re);
  if(named) return named;
  const numbered = byNum(num);
  return numbered && !SPECIAL_NAME.test(numbered.name) ? numbered : null;
}

// producer-facing subtitles -> client-ready equivalents (final SOP is not a shooting brief)
const SUBMAP={
 "what the reader can do after":"What you'll be able to do",
 "what you need before you start":"Before you start",
 "teach this before the demo":"Before you begin",
 "how the reader knows they have it":"Check your work",
 "what goes wrong":"Avoid these mistakes",
 "what this sop covers":"What this covers",
 "library entry":"For the record"
};
function clientSub(sub){ if(!sub) return sub; const k=sub.toLowerCase().trim(); return (k in SUBMAP)?SUBMAP[k]:sub; }

// markdown pipe-table helpers (used by parseBody and parseUseCases)
function isTableRow(l){ return /^\|.*\|$/.test(l) && (l.match(/\|/g)||[]).length>=2; }
function isTableSep(l){ return /^\|[\s:|-]+\|$/.test(l) && /-/.test(l); }
function splitRow(l){ return l.replace(/^\|/,"").replace(/\|$/,"").split("|").map(c=>clean(c)); }

// body → paragraphs vs bullet-lines vs tables. Heuristic: a "paragraph" line is long & sentence-like;
// short standalone lines are bullets; runs of "| a | b |" lines become a table.
// Returns array of {type:'p'|'b'|'sub'|'table', text|rows}.
function parseBody(bodyLines){
  const out=[]; let tbl=null;
  const flushT=()=>{ if(tbl && tbl.length) out.push({type:"table",rows:tbl}); tbl=null; };
  for(let raw of bodyLines){
    const l=clean(raw);
    if(isTableRow(l)){ tbl=tbl||[]; if(!isTableSep(l)) tbl.push(splitRow(l)); continue; }
    flushT();
    if(!l) { continue; }
    // sub-label: "Word:" or "1. Word" style lead-ins kept as sub headers
    if(/^[A-Z][A-Za-z /&+]{2,40}:\s*$/.test(l)){ out.push({type:"sub",text:l.replace(/:$/,"")}); continue; }
    const labelMatch=l.match(/^([A-Z][A-Za-z /&+]{2,32}):\s+(.+)$/);
    if(labelMatch && labelMatch[1].split(" ").length<=4){ out.push({type:"p",text:l}); continue; }
    // long -> paragraph, short -> bullet
    if(l.length>110 || /[.]\s/.test(l) && l.length>70) out.push({type:"p",text:l});
    else out.push({type:"b",text:l});
  }
  flushT();
  return out;
}

// shot list parser
function parseShots(section){
  if(!section) return {intro:[],shots:[]};
  const shots=[]; let intro=[]; let sh=null;
  const push=()=>{ if(sh) shots.push(sh); };
  for(let raw of section.body){
    const l=clean(raw);
    const sm=l.match(/^Shot\s+(\d+)\s*[—–-]\s*(.+)$/i);
    if(sm){ push(); sh={n:sm[1], title:sm[2], capture:"", caption:"", callouts:[], input:null, inputLabel:null, expected:""}; continue; }
    if(!sh){ if(l) intro.push(l); continue; }
    let m;
    if(m=l.match(/^Capture:\s*(.+)$/i)) sh.capture=m[1];
    else if(m=l.match(/^Caption:\s*(.+)$/i)) sh.caption=m[1];
    else if(m=l.match(/^Callouts?:\s*(.+)$/i)) sh.callouts=m[1].split(/,|;/).map(clean).filter(Boolean);
    else if(m=l.match(/^(Paste|Ask):\s*(.+)$/i)){ sh.inputLabel=(m[1].toLowerCase()==="ask"?"ASK":"PASTE THIS"); sh.input=m[2]; }
    else if(m=l.match(/^(Recommended|Include|Text|Alternative names?):\s*(.+)$/i)){ if(!sh.input){sh.inputLabel=m[1].toUpperCase(); sh.input=m[2];} }
    else if(m=l.match(/^Expected( result)?:\s*(.+)$/i)) sh.expected=m[2];
    else if(sh.input!=null && l) sh.input+="\n"+l;   // continuation of paste/ask (preserve line breaks)
    else if(l && !sh.caption) sh.capture += (sh.capture?" ":"")+l;
  }
  push();
  return {intro, shots};
}

// pull "When ... right tool" / "not enough" out of use cases
function parseUseCases(section){
  if(!section) return null;
  const txt=section.body.map(clean);
  let mode="right", right=[], not=[], moveTo="", tbl=null, table=null;
  const flushT=()=>{ if(tbl && tbl.length) table=tbl; tbl=null; };
  for(const l of txt){
    if(!l) continue;
    if(isTableRow(l)){ tbl=tbl||[]; if(!isTableSep(l)) tbl.push(splitRow(l)); continue; }
    flushT();
    if(/right tool/i.test(l)){ mode="right"; continue; }
    if(/not enough/i.test(l)){ mode="not"; continue; }
    if(/^Move to:/i.test(l)){ moveTo=l.replace(/^Move to:\s*/i,""); continue; }
    (mode==="right"?right:not).push(l);
  }
  flushT();
  return {right,not,moveTo,table};
}

// ---------- rendering ----------
const p=new pptxgen();
p.defineLayout({name:"A4P",width:PW,height:PH}); p.layout="A4P";
p.author=BRAND_NAME; p.company=BRAND_NAME;
let S, y=TOP, curSection="", curDark=false;
const footMeta = ()=> (meta["SOP ID"]?("SOP "+meta["SOP ID"]):"SOP");

function estLines(text,w,size){ const cpl=Math.max(6, Math.floor((w*72)/(size*0.52))); return Math.max(1, Math.ceil((text||"").length/cpl)); }
function estH(text,w,size,lh){ return estLines(text,w,size)*(size*(lh||1.2)/72); }
// Dedicated height for the mono PASTE/ASK box: JetBrains Mono advances ~0.6em (wider than the
// 0.52 factor estLines uses), so estimate lines with a mono-accurate factor, add a line of slack
// for structural wraps, and grow the box to fit. Capped only at a full content page for safety.
function pasteBoxH(text){
  const w=CW-0.36, size=8.5, lh=1.3;
  const cpl=Math.max(8, Math.floor((w*72)/(size*0.62)));
  const segs=String(text||"").split("\n");
  let lines=0; for(const s of segs) lines += Math.max(1, Math.ceil(s.length/cpl));
  lines += 1;
  return Math.min(BOT-TOP, 0.34 + lines*(size*lh/72) + 0.16);
}

function header(dark){
  drawMark(MX,0.4,0.26,dark);
  S.addText(BRAND_NAME.toUpperCase(),{x:MX+0.34,y:0.4,w:4,h:0.26,fontFace:MONO,fontSize:8.5,bold:true,color:dark?PAPER:NAVY,charSpacing:1.5,valign:"middle",margin:0});
  S.addText(curSection,{x:PW-4.72,y:0.4,w:4.1,h:0.26,fontFace:MONO,fontSize:8,color:dark?"AEB6C6":MUTED_D,charSpacing:1.3,align:"right",valign:"middle",margin:0});
  S.addShape(p.ShapeType.line,{x:MX,y:0.8,w:CW,h:0,line:{color:dark?BORD_D:LINE,width:0.75}});
}
function footer(dark){
  S.addText(TAGLINE,{x:MX,y:PH-0.52,w:3.8,h:0.3,fontFace:SANS,fontSize:9,italic:true,color:dark?PAPER:NAVY,valign:"middle",margin:0});
  S.addText(footMeta(),{x:PW-4.72,y:PH-0.52,w:4.1,h:0.3,fontFace:MONO,fontSize:8,color:dark?"8893A8":MUTED,charSpacing:1.3,align:"right",valign:"middle",margin:0});
}
function newPage(section,dark){ curSection=section??curSection; curDark=!!dark; S=p.addSlide(); S.background={color:dark?INK:PAPER}; header(curDark); footer(curDark); y=TOP; }
function ensure(h){ if(y+h>BOT) newPage(curSection,curDark); }

function eyebrow(x,yy,w,t,c){ S.addText(t,{x,y:yy,w,h:0.24,fontFace:MONO,fontSize:9,bold:true,color:c||TERRA,charSpacing:2,valign:"middle",margin:0}); }
function sectionHead(num,name,sub){
  sub=clientSub(sub);
  ensure(1.0);
  eyebrow(MX,y,CW,(num?num+" · ":"")+name.toUpperCase(),TERRA);
  S.addText(sub||name,{x:MX,y:y+0.26,w:CW,h:0.4,fontFace:SANS,fontSize:17,bold:true,color:NAVY,valign:"middle",margin:0});
  S.addShape(p.ShapeType.line,{x:MX,y:y+0.72,w:CW,h:0,line:{color:LINE,width:1}});
  y+=0.95;
}
function paragraph(text,dark){
  const h=estH(text,CW,11,1.28)+0.1; ensure(h);
  S.addText(text,{x:MX,y,w:CW,h,fontFace:SANS,fontSize:11,color:dark?TXT_D:NAVY,valign:"top",margin:0,lineSpacingMultiple:1.28});
  y+=h;
}
function subLabel(text){ ensure(0.4); S.addText(text.toUpperCase(),{x:MX,y,w:CW,h:0.28,fontFace:MONO,fontSize:9,bold:true,color:TERRA,charSpacing:1.5,valign:"middle",margin:0}); y+=0.32; }
function bulletsBlock(items,dark){
  // add bullets, paginating if needed
  let batch=[];
  const flush=()=>{ if(!batch.length) return; const h=batch.reduce((a,t)=>a+estH(t,CW-0.25,11,1.2)+0.05,0)+0.05; ensure(Math.min(h,BOT-TOP));
    S.addText(batch.map(t=>({text:t,options:{bullet:{indent:14},breakLine:true,color:dark?TXT_D:NAVY,paraSpaceAfter:5}})),{x:MX,y,w:CW,h,fontFace:SANS,fontSize:11,valign:"top",margin:0}); y+=h; batch=[]; };
  for(const it of items){ // simple greedy pack ~6 per group
    batch.push(it);
    if(batch.length>=6){ flush(); }
  }
  flush();
}
function tableBlock(rows,dark){
  if(!rows||!rows.length) return;
  const ncol=Math.max(...rows.map(r=>r.length));
  rows=rows.map(r=>{ const rr=r.slice(); while(rr.length<ncol) rr.push(""); return rr; });
  const colW=CW/ncol;
  // step the font down as columns grow so wide reference tables stay legible on portrait A4
  const fs = ncol>=6 ? 8 : ncol>=5 ? 8.5 : 9.5;
  const mg = ncol>=6 ? 3 : 5;
  const rowHt=cells=>Math.max(0.32, Math.max(...cells.map(c=>estH(c,colW-mg/36,fs,1.16)))+0.14);
  const heights=rows.map(r=>rowHt(r));
  const total=heights.reduce((a,b)=>a+b,0);
  // keep a table together: if it doesn't fit in the remaining space, start a fresh page
  if(y+total>BOT && total<=BOT-TOP) newPage(curSection,curDark);
  const tRows=rows.map((r,ri)=>r.map(c=>({
    text:c,
    options: ri===0
      ? {fill:{color:NAVY},color:PAPER,bold:true,fontFace:SANS,fontSize:fs,valign:"middle",align:"left",margin:mg}
      : {fill:{color:ri%2?PAPER:CARD},color:dark?TXT_D:INK,fontFace:SANS,fontSize:fs,valign:"top",align:"left",margin:mg}
  })));
  S.addTable(tRows,{x:MX,y,w:CW,colW:Array(ncol).fill(colW),rowH:heights,border:{type:"solid",color:LINE,pt:0.5},valign:"top"});
  y+=total+0.14;
}
function renderBody(blocks,dark){
  // group consecutive bullets
  let bg=[];
  const flushB=()=>{ if(bg.length){ bulletsBlock(bg,dark); bg=[]; } };
  for(const b of blocks){
    if(b.type==="b"){ bg.push(b.text); }
    else if(b.type==="table"){ flushB(); tableBlock(b.rows,dark); }
    else { flushB(); if(b.type==="sub") subLabel(b.text); else paragraph(b.text,dark); }
  }
  flushB();
}
function calloutCard(eb,ttl,body){
  const bh=estH(body,CW-0.5,10,1.15); const h=Math.max(1.1,0.7+bh); ensure(h+0.15);
  S.addShape(p.ShapeType.rect,{x:MX,y,w:CW,h,fill:{color:CARD},line:{color:LINE,width:1}});
  S.addShape(p.ShapeType.rect,{x:MX,y,w:0.06,h,fill:{color:TERRA}});
  eyebrow(MX+0.22,y+0.14,CW-0.4,eb,TERRA);
  S.addText(ttl,{x:MX+0.22,y:y+0.36,w:CW-0.4,h:0.3,fontFace:SANS,fontSize:12.5,bold:true,color:NAVY,valign:"middle",margin:0});
  S.addText(body,{x:MX+0.22,y:y+0.66,w:CW-0.4,h:h-0.76,fontFace:SANS,fontSize:10,italic:true,color:MUTED,valign:"top",margin:0,lineSpacingMultiple:1.15});
  y+=h+0.15;
}

// ---- a single demonstration step block (client-ready) ----
function stepBlock(sh){
  const inputH = sh.input ? pasteBoxH(sh.input) : 0;
  const expH = sh.expected ? 0.44 : 0;
  const calloutH = sh.callouts.length ? 0.28+Math.ceil(sh.callouts.length)*0.22 : 0;
  const SHOT_H = 2.5;
  const blockH = 0.52 + SHOT_H + 0.38 + calloutH + inputH + expH + 0.3;
  ensure(blockH);
  const x=MX;
  // step header: number + action title
  S.addShape(p.ShapeType.ellipse,{x,y,w:0.38,h:0.38,fill:{color:NAVY}});
  S.addText(sh.n,{x,y,w:0.38,h:0.38,fontFace:SANS,fontSize:12,bold:true,color:PAPER,align:"center",valign:"middle",margin:0});
  S.addText(sh.title,{x:x+0.52,y:y-0.03,w:CW-0.52,h:0.44,fontFace:DISP,fontSize:15,color:NAVY,valign:"middle",margin:0});
  y+=0.52;
  // screenshot frame (clean, single label inside)
  S.addShape(p.ShapeType.rect,{x,y,w:CW,h:SHOT_H,fill:{color:"FFFFFF"},line:{color:DASH,width:1,dashType:"dash"}});
  S.addText([{text:"\u25A2  DROP SCREENSHOT",options:{fontFace:MONO,fontSize:10,bold:true,color:MUTED_D,breakLine:true}},{text:"Insert > Picture, or paste over this frame",options:{fontFace:SANS,fontSize:8.5,italic:true,color:MUTED}}],
    {x,y,w:CW,h:SHOT_H,align:"center",valign:"middle",margin:0,lineSpacingMultiple:1.3});
  y+=SHOT_H+0.1;
  // caption (client-facing explanation of the screen)
  if(sh.caption){ const ch=Math.max(0.28,estH(sh.caption,CW,10.5,1.2)); S.addText(sh.caption,{x,y,w:CW,h:ch,fontFace:SANS,fontSize:10.5,color:NAVY,valign:"top",margin:0,lineSpacingMultiple:1.2}); y+=ch+0.06; }
  // what to look for (former callouts) — reader guidance, not shooting notes
  if(sh.callouts.length){
    S.addText("WHAT TO LOOK FOR",{x,y,w:CW,h:0.2,fontFace:MONO,fontSize:7.5,bold:true,color:TERRA,charSpacing:1,valign:"middle",margin:0}); y+=0.22;
    S.addText(sh.callouts.map(c=>({text:c,options:{bullet:{indent:12},breakLine:true,color:MUTED_D,paraSpaceAfter:3}})),
      {x:x+0.1,y,w:CW-0.1,h:sh.callouts.length*0.22,fontFace:SANS,fontSize:9.5,valign:"top",margin:0});
    y+=sh.callouts.length*0.22;
  }
  // input the reader actually types/pastes (client content)
  if(sh.input){
    const ih=pasteBoxH(sh.input); ensure(ih+0.1);
    S.addShape(p.ShapeType.rect,{x,y,w:CW,h:ih,fill:{color:CARD},line:{color:LINE,width:0.75}});
    S.addShape(p.ShapeType.rect,{x,y,w:0.05,h:ih,fill:{color:TERRA}});
    S.addText(sh.inputLabel||"PASTE THIS",{x:x+0.18,y:y+0.1,w:CW-0.3,h:0.2,fontFace:MONO,fontSize:7.5,bold:true,color:TERRA,charSpacing:1,valign:"middle",margin:0});
    S.addText(String(sh.input).split("\n").map(t=>({text:t,options:{breakLine:true}})),{x:x+0.18,y:y+0.30,w:CW-0.36,h:ih-0.42,fontFace:MONO,fontSize:8.5,color:NAVY,valign:"top",margin:0,lineSpacingMultiple:1.3});
    y+=ih+0.08;
  }
  if(sh.expected){ S.addText([{text:"WHAT GOOD LOOKS LIKE   ",options:{fontFace:MONO,fontSize:7.5,bold:true,color:TERRA}},{text:sh.expected,options:{fontFace:SANS,fontSize:9.5,italic:true,color:MUTED_D}}],{x,y,w:CW,h:0.42,valign:"top",margin:0,lineSpacingMultiple:1.15}); y+=0.44; }
  S.addShape(p.ShapeType.line,{x,y:y+0.05,w:CW,h:0,line:{color:LINE,width:0.5}});
  y+=0.26;
}

// ================= BUILD =================
// 1) COVER
S=p.addSlide(); S.background={color:INK}; curDark=true; curSection="STANDARD OPERATING PROCEDURE";
drawMark(MX,0.6,0.38,true);
S.addText(BRAND_NAME.toUpperCase(),{x:MX+0.5,y:0.6,w:5,h:0.38,fontFace:MONO,fontSize:10,bold:true,color:PAPER,charSpacing:2,valign:"middle",margin:0});
S.addText("STANDARD OPERATING PROCEDURE",{x:PW-3.3,y:0.6,w:2.75,h:0.38,fontFace:MONO,fontSize:8,color:"AEB6C6",charSpacing:1,align:"right",valign:"middle",margin:0});
eyebrow(MX,3.2,7,"STANDARD OPERATING PROCEDURE",TERRA);
// title (accent last word)
const tw2=title.split(" "); const tHead=tw2.slice(0,-1).join(" "), tAcc=tw2.slice(-1)[0];
S.addText([{text:tHead+" ",options:{color:PAPER,fontFace:DISP}},{text:tAcc,options:{color:TERRA,italic:true,fontFace:DISP}}],
  {x:MX-0.02,y:3.55,w:7.2,h:1.6,fontSize:tHead.length>22?30:36,valign:"top",margin:0,lineSpacingMultiple:1.03});
if(subtitle) S.addText(subtitle,{x:MX,y:5.25,w:6.9,h:0.8,fontFace:SANS,fontSize:12,italic:true,color:"AEB6C6",valign:"top",margin:0,lineSpacingMultiple:1.2});
// metadata grid
S.addShape(p.ShapeType.line,{x:MX,y:6.15,w:CW,h:0,line:{color:BORD_D,width:0.75}});
const order=["SOP ID","Family","Category","Type","Status","Owner","Version","Date"]; const cw4=CW/4;
order.forEach((k,i)=>{ const c=i%4, r=Math.floor(i/4); const gx=MX+c*cw4, gy=6.35+r*0.66;
  S.addText(k.toUpperCase(),{x:gx,y:gy,w:cw4-0.1,h:0.2,fontFace:MONO,fontSize:7.5,bold:true,color:TERRA,charSpacing:1,valign:"middle",margin:0});
  S.addText(meta[k]||"[ … ]",{x:gx,y:gy+0.2,w:cw4-0.12,h:0.34,fontFace:SANS,fontSize:9,color:PAPER,valign:"top",margin:0,lineSpacingMultiple:1.05});
});
S.addShape(p.ShapeType.line,{x:MX,y:7.85,w:CW,h:0,line:{color:BORD_D,width:0.75}});
// how to use + counts
const nShots=parseShots(byNameOrLegacyNumber(/Demonstration/i,"06")).shots.length;
S.addShape(p.ShapeType.rect,{x:0,y:PH-1.5,w:PW,h:1.5,fill:{color:"11162E"}});
S.addText([{text:"How to use this document.  ",options:{bold:true,color:PAPER,fontFace:SANS}},{text:"Follow the steps in order. Each one shows the action to take and the screen you should see.",options:{color:"AEB6C6",italic:true,fontFace:SANS}}],
  {x:MX,y:PH-1.15,w:5.0,h:0.8,fontSize:10,valign:"top",margin:0,lineSpacingMultiple:1.2});
S.addText((meta["Family"]||"")+"\n"+nShots+" STEPS · "+sections.length+" SECTIONS",{x:PW-3.5,y:PH-1.12,w:2.95,h:0.8,fontFace:MONO,fontSize:8.5,color:"8893A8",charSpacing:1,align:"right",valign:"top",margin:0,lineSpacingMultiple:1.3});

// 2) OVERVIEW — render every non-special section in SOURCE ORDER (Definition, Description,
//    Outcome, Prerequisites, Key Concept, plus any extra concept section a brief inserts, e.g.
//    "Context Window and File Limits"). Special sections are matched by NAME so a shifted section
//    number never misroutes content.
const isSpecial=s=>SPECIAL_NAME.test(s.name);
newPage("SOP · OVERVIEW",false);
for(const sec of sections){
  if(isSpecial(sec)) continue;
  curSection="SOP · "+sec.name.toUpperCase();
  sectionHead(sec.num,sec.name,sec.sub);
  renderBody(parseBody(sec.body),false);
  y+=0.15;
}
// use cases (name-first)
const ucSec=byNameOrLegacyNumber(/Use Case/i,"05"); const uc=parseUseCases(ucSec);
if(uc){
  curSection="SOP · USE CASE APPLICATIONS";
  sectionHead(ucSec?ucSec.num:"05","Use Case Applications","When this is the right tool");
  bulletsBlock(uc.right,false); y+=0.1;
  subLabel("When it is not enough"); bulletsBlock(uc.not,false); y+=0.05;
  if(uc.moveTo) calloutCard("MOVE TO","Move to a more advanced workflow",uc.moveTo);
  if(uc.table){ y+=0.12; subLabel("At a glance"); tableBlock(uc.table,false); }
}

// 3) DEMONSTRATION divider + steps (name-first)
const demoSec=byNameOrLegacyNumber(/Demonstration/i,"06");
const {intro,shots}=parseShots(demoSec);
let demoTask=""; for(const l of intro){ const m=l.match(/Demo task:\s*(.+?)(?:\.|$)/i); if(m) demoTask=clean(m[1]); }
newPage("SOP · WALKTHROUGH",true);
eyebrow(MX,3.45,CW,(demoSec&&demoSec.num?demoSec.num+" · ":"")+"DEMONSTRATION",TERRA);
S.addText(demoTask||"The walkthrough",{x:MX,y:3.78,w:CW,h:1.2,fontFace:DISP,fontSize:30,color:PAPER,valign:"top",margin:0,lineSpacingMultiple:1.05});
S.addText("Follow these steps in order. Each one shows the action to take and the screen you should see.",{x:MX,y:5.15,w:CW,h:0.9,fontFace:SANS,fontSize:12.5,italic:true,color:MUT_D,valign:"top",margin:0,lineSpacingMultiple:1.3});
S.addShape(p.ShapeType.line,{x:MX,y:9.2,w:1.1,h:0,line:{color:TERRA,width:2}});
S.addText(shots.length+" STEPS",{x:MX,y:9.35,w:CW,h:0.4,fontFace:MONO,fontSize:11,bold:true,color:TERRA,charSpacing:2.5,valign:"middle",margin:0});
// step pages
newPage("SOP · WALKTHROUGH",false);
for(const sh of shots){ stepBlock(sh); }

// 4) [Screenshot Non-Negotiables intentionally omitted — production instruction, not client-facing]
// 5) Test / Mistakes / Not covered / Log
for(const [num,re,label] of [["07",/Test/i,"TEST & VERIFY"],["08",/Common Mistakes/i,"COMMON MISTAKES"]]){
  const sec=byNameOrLegacyNumber(re,num); if(!sec) continue;
  curSection="SOP · "+label; sectionHead(sec.num,sec.name,sec.sub); renderBody(parseBody(sec.body),false); y+=0.1;
}
// not covered (stronger panel)
const ncSec=byNameOrLegacyNumber(/Does Not Cover|Not Cover/i,"09");
if(ncSec){ curSection="SOP · SCOPE"; sectionHead(ncSec.num,ncSec.name,ncSec.sub);
  const items=parseBody(ncSec.body).filter(b=>b.type==="b"||b.type==="p").map(b=>b.text).filter(t=>!/those topics come later/i.test(t));
  const rows=Math.ceil(items.length/2); const ph2=0.6+rows*0.26; ensure(ph2+0.1);
  S.addShape(p.ShapeType.rect,{x:MX,y,w:CW,h:ph2,fill:{color:CARD},line:{color:TERRA,width:1.25}});
  S.addShape(p.ShapeType.rect,{x:MX,y,w:0.1,h:ph2,fill:{color:TERRA}});
  S.addText("This SOP is scoped deliberately. Each item below is a separate SOP — do not blend them in.",{x:MX+0.35,y:y+0.14,w:CW-0.6,h:0.4,fontFace:SANS,fontSize:10.5,bold:true,color:NAVY,valign:"top",margin:0});
  [0,1].forEach(c=>{ const col=items.slice(c*rows,c*rows+rows);
    S.addText(col.map(t=>({text:t,options:{bullet:{indent:12},breakLine:true,italic:true,color:MUTED,paraSpaceAfter:5}})),{x:MX+0.4+c*(CW/2-0.05),y:y+0.6,w:CW/2-0.5,h:ph2-0.65,fontFace:SANS,fontSize:10,valign:"top",margin:0}); });
  y+=ph2+0.15;
}
// log
const logSec=byNameOrLegacyNumber(/Log/i,"10");
if(logSec){ curSection="SOP · LIBRARY"; sectionHead(logSec.num,logSec.name,logSec.sub); renderBody(parseBody(logSec.body),false); }

// 6) Final teaching message (closing dark)
const ftm=byName(/Final Teaching/i);
newPage("SOP · REVIEW & CLOSE",true);
eyebrow(MX,3.4,CW,"FINAL TEACHING MESSAGE",TERRA);
S.addText([{text:"Before ",options:{color:PAPER,fontFace:DISP}},{text:"you ship",options:{color:TERRA,italic:true,fontFace:DISP}}],{x:MX,y:3.7,w:CW,h:0.7,fontSize:26,valign:"top",margin:0});
if(ftm){ const t=ftm.body.map(clean).filter(Boolean).join(" ");
  S.addText(t,{x:MX,y:4.6,w:CW,h:3.0,fontFace:DISP,fontSize:15,italic:true,color:TXT_D,valign:"top",margin:0,lineSpacingMultiple:1.3}); }
// next SOP if present in log
const nextM=RAW.match(/Next SOP:\s*(.+)/i);
if(nextM) S.addText([{text:"NEXT →  ",options:{fontFace:MONO,bold:true,color:TERRA}},{text:clean(nextM[1]),options:{fontFace:SANS,color:PAPER}}],{x:MX,y:PH-1.0,w:CW,h:0.4,fontSize:12,valign:"middle",margin:0});

async function writeValidatedPackage(){
  const fileName = await p.writeFile({fileName:OUT});

  // PptxGenJS 4.0.1 may declare unused slideMaster2..6 parts without
  // writing those files. Remove only stale slide-master declarations so
  // strict OOXML validators do not require PowerPoint to repair the deck.
  const archive = await JSZip.loadAsync(fs.readFileSync(OUT));
  const typesPath = "[Content_Types].xml";
  const originalTypes = await archive.file(typesPath).async("string");
  const cleanedTypes = originalTypes.replace(
    /<Override PartName="\/(ppt\/slideMasters\/slideMaster\d+\.xml)" ContentType="application\/vnd\.openxmlformats-officedocument\.presentationml\.slideMaster\+xml"\/>/g,
    (declaration, member) => archive.file(member) ? declaration : ""
  );
  if(cleanedTypes !== originalTypes){
    archive.file(typesPath, cleanedTypes);
    const payload = await archive.generateAsync({type:"nodebuffer", compression:"DEFLATE", compressionOptions:{level:9}});
    fs.writeFileSync(OUT, payload);
  }
  console.log("WROTE",fileName,"| shots:",shots.length,"| sections:",sections.length);
}

writeValidatedPackage().catch(error=>{
  console.error("Failed to write PPTX:", error.message);
  process.exitCode = 1;
});
