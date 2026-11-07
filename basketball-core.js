/* Общий код страницы счёта и страницы результатов */
var C=window.CONFIG||{};
var BASE=(C.FIREBASE_URL||'').replace(/\/+$/,'');
var SYNC=!!BASE;
var EURL=BASE+'/rooms/'+encodeURIComponent(C.ROOM||'saturday')+'/events.json';
var LKEY='bb-events-v3';
var GAME_MS=(Number(C.GAME_MINUTES)||7)*60000;
var MEET_END=String(C.MEETING_END||'10:00');
function endTs(d){var p=MEET_END.split(':'),y=d.split('-');return new Date(+y[0],+y[1]-1,+y[2],+p[0]||9,+p[1]||0,59,999).getTime()}
/* До какого момента игры дня идут в статистику: до конца встречи или до сохранения итогов, что раньше */
function cutFor(St,d){var c=endTs(d),sv=St.saves[d];return sv!=null&&sv<c?sv:c}
function isTraining(St){return Date.now()>cutFor(St,today())}
var COL={w:'#f5f5f5',b:'#000',r:'#E5262B'};
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function pad(n){return ('0'+n).slice(-2)}
function dstr(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())}
function today(){return dstr(new Date())}
function dateOf(ts){return dstr(new Date(ts))}
function hm(ts){var d=new Date(ts);return pad(d.getHours())+':'+pad(d.getMinutes())}
function fmt(d){return new Date(d+'T12:00:00').toLocaleDateString('ru-RU',{weekday:'long',day:'numeric',month:'long',year:'numeric'})}
function fmtShort(d){return new Date(d+'T12:00:00').toLocaleDateString('ru-RU',{day:'numeric',month:'long'})}
function dot(k){return '<span class="dot" style="background:'+COL[k]+'"></span>'}
/* стороны площадки: слева играет команда cur.left, справа вторая */
function sides(c){var L=(c.left===c.a||c.left===c.b)?c.left:c.a;return {l:L,r:L===c.a?c.b:c.a}}
function newTm(){return {acc:0,run:false,since:null,used:false}}
function elapsed(tm,now){return tm.acc+(tm.run&&tm.since!=null?Math.max(0,now-tm.since):0)}
function tsOf(e){return e.ts||parseInt(String(e.id).slice(0,8),36)||0}

/* очки команды = сумма очков её игроков в текущей игре */
function teamScore(St,k){
  var t=St.roster&&St.roster.teams[k];if(!t)return 0;
  return t.players.reduce(function(a,p){return a+(St.cur.pts[p.n]||0)},0);
}
function teamOf(St,name){
  if(!St.roster)return null;
  for(var k in St.roster.teams){if(St.roster.teams[k].players.some(function(p){return p.n===name}))return k}
  return null;
}
/* не больше двух игр подряд: команда, сыгравшая две игры подряд, уступает место */
function streakOf(games,k,d){var n=0;for(var i=games.length-1;i>=0;i--){var g=games[i];if(g.d!==d)break;if(g.a===k||g.b===k)n++;else break}return n}
function nextPair(games,g){
  var third=['w','b','r'].filter(function(k){return k!==g.a&&k!==g.b})[0];
  var stay=g.dr?g.b:(g.sa>g.sb?g.a:g.b),other=stay===g.a?g.b:g.a,benched=null;
  if(streakOf(games,stay,g.d)>=2&&streakOf(games,other,g.d)<2){benched=stay;stay=other}
  if(g.dr&&!benched){var lv=stay===g.a?g.b:g.a;if(streakOf(games,lv,g.d)>=2)benched=lv}
  return {a:stay,b:third,benched:benched};
}
function winners(g){return g.dr?[g.a,g.b]:[g.sa>g.sb?g.a:g.b]}

