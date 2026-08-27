// Sample Mock Data Generation
function generateMockData(count) {
    const data = [];
    for (let i = 0; i < count; i++) {
        // MZR & Main Sequence correlation
        const mass = 8.0 + Math.random() * 3.5; // 8.0 to 11.5
        const isSF = Math.random() > 0.3; // 70% star forming
        
        let sfr;
        if (isSF) {
            sfr = mass - 10 + (Math.random() - 0.5) * 0.8; // Main sequence
        } else {
            sfr = mass - 12 + (Math.random() - 0.5) * 1.0; // Quenched
        }

        const oh = 7.5 + (mass - 8) * 0.3 + (Math.random() - 0.5) * 0.2; // MZR
        
        let bptClass;
        let logNiiHa, logOiiiHb;
        if (isSF) {
            logNiiHa = -1.5 + Math.random() * 1.0;
            logOiiiHb = 0.61 / (logNiiHa - 0.05) + 1.3 + (Math.random() - 0.5) * 0.3;
            bptClass = 'Star Forming';
        } else {
            logNiiHa = -0.2 + Math.random() * 0.6;
            logOiiiHb = -0.5 + Math.random() * 1.5;
            bptClass = logOiiiHb > 0.5 ? 'Seyfert' : 'LINER';
        }

        const cluster = isSF ? (mass > 10 ? 'C1 (Massive SF)' : 'C2 (Dwarf SF)') : 'C3 (Quenched)';
        
        data.push({
            id: i,
            mass: mass,
            sfr: sfr,
            oh: oh,
            logNiiHa: logNiiHa,
            logOiiiHb: logOiiiHb,
            u_g: (mass - 8) * 0.3 + (Math.random()*0.5),
            bpt_class: bptClass,
            cluster: cluster
        });
    }
    return data;
}

const galaxyData = generateMockData(300);

const variables = {
    'mass': { label: '항성 질량 (log M/M_sun)', data: galaxyData.map(d => d.mass) },
    'sfr': { label: '별 생성률 (log SFR)', data: galaxyData.map(d => d.sfr) },
    'oh': { label: '금속성 (12+log(O/H))', data: galaxyData.map(d => d.oh) },
    'logNiiHa': { label: 'log([NII]/Hα)', data: galaxyData.map(d => d.logNiiHa) },
    'logOiiiHb': { label: 'log([OIII]/Hβ)', data: galaxyData.map(d => d.logOiiiHb) },
    'u_g': { label: 'u-g 색지수', data: galaxyData.map(d => d.u_g) }
};

const categoricals = {
    'bpt_class': { label: 'BPT 분류', data: galaxyData.map(d => d.bpt_class) },
    'cluster': { label: '진화 군집', data: galaxyData.map(d => d.cluster) }
};

// UI Elements
const xSelect = document.getElementById('x-var');
const ySelect = document.getElementById('y-var');
const cSelect = document.getElementById('color-var');
const plotDiv = document.getElementById('plot-container');

// Init Selects
Object.entries(variables).forEach(([key, val]) => {
    xSelect.add(new Option(val.label, key));
    ySelect.add(new Option(val.label, key));
    cSelect.add(new Option(val.label, key));
});
Object.entries(categoricals).forEach(([key, val]) => {
    cSelect.add(new Option(val.label, key));
});

ySelect.value = 'sfr';
cSelect.value = 'bpt_class';

function drawPlot() {
    const xKey = xSelect.value;
    const yKey = ySelect.value;
    const cKey = cSelect.value;

    let trace = {
        x: variables[xKey] ? variables[xKey].data : categoricals[xKey].data,
        y: variables[yKey] ? variables[yKey].data : categoricals[yKey].data,
        mode: 'markers',
        type: 'scatter',
        marker: { size: 6, opacity: 0.8 },
        text: galaxyData.map(d => `Mass: ${d.mass.toFixed(2)}<br>BPT: ${d.bpt_class}`)
    };

    if (categoricals[cKey]) {
        // Group by category
        const groups = [...new Set(categoricals[cKey].data)];
        const traces = groups.map(g => {
            const indices = categoricals[cKey].data.map((v, i) => v === g ? i : -1).filter(i => i !== -1);
            return {
                x: indices.map(i => trace.x[i]),
                y: indices.map(i => trace.y[i]),
                mode: 'markers',
                name: g,
                marker: { size: 7 }
            };
        });
        trace = traces;
    } else {
        trace.marker.color = variables[cKey].data;
        trace.marker.colorscale = 'Viridis';
        trace.marker.showscale = true;
        trace = [trace];
    }

    const layout = {
        title: `${variables[yKey].label} vs ${variables[xKey].label}`,
        xaxis: { title: variables[xKey].label, gridcolor: '#333' },
        yaxis: { title: variables[yKey].label, gridcolor: '#333' },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e0e6ed' },
        margin: { t: 50, b: 50, l: 60, r: 20 },
        hovermode: 'closest'
    };

    Plotly.newPlot(plotDiv, trace, layout, {responsive: true});
}

