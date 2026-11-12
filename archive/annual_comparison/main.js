const COLORS = {historical: '#637582', ssp126: '#168b82', ssp245: '#dc942c', ssp585: '#c75064'};
const LABELS = {historical: 'Historical', ssp126: 'SSP1-2.6', ssp245: 'SSP2-4.5', ssp585: 'SSP5-8.5'};
const state = {region: 'Global', start: 1995, end: 2100, scenarios: ['ssp126', 'ssp245', 'ssp585'], year: 2100};
const fmt = d3.format('+.2f');
let rows, meta, inspect;

Promise.all([d3.json('data/temperature.json'), d3.json('data/metadata.json')]).then(([data, metadata]) => {
  rows = data;
  meta = metadata;
  d3.select('#model-tag').text(`CMIP6 / ${meta.model}`);
  d3.select('#model-details').text(`${meta.model} · member ${meta.member} · native grid ${meta.grid}`);
  d3.select('#region').selectAll('option').data(meta.regions).join('option').attr('value', d => d.name).text(d => d.name);
  d3.select('#region').on('change', function() {state.region = this.value; render();});
  d3.selectAll('input[name=scenario]').on('change', () => {
    state.scenarios = [...document.querySelectorAll('input[name=scenario]:checked')].map(d => d.value);
    render();
  });
  d3.select('#start-year').on('input', function() {
    state.start = Math.min(+this.value, state.end - 1);
    render();
  });
  d3.select('#end-year').on('input', function() {
    state.end = Math.max(+this.value, state.start + 1);
    render();
  });
  d3.select('#reset').on('click', () => {
    Object.assign(state, {region: 'Global', start: 1995, end: 2100, scenarios: ['ssp126','ssp245','ssp585'], year: 2100});
    d3.select('#region').property('value', state.region);
    d3.selectAll('input[name=scenario]').property('checked', true);
    render();
  });
  new ResizeObserver(() => render()).observe(document.querySelector('#chart'));
  render();
}).catch(error => {
  document.querySelector('#summary').textContent = 'Data could not be loaded.';
  d3.select('#error').property('hidden', false).text(`Run this project through an HTTP server. ${error.message}`);
});

