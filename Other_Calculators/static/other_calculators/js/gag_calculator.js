let gaugeC=null, radarC=null, compareC=null, scoresC=null;
function ck(){return typeof Chart!=='undefined';}

document.addEventListener('DOMContentLoaded', function(){
    const form=document.getElementById('calculatorForm');
    const init=document.getElementById('initialState');
    const load=document.getElementById('loadingState');
    const err=document.getElementById('errorState');
    const res=document.getElementById('results');
    const card=document.getElementById('resultCard');

    const attrKeys = window.djangoContext.attrKeys || [];

    form.addEventListener('submit', async function(e){
        e.preventDefault();
        if(init) init.classList.add('hidden');
        if(res)  res.classList.add('hidden');
        if(err)  err.classList.add('hidden');
        if(load) load.classList.remove('hidden');

        const scores = {};
        attrKeys.forEach(k => {
            const el = document.getElementById(k);
            if(el) scores[k] = parseInt(el.value) || 5;
        });

        const btn=document.getElementById('calcBtnText');
        const orig=btn?btn.textContent:'';
        if(btn) btn.textContent=window.djangoContext.trans_Calculating_0;

        try {
            const r = await fetch(window.location.href, {
                method:'POST',
                headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value},
                body: JSON.stringify({scores})
            });
            const d = await r.json();
            if(load) load.classList.add('hidden');
            if(btn) btn.textContent=orig;
            if(!d.success){if(err){document.getElementById('errorMessage').textContent=d.error||'Error';err.classList.remove('hidden');}return;}
            show(d);
        } catch(ex){
            if(load) load.classList.add('hidden');
            if(btn) btn.textContent=orig;
            if(err){document.getElementById('errorMessage').textContent=window.djangoContext.trans_Networkerror_1;err.classList.remove('hidden');}
        }
    });

    function show(d){
        try {
            const g=d.grade;
            document.getElementById('gradeEmoji').textContent=g.emoji;
            document.getElementById('gradeValue').textContent=g.grade;
            document.getElementById('gradeLabel').textContent=g.label;
            document.getElementById('overallScore').textContent=d.overall+' / 10';
            document.getElementById('percentileText').textContent=window.djangoContext.trans_Top_2 + " "+Math.round(100-d.percentile)+'%';
            document.getElementById('gradeBadgeText').textContent=g.grade+' — '+g.label;
            document.getElementById('gradeDesc').textContent=g.description;

            const bg=document.getElementById('gradeBadge');
            if(bg&&d.color_info) bg.className='inline-block mt-3 px-4 py-2 rounded-full text-sm font-semibold shadow-md border-2 '+d.color_info.tailwind;

            const grads={green:'from-green-500 to-green-600',blue:'from-blue-500 to-blue-600',yellow:'from-yellow-400 to-yellow-500',orange:'from-orange-500 to-orange-600',red:'from-red-500 to-red-600',purple:'from-purple-500 to-purple-600'};
            if(card) card.className='bg-gradient-to-br rounded-xl p-6 sm:p-8 shadow-xl text-white '+(grads[g.color]||'from-pink-500 to-rose-500');

            document.getElementById('sPhysical').textContent=d.physical_avg;
            document.getElementById('sPersonality').textContent=d.personality_avg;
            document.getElementById('sOverall').textContent=d.overall;

            /* Charts */
            if(d.chart_data&&ck()){
                if(d.chart_data.gauge_chart) mkGauge(d.chart_data.gauge_chart);
                if(d.chart_data.compare_chart) mkCompare(d.chart_data.compare_chart);
                if(d.chart_data.radar_chart) mkRadar(d.chart_data.radar_chart);
                if(d.chart_data.scores_chart) mkScores(d.chart_data.scores_chart);
            }
            if(res){res.classList.remove('hidden');setTimeout(()=>res.scrollIntoView({behavior:'smooth',block:'nearest'}),100);}
        }catch(e){console.error(e);}
    }

    function mkGauge(cd){
        const ctx=document.getElementById('gaugeChart');if(!ctx||!ck())return;if(gaugeC)gaugeC.destroy();
        const ct=cd.center_text;
        try{gaugeC=new Chart(ctx,{type:cd.type,data:cd.data,options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},animation:{animateRotate:true,duration:1500}},plugins:[{id:'gc',afterDraw(ch){const c=ch.ctx;const x=ch.chartArea.left+(ch.chartArea.right-ch.chartArea.left)/2;const y=ch.chartArea.top+(ch.chartArea.bottom-ch.chartArea.top)/2;c.save();c.font='bold 36px Inter,Arial';c.fillStyle=ct.color;c.textAlign='center';c.textBaseline='middle';c.fillText(ct.value,x,y-12);c.font='bold 20px Inter,Arial';c.fillText(ct.label,x,y+20);c.restore();}}]});}catch(e){console.error(e);}
    }

    function mkCompare(cd){
        const ctx=document.getElementById('compareChart');if(!ctx||!ck())return;if(compareC)compareC.destroy();
        try{compareC=new Chart(ctx,{type:cd.type,data:cd.data,options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.parsed.y.toFixed(1)} / 10`}}},scales:{y:{beginAtZero:true,max:10,grid:{color:'#f3f4f6'},ticks:{font:{size:11}}},x:{grid:{display:false},ticks:{font:{size:12,weight:'bold'}}}},animation:{duration:1500}}});}catch(e){console.error(e);}
    }

    function mkRadar(cd){
        const ctx=document.getElementById('radarChart');if(!ctx||!ck())return;if(radarC)radarC.destroy();
        try{radarC=new Chart(ctx,{type:cd.type,data:cd.data,options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{r:{beginAtZero:true,max:10,ticks:{stepSize:2,backdropColor:'transparent',font:{size:10}},grid:{color:'rgba(0,0,0,0.05)'},pointLabels:{font:{size:10,weight:'bold'}}}},animation:{duration:1500}}});}catch(e){console.error(e);}
    }

    function mkScores(cd){
        const ctx=document.getElementById('scoresChart');if(!ctx||!ck())return;if(scoresC)scoresC.destroy();
        try{scoresC=new Chart(ctx,{type:cd.type,data:cd.data,options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.parsed.x} / 10`}}},scales:{x:{beginAtZero:true,max:10,grid:{color:'#f3f4f6'},ticks:{font:{size:11}}},y:{grid:{display:false},ticks:{font:{size:10,weight:'bold'}}}},animation:{duration:1500}}});}catch(e){console.error(e);}
    }
});