xSelect.addEventListener('change', drawPlot);
ySelect.addEventListener('change', drawPlot);
cSelect.addEventListener('change', drawPlot);

// Presets
document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const p = e.target.dataset.preset;
        if(p === 'main_sequence') { xSelect.value='mass'; ySelect.value='sfr'; cSelect.value='cluster'; }
        else if(p === 'mzr') { xSelect.value='mass'; ySelect.value='oh'; cSelect.value='sfr'; }
        else if(p === 'bpt') { xSelect.value='logNiiHa'; ySelect.value='logOiiiHb'; cSelect.value='bpt_class'; }
        else if(p === 'color_mass') { xSelect.value='mass'; ySelect.value='u_g'; cSelect.value='bpt_class'; }
        drawPlot();
    });
});

drawPlot();

// Tabs Logic
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        btn.classList.add('active');
        document.getElementById(btn.dataset.tab).classList.add('active');
        
        if(btn.dataset.tab === 'explore') drawPlot();
    });
});

// Validate Logic
document.getElementById('validate-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const ha = parseFloat(document.getElementById('ha-flux').value);
    const hb = parseFloat(document.getElementById('hb-flux').value);
    const oiii = parseFloat(document.getElementById('oiii-flux').value);
    const nii = parseFloat(document.getElementById('nii-flux').value);

    // Calc ratios
    const logNiiHa = Math.log10(nii/ha);
    const logOiiiHb = Math.log10(oiii/hb);
    
    // BPT Kauffmann 2003 line: y = 0.61 / (x - 0.05) + 1.3
    let bpt = "Unknown";
    if (logNiiHa >= 0.05) {
        bpt = logOiiiHb > 0.5 ? "AGN (Seyfert)" : "LINER";
    } else {
        const kauff = 0.61 / (logNiiHa - 0.05) + 1.3;
        bpt = logOiiiHb < kauff ? "별생성 (Star-forming)" : "AGN/Composite";
    }

    // Dust (Balmer Decrement) intrinsic Ha/Hb is ~2.86
    const bd = ha/hb;
    const ebv = bd > 2.86 ? (1.086 * Math.log(bd/2.86) / 1.16).toFixed(3) : 0.0;

    // Metallicity (N2 index calibration approx)
    const oh_est = (8.90 + 0.57 * logNiiHa).toFixed(2);

    document.getElementById('res-bpt').textContent = bpt;
    document.getElementById('res-dust').textContent = ebv;
    document.getElementById('res-metallicity').textContent = oh_est;
    document.getElementById('res-cluster').textContent = (bpt.includes("별생성")) ? "Active SF Cluster" : "Quenched / AGN Cluster";
    
    document.getElementById('val-result').classList.remove('hidden');

    // Mini Plot
    const trace = {
        x: variables['logNiiHa'].data,
        y: variables['logOiiiHb'].data,
        mode: 'markers',
        type: 'scatter',
        marker: { size: 3, color: '#333', opacity: 0.3 },
        name: 'Background'
    };
    
    const target = {
        x: [logNiiHa], y: [logOiiiHb], mode: 'markers', type: 'scatter',
        marker: { size: 12, color: '#FF7043', symbol: 'star' },
        name: 'Target Galaxy'
    };

    const layout = {
        title: 'BPT Location',
        xaxis: { title: 'log([NII]/Hα)', gridcolor: '#333', range: [-2, 1] },
        yaxis: { title: 'log([OIII]/Hβ)', gridcolor: '#333', range: [-1.5, 1.5] },
        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e0e6ed' },
        margin: { t: 30, b: 40, l: 40, r: 20 },
        showlegend: false
    };

    Plotly.newPlot('val-plot', [trace, target], layout, {responsive: true});
});