function render() {
  if (!rows) return;
  const region = meta.regions.find(d => d.name === state.region);
  d3.select('#bounds').text(`${region.south}° to ${region.north}° latitude · land + ocean`);
  ['start', 'end'].forEach(key => {
    d3.select(`#${key}-year`).property('value', state[key]);
    d3.select(`#${key}-output`).text(state[key]);
  });
  d3.select('#tooltip').property('hidden', true);
  const active = ['historical', ...state.scenarios];
  const data = rows.filter(d => d.region === state.region && d.year >= state.start && d.year <= state.end && active.includes(d.scenario));
  const groups = d3.groups(data, d => d.scenario).map(([key, values]) => ({key, values}));
  const width = Math.max(300, document.querySelector('#chart').clientWidth);
  const height = width < 500 ? 310 : 390;
  const m = {top: 20, right: 20, bottom: 35, left: 45};
  const x = d3.scaleLinear().domain([state.start, state.end]).range([m.left, width - m.right]);
  const extent = d3.extent(data, d => d.anomaly);
  const y = d3.scaleLinear().domain(data.length ? [Math.min(-.3, extent[0] - .2), Math.max(.5, extent[1] + .3)] : [-.5, 1]).nice().range([height - m.bottom, m.top]);
  const svg = d3.select('#chart').selectAll('svg').data([null]).join('svg').attr('viewBox', `0 0 ${width} ${height}`).attr('tabindex', 0).attr('role', 'img').attr('aria-label', `${state.region}, annual temperature anomaly in degrees Celsius, ${state.start} to ${state.end}. Use left and right arrows to inspect.`);
  svg.selectAll('title').data([null]).join('title').text(`${state.region}: temperature change relative to 1995–2014`);
  svg.selectAll('.grid').data([null]).join('g').attr('class','grid').attr('transform',`translate(${m.left},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(width-m.left-m.right)).tickFormat(''));
  svg.selectAll('.x-axis').data([null]).join('g').attr('class','axis x-axis').attr('transform',`translate(0,${height-m.bottom})`).call(d3.axisBottom(x).ticks(width < 500 ? 4 : 8).tickFormat(d3.format('d')));
  svg.selectAll('.y-axis').data([null]).join('g').attr('class','axis y-axis').attr('transform',`translate(${m.left},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d > 0 ? '+' : ''}${d}`));
  svg.selectAll('.zero').data([null]).join('line').attr('class','zero').attr('x1',m.left).attr('x2',width-m.right).attr('y1',y(0)).attr('y2',y(0)).attr('stroke','#b4c6bf').attr('stroke-dasharray','3 4');
  const line = d3.line().x(d => x(d.year)).y(d => y(d.anomaly));
  svg.selectAll('.series').data(groups, d => d.key).join('path').attr('class','series').attr('data-scenario',d => d.key).attr('stroke',d => COLORS[d.key]).attr('d',d => line(d.values)).interrupt().attr('opacity',.65).transition().duration(matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 180).attr('opacity',1);
  svg.selectAll('.year-label').data([null]).join('text').attr('class','year-label').attr('x',width-m.right).attr('y',height-2).attr('text-anchor','end').attr('fill','#687b7d').attr('font-size',10).text('Year');
  const cursor = svg.selectAll('.cursor').data([null]).join('g').attr('class','cursor').attr('pointer-events','none').style('display','none');
  const overlay = svg.selectAll('.overlay').data([null]).join('rect').attr('class','overlay').attr('x',m.left).attr('y',m.top).attr('width',width-m.left-m.right).attr('height',height-m.top-m.bottom).attr('fill','transparent');
  cursor.raise();
  inspect = (year, pointer = null) => {
    state.year = Math.max(state.start, Math.min(state.end, Math.round(year)));
    const points = data.filter(d => d.year === state.year);
    cursor.style('display',null);
    cursor.selectAll('line').data([state.year]).join('line').attr('x1',d => x(d)).attr('x2',d => x(d)).attr('y1',m.top).attr('y2',height-m.bottom).attr('stroke','#8ca39c').attr('stroke-dasharray','3 3');
    cursor.selectAll('circle').data(points,d => d.scenario).join('circle').attr('cx',d => x(d.year)).attr('cy',d => y(d.anomaly)).attr('r',4).attr('fill',d => COLORS[d.scenario]).attr('stroke','white').attr('stroke-width',1.5);
    const tip = d3.select('#tooltip').property('hidden',false);
    tip.selectAll('*').remove();
    tip.append('b').text(`${state.region} · ${state.year}`);
    points.forEach(d => tip.append('span').text(`${LABELS[d.scenario]}: ${fmt(d.anomaly)} °C`));
    if (!points.length) tip.append('span').text('No selected projection in this year.');
    const box = document.querySelector('.explorer').getBoundingClientRect();
    const chartBox = document.querySelector('#chart').getBoundingClientRect();
    const left = pointer ? pointer[0] + chartBox.left - box.left + 12 : m.left + chartBox.left - box.left;
    tip.style('left',`${Math.max(8,Math.min(left,box.width-tip.node().offsetWidth-12))}px`).style('top',`${chartBox.top-box.top+20}px`);
  };
  overlay.on('pointermove', event => {const p=d3.pointer(event,svg.node());inspect(x.invert(p[0]),p);}).on('pointerleave',() => {cursor.style('display','none');d3.select('#tooltip').property('hidden',true);});
  svg.on('keydown',event => {
    if (['ArrowLeft','ArrowRight'].includes(event.key)) {
      event.preventDefault(); inspect(state.year+(event.key === 'ArrowRight' ? 1 : -1));
      d3.select('#tooltip').attr('aria-live','polite');
    }
  }).on('blur',() => {cursor.style('display','none');d3.select('#tooltip').property('hidden',true).attr('aria-live','off');});
  d3.select('#empty').property('hidden',state.scenarios.length > 0);
  updateSummary(data);
}

function updateSummary(data) {
  const future = data.filter(d => d.scenario !== 'historical');
  let text;
  if (!state.scenarios.length) text = 'No future scenarios selected. Select one or more pathways to explore the projections.';
  else if (!future.length) text = 'This period contains historical simulations only. Extend the end year to 2015 or later to see scenario projections.';
  else {
    const years = d3.sort([...new Set(future.map(d => d.year))]);
    const end = years.at(-1);
    const start = Math.max(years[0], end-19);
    const averages = state.scenarios.map(s => ({scenario:s, value:d3.mean(future.filter(d => d.scenario === s && d.year >= start),d => d.anomaly)}));
    const detail = averages.map(d => `${LABELS[d.scenario]}: ${fmt(d.value)} °C`).join('; ');
    text = `${state.region}, ${start}–${end} mean (${end-start+1} year${end===start ? '' : 's'}): ${detail}.`;
    if (averages.length > 1) {
      const sorted = d3.sort(averages,d => d.value);
      text += ` The gap between ${LABELS[sorted.at(-1).scenario]} and ${LABELS[sorted[0].scenario]} is ${(sorted.at(-1).value-sorted[0].value).toFixed(2)} °C.`;
    }
    text += ' Relative to 1995–2014; one model realization.';
  }
  d3.select('#summary').text(text);
}
