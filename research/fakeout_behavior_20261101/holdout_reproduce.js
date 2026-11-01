// Holdout on previously unseen pairs. Same analyze() function as first pass.
const fs=require("fs");
function analyze(s,b){
  let ev=[],rej={gap:0,doubleSweep:0},last={};
  for(let i=101;i<b.length-12;i++){
    let good=true;
    for(let k=i-81;k<=i+12;k++){if(k>0 && b[k].t-b[k-1].t!==14400000){good=false;break}}
    if(!good){rej.gap++;continue}
    let atr=0;for(let k=i-14;k<i;k++){let x=b[k],pc=b[k-1].c;atr+=Math.max(x.h-x.l,Math.abs(x.h-pc),Math.abs(x.l-pc))}atr/=14;
    if(!(atr>0))continue;
    let high=-Infinity,low=Infinity;
    for(let k=i-20;k<i;k++){high=Math.max(high,b[k].h);low=Math.min(low,b[k].l)}
    const x=b[i],pup=x.h>high+atr*0.1,pdn=x.l<low-atr*0.1;
    if(pup&&pdn){rej.doubleSweep++;continue}
    let type="",dir=0;
    if(pup){if(x.c<=high&&x.c>=low){type="fake_up";dir=-1}else if(x.c>high){type="true_up";dir=1}}
    else if(pdn){if(x.c>=low&&x.c<=high){type="fake_dn";dir=1}else if(x.c<low){type="true_dn";dir=-1}}
    else if(x.c>=low&&x.c<=high){
      let nu=x.h>=high-atr*0.1,nd=x.l<=low+atr*0.1;
      if(nu&&!nd){type="near_up";dir=-1}
      if(nd&&!nu){type="near_dn";dir=1}
    }
    if(!type || i-(last[type]??-1000)<=12)continue;
    last[type]=i;
    const entry=b[i+1].o,tp=entry+dir*atr,sl=entry-dir*atr;
    let status="TIMEOUT",exit=b[i+12].c,hold=12;
    for(let j=i+1;j<=i+12;j++){
      let bar=b[j],w=(dir>0?bar.h>=tp:bar.l<=tp),l=(dir>0?bar.l<=sl:bar.h>=sl);
      if(w&&l){status="AMBIGUOUS";exit=sl;hold=j-i;break}
      if(w){status="WIN";exit=tp;hold=j-i;break}
      if(l){status="LOSS";exit=sl;hold=j-i;break}
    }
    const trend=(b[i-1].c-b[i-81].c)/(atr*Math.sqrt(80)),gross=dir*(exit-entry)/entry;
    ev.push({s,type,t:x.t,entryTime:b[i+1].t,dir,entry,atr,high,low,trend,regime:trend>1?"UP":trend< -1?"DOWN":"SIDE",period:x.t<Date.parse("2025-06-01T00:00:00Z")?"early":"late",status,hold,gross,base:gross-0.002,stress:gross-0.0035,breach:pup?(x.h-high)/atr:pdn?(low-x.l)/atr:null,depth:pup?(high-x.c)/atr:pdn?(x.c-low)/atr:null});
  }
  return{ev,rej};
}
function summary(a){
  const n=a.length,win=a.filter(x=>x.status==="WIN").length,loss=a.filter(x=>x.status==="LOSS").length,amb=a.filter(x=>x.status==="AMBIGUOUS").length,timeout=a.filter(x=>x.status==="TIMEOUT").length;
  const mean=f=>n?+(a.reduce((v,x)=>v+x[f],0)/n*100).toFixed(4):null;
  const resolved=win+loss,ratio=resolved?win/resolved:0,z=1.96;
  let bounds=null;if(resolved){const mid=(ratio+z*z/(2*resolved))/(1+z*z/resolved),wid=z*Math.sqrt(ratio*(1-ratio)/resolved+z*z/(4*resolved*resolved))/(1+z*z/resolved);bounds=[+((mid-wid)*100).toFixed(1),+((mid+wid)*100).toFixed(1)]}
  return{n,win,loss,amb,timeout,winPctResolved:resolved?+(ratio*100).toFixed(2):null,wilson95:bounds,meanGrossPct:mean("gross"),meanBasePct:mean("base"),meanStressPct:mean("stress")};
}
const symbols=["BNBUSDT","XRPUSDT","LINKUSDT","OPUSDT","ARBUSDT"];
let all=[];for(const s of symbols){const b=fs.readFileSync(__dirname+"/holdout_data/"+s+"_4h.csv","utf8").trim().split("\n").slice(1).map(l=>{let a=l.split(",").map(Number);return{t:a[0],o:a[1],h:a[2],l:a[3],c:a[4],v:a[5]}});all.push(...analyze(s,b).ev)}
for(const k of ["fake","true","near"]){const a=all.filter(x=>x.type.startsWith(k));console.log(k,JSON.stringify({all:summary(a),strong:summary(a.filter(x=>x.regime!=="SIDE")),side:summary(a.filter(x=>x.regime==="SIDE"))}))}