/* Состояние и протокол целиком восстанавливаются из журнала событий */
function build(events){
  var seen={},snaps=[],St={names:{w:'Белые',b:'Чёрные',r:'Красные'},cur:{a:'w',b:'b',left:'w',pts:{},la:0,lb:0,t0:null,tm:newTm()},games:[],log:[],lastFin:null,roster:null,adj:[],saves:{},w:{w:0,b:0,r:0},td:{w:0,b:0,r:0},trd:{w:0,b:0,r:0}};
  events.forEach(function(e){
    if(seen[e.id])return;seen[e.id]=1;
    var c=St.cur,ts=tsOf(e);
    function snap(kind){snaps.push({k:kind,ts:ts,cur:JSON.parse(JSON.stringify(c)),g:St.games.length,ll:St.log.length,lf:St.lastFin})}
    if(e.t==='pt'){
      var v=(c.pts[e.p]||0)+e.n;if(v<0)return;
      snap('pt');
      /* начало игры: конец предыдущей, если первое очко пришло не позже чем через 3 минуты, иначе первое очко */
      if(c.t0==null)c.t0=(St.lastFin!=null&&ts-St.lastFin<=180000)?St.lastFin:ts;
      c.pts[e.p]=v;
      St.log.push({k:'pt',ts:ts,gi:St.games.length,p:e.p,tm:teamOf(St,e.p),n:e.n,a:c.a,b:c.b,sa:teamScore(St,c.a),sb:teamScore(St,c.b),m:c.tm.used?Math.floor(elapsed(c.tm,ts)/60000)+1:Math.max(1,Math.floor((ts-c.t0)/60000)+1)});
    }
    else if(e.t==='score'){var lk=e.s==='a'?'la':'lb';c[lk]=Math.max(0,c[lk]+e.n)}
    else if(e.t==='setscore'){c.la=e.sa;c.lb=e.sb}
    else if(e.t==='tstart'){if(!c.tm.run){c.tm.run=true;c.tm.since=ts;c.tm.used=true}}
    else if(e.t==='tpause'){if(c.tm.run){c.tm.acc+=Math.max(0,ts-c.tm.since);c.tm.run=false;c.tm.since=null}}
    else if(e.t==='treset'){c.tm=newTm()}
    else if(e.t==='pabs'){
      if(St.roster)for(var kk in St.roster.teams)St.roster.teams[kk].players.forEach(function(p){if(p.n===e.n)p.x=!!e.on});
    }
    else if(e.t==='padd'){
      if(St.roster&&St.roster.teams[e.tm]){
        var ex=null;for(var k3 in St.roster.teams)St.roster.teams[k3].players.forEach(function(p){if(p.n===e.n)ex=p});
        if(ex)ex.x=false;else St.roster.teams[e.tm].players.push({n:e.n,u:'',role:'гость',r:'',g:true});
      }
    }
    else if(e.t==='teams'){c.a=e.a;c.b=e.b;if(c.left!==c.a&&c.left!==c.b)c.left=c.a}
    else if(e.t==='swap'){var sd0=sides(c);c.left=sd0.r}
    else if(e.t==='finish'){
      if(c.a===c.b)return;
      var sa=e.v?teamScore(St,c.a):c.la,sb=e.v?teamScore(St,c.b):c.lb,dr=sa===sb;
      if(dr&&!e.dr)return;
      snap('fin');
      var pts={},pm={},pl=[];
      for(var n in c.pts)if(c.pts[n]>0)pts[n]=c.pts[n];
      [c.a,c.b].forEach(function(k){var t=St.roster&&St.roster.teams[k];if(t)t.players.forEach(function(p){if(!p.x){pl.push(p.n);pm[p.n]=k}})});
      for(var n2 in pts)if(!pm[n2]){var tk=teamOf(St,n2);if(tk)pm[n2]=tk}
      var g={a:c.a,b:c.b,sa:sa,sb:sb,d:e.d,dr:dr,pts:pts,pm:pm,pl:pl,t0:c.t0,t1:ts};
      St.games.push(g);
      St.log.push({k:'fin',ts:ts,gi:St.games.length-1,a:c.a,b:c.b,sa:sa,sb:sb,dr:dr});
      St.lastFin=ts;
      var np=nextPair(St.games,g);
      /* команда, которая осталась, сохраняет свою сторону, вышедшая на поле третья занимает освободившуюся */
      var oldL=sides(c).l;
      St.cur={a:np.a,b:np.b,left:(oldL===np.a?np.a:np.b),pts:{},la:0,lb:0,t0:null,tm:newTm()};
    }
    else if(e.t==='undo'){
      var sn=snaps[snaps.length-1],cn=cutFor(St,dateOf(ts));
      if(sn&&sn.ts<=cn&&ts>cn)sn=null;   /* тренировка не отменяет игры самой встречи */
      if(sn){
        snaps.pop();
        var tmNow=c.tm,leftNow=c.left;
        St.games.length=sn.g;St.log.length=sn.ll;St.lastFin=sn.lf;St.cur=sn.cur;
        if(sn.k==='pt'){St.cur.tm=tmNow;St.cur.left=leftNow}
        else{var t0m=St.cur.tm;if(t0m.run){t0m.acc+=Math.max(0,sn.ts-t0m.since);t0m.run=false;t0m.since=null}}
      }
    }
    else if(e.t==='adj'){St.adj.push({k:e.k,n:e.n,d:e.d,ts:ts})}
    else if(e.t==='save'){if(St.saves[e.d]==null)St.saves[e.d]=ts}
    else if(e.t==='unsave'){delete St.saves[e.d]}
    else if(e.t==='roster'){St.roster=JSON.parse(JSON.stringify(e.r));for(var k2 in e.r.teams)St.names[k2]=e.r.teams[k2].name}
  });
  var tdate=today();
  St.games.forEach(function(g){g.off=g.t1<=cutFor(St,g.d)});
  St.log.forEach(function(x){x.off=x.ts<=cutFor(St,dateOf(x.ts))});
  St.adj.forEach(function(x){x.off=x.ts==null||x.ts<=cutFor(St,x.d)});
  St.games.forEach(function(g){winners(g).forEach(function(k){
    if(g.off){St.w[k]++;if(g.d===tdate)St.td[k]++}else if(g.d===tdate)St.trd[k]++;
  })});
  St.adj.forEach(function(x){if(x.off){St.w[x.k]+=x.n;if(x.d===tdate)St.td[x.k]+=x.n}});
  return St;
}

