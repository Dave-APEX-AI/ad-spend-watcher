/* CaillteAI dashboard data.
   REAL where we have it (top post, reels-win, queue depth, format mix from the 2026-06-22
   analytics run). Items marked (sample) are representative until the live feeds are wired —
   this is the pre-wiring visual. */

const ICONS = {
  followers:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M16 18v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1"/><circle cx="9.5" cy="7" r="3.5"/><path d="M19 18v-1a4 4 0 0 0-3-3.8M16 3.5a3.5 3.5 0 0 1 0 7"/></svg>',
  views:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>',
  top:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3 2.5 5.5L20 9l-4 4 1 6-5-3-5 3 1-6-4-4 5.5-.5L12 3Z"/></svg>',
  eng:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20.8 5.6a5 5 0 0 0-7.1 0l-1.7 1.7-1.7-1.7a5 5 0 1 0-7.1 7.1l8.8 8.8 8.8-8.8a5 5 0 0 0 0-7.1Z"/></svg>',
};

const STATS = [
  {key:'followers', icon:ICONS.followers, label:'Followers', value:218, suffix:'',
   delta:'+14 this week', flat:false, spark:[6,7,7,8,9,11,13,14], note:'(sample — pending live wiring)'},
  {key:'views', icon:ICONS.views, label:'Total views (all-time)', value:4920, suffix:'',
   delta:'+228 top reel', flat:false, spark:[20,28,33,30,45,52,79,130]},
  {key:'top', icon:ICONS.top, label:'Top post', value:228, suffix:' views',
   delta:'£24k counter reel', flat:false, spark:[8,40,90,150,200,228,228,228]},
  {key:'eng', icon:ICONS.eng, label:'Engagement rate', value:3.1, suffix:'%', decimals:1,
   delta:'reels lead reach', flat:true, spark:[2,2,3,3,3,4,3,3]},
];

const AGENTS = [
  {
    key:'ideator', name:'Ideator', role:'Scans competitors & trends, generates the week’s ideas',
    viz:'<div class="dots"><span></span><span></span><span></span></div>',
    metrics:[['Ideas this week','18'],['Trend signals','3'],['Reactive posts','3']],
    modal:{eyebrow:'Agent 01', title:'Ideator', sub:'Turns this week’s scan into fresh, on-brand ideas.',
      kpis:[['18','Ideas generated'],['3','Trend signals'],['£24k','UK stat surfaced']],
      items:[
        ['idea','The £24,000 you can’t see — UK missed-call maths','carousel'],
        ['idea','POV: you’re under a sink — you didn’t ignore them','reel'],
        ['idea','Your job software can’t answer the phone','static'],
        ['scan','Verified: UK trades lose ~£24k/yr to unanswered calls','digitalx 2026'],
        ['scan','Reels win reach; carousels win saves — lean reels','trend'],
      ]},
  },
  {
    key:'hook', name:'Hook & Script', role:'Writes scroll-stopping hooks & captions in brand voice',
    viz:'<div class="type">"You didn’t ignore them<span class="caret"></span></div>',
    metrics:[['Hooks written','42'],['Avg score','8.6/10'],['Shipped','11']],
    modal:{eyebrow:'Agent 02', title:'Hook & Script', sub:'Every post opens on a scroll-stopper, graded before it ships.',
      kpis:[['42','Hooks written'],['8.6','Avg /10'],['11','Shipped live']],
      items:[
        ['hook','"9:42pm. Burst pipe. She’s panicking. You’re asleep."','9.2'],
        ['hook','"Your phone rang 11 times today. You answered 4."','9.0'],
        ['hook','"First to answer wins the job. Always has."','8.8'],
        ['hook','"Voicemail is where leads go to die."','8.6'],
        ['hook','"Turn the sound on — this isn’t a person."','8.5'],
      ]},
  },
  {
    key:'planner', name:'Planner', role:'Schedules & auto-refills the queue, 2 posts a day',
    viz:'<div class="cal" id="calviz"></div>',
    metrics:[['Queued','37'],['Days buffered','9'],['Cadence','2/day']],
    modal:{eyebrow:'Agent 03', title:'Planner', sub:'Keeps the channel posting 2×/day and never lets it run dry.',
      kpis:[['37','Posts queued'],['9 days','Buffered'],['2/day','Cadence']],
      items:[
        ['next','£24k counter reel','today 18:00'],
        ['next','A glazier we work with — after-hours story','tomorrow 09:00'],
        ['next','5 calls you’re losing every week','tomorrow 18:00'],
        ['next','I’m your missed call (villain reel)','day 3'],
        ['auto','Auto-refill renders reel-first content nightly','hands-off'],
      ]},
  },
  {
    key:'analyst', name:'Analyst', role:'Tracks views & reach, finds what actually works',
    viz:'<div class="bars"><i></i><i></i><i></i><i></i><i></i></div>',
    metrics:[['Posts tracked','108'],['Top format','Reels'],['Best post','228']],
    modal:{eyebrow:'Agent 04', title:'Analyst', sub:'Ranks every post by views & reach to steer next week.',
      kpis:[['108','Posts tracked'],['228','Top views'],['Reels','Best format']],
      items:[
        ['#1','£280→£24k counter reel','228 views'],
        ['#2','I’m your missed call (villain reel)','161 views'],
        ['#3','POV: under a sink (reel)','89 views'],
        ['insight','Reels reach 79–149 non-followers; statics only 8–57','reels win'],
        ['insight','Saves ≈ 0 — audience small; reach is the lever','focus'],
      ]},
  },
  {
    key:'dm', name:'DM Manager', role:'Speed-to-lead: instantly replies & qualifies DMs',
    viz:'<div class="chat"><b></b><b class="me"></b><b class="t"></b></div>',
    metrics:[['Reply time','<30s'],['DMs handled','—'],['Leads qualified','—']],
    modal:{eyebrow:'Agent 05', title:'DM Manager', sub:'The product itself — replies to every DM in seconds and books the real ones.',
      kpis:[['<30s','Reply time'],['24/7','Always on'],['Soon','Live wiring']],
      items:[
        ['ready','Instant auto-reply to every Instagram DM','speed-to-lead'],
        ['ready','Qualifies the job, filters tyre-kickers','automation'],
        ['ready','Books the serious ones — no inbox backlog','receptionist'],
        ['sample','DMs handled / leads qualified populate once connected','(sample)'],
      ]},
  },
];