/* Протокол встречи за день: кто, когда и на какой минуте забил */
function protoHtml(St,d,offOnly){
  var gis={};
  St.log.forEach(function(x){if(dateOf(x.ts)===d&&(!offOnly||x.off))gis[x.gi]=1});
  St.games.forEach(function(g,i){if(g.d===d&&(!offOnly||g.off))gis[i]=1});
  var list=Object.keys(gis).map(Number).sort(function(a,b){return a-b});
  if(!list.length)return '<div class="mut">Записей пока нет</div>';
  return list.map(function(gi){
    var g=St.games[gi],no=1;
    for(var i=0;i<gi;i++)if(St.games[i].d===d&&(!offOnly||St.games[i].off))no++;
    var head=g?('Игра '+no+' · '+esc(St.names[g.a])+' '+g.sa+':'+g.sb+' '+esc(St.names[g.b])+(g.dr?' · ничья':'')+(g.off?'':' · <i style="font-style:normal;color:#FFB020">тренировка</i>')):('Игра '+no+' · идёт сейчас');
    var span=g&&g.t0!=null?' <span class="mut">'+hm(g.t0)+'–'+hm(g.t1)+'</span>':'';
    var rows=St.log.filter(function(x){return x.gi===gi}).map(function(x){
      if(x.k==='fin')return '<div class="lg fin"><span class="mn">'+hm(x.ts)+'</span><span>'+(x.dr?'Игра завершена: ничья, по очку каждой':'Игра завершена: победа '+esc(St.names[x.sa>x.sb?x.a:x.b]))+'</span><b>'+x.sa+':'+x.sb+'</b></div>';
      return '<div class="lg"><span class="mn">'+x.m+'′</span><span>'+(x.tm?dot(x.tm):'')+esc(x.p)+' '+(x.n>0?'+'+x.n:'−'+Math.abs(x.n))+(x.n<0?' <i>исправление</i>':'')+'</span><b>'+x.sa+':'+x.sb+'</b><small>'+hm(x.ts)+'</small></div>';
    }).join('');
    return '<div class="pg"><div class="ph">'+head+span+'</div>'+rows+'</div>';
  }).join('');
}
