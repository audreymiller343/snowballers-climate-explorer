const COLORS = {historical: '#637582', ssp245: '#dc942c', ssp585: '#c75064'};
const LABELS = {historical: 'Historical', ssp245: 'SSP2-4.5', ssp585: 'SSP5-8.5'};
const SEASONS = {DJF: 'Winter', JJA: 'Summer', gap: 'Winter − summer anomaly'};
const defaults = {region: 'North America sector', start: 2015, end: 2100, scenarios: ['ssp245', 'ssp585'], measure: 'anomaly', year: 2100};
const state = {...defaults};
const fmt = d3.format('+.2f');
const rateFmt = d3.format('+.3f');
let rows, meta;

Promise.all([d3.json('data/temperature.json'), d3.json('data/metadata.json')]).then(([data, metadata]) => {
  rows = data;
  meta = metadata;
  d3.select('#model-tag').text(`CMIP6 / ${meta.model}`);
  d3.select('#model-details').text(`${meta.model} · member ${meta.member} · grid ${meta.grid}`);
  d3.select('#region').selectAll('option').data(meta.regions).join('option').attr('value', d => d.name).text(d => d.name);
  d3.select('#region').on('change', function() {state.region = this.value; render();});
  d3.select('#measure').on('change', function() {state.measure = this.value; render();});
  d3.selectAll('input[name=scenario]').on('change', () => {
    state.scenarios = [...document.querySelectorAll('input[name=scenario]:checked')].map(d => d.value);
    render();
  });
  d3.select('#start-year').on('input', function() {state.start = Math.min(+this.value, state.end - 1); render();});
  d3.select('#end-year').on('input', function() {state.end = Math.max(+this.value, state.start + 1); render();});
  d3.select('#reset').on('click', () => {
    Object.assign(state, defaults, {scenarios: [...defaults.scenarios]});
    d3.select('#region').property('value', state.region);
    d3.select('#measure').property('value', state.measure);
    d3.selectAll('input[name=scenario]').property('checked', true);
    render();
  });
  new ResizeObserver(render).observe(document.querySelector('#chart'));
  render();
}).catch(error => {
  d3.select('#summary').text('Seasonal data could not be loaded.');
  d3.select('#error').property('hidden', false).text(`Run this project through an HTTP server. ${error.message}`);
});

function paired(data) {
  return d3.groups(data, d => `${d.scenario}:${d.year}`).map(([, values]) => {
    const winter = values.find(d => d.season === 'DJF');
    const summer = values.find(d => d.season === 'JJA');
    return winter && summer ? {...winter, season: 'gap', anomaly: winter.anomaly - summer.anomaly} : null;
  }).filter(Boolean);
}

function slope(values) {
  const xMean = d3.mean(values, d => d.year);
  const yMean = d3.mean(values, d => d.anomaly);
  return 10 * d3.sum(values, d => (d.year - xMean) * (d.anomaly - yMean)) / d3.sum(values, d => (d.year - xMean) ** 2);
}

function render() {
  if (!rows) return;
  const region = meta.regions.find(d => d.name === state.region);
  d3.select('#bounds').text(region.description);
  ['start', 'end'].forEach(key => {
    d3.select(`#${key}-year`).property('value', state[key]);
    d3.select(`#${key}-output`).text(state[key]);
  });
  d3.select('#tooltip').property('hidden', true);
  const active = ['historical', ...state.scenarios];
  const original = rows.filter(d => d.region === state.region && d.year >= state.start && d.year <= state.end && active.includes(d.scenario));
  const data = state.measure === 'gap' ? paired(original) : original;
  d3.select('#chart-description').text(state.measure === 'gap' ? 'Winter − summer warming anomaly · °C' : 'Seasonal temperature anomaly · °C');
  d3.select('.season-legend').style('visibility', state.measure === 'gap' ? 'hidden' : 'visible');
  const groups = d3.groups(data, d => `${d.scenario}:${d.season}`).map(([key, values]) => ({key, scenario: values[0].scenario, season: values[0].season, values: d3.sort(values, d => d.year)}));
  const width = Math.max(280, document.querySelector('#chart').clientWidth);
  const height = width < 500 ? 310 : 390;
  const m = {top: 46, right: 20, bottom: 35, left: 45};
  const x = d3.scaleLinear().domain([state.start, state.end]).range([m.left, width - m.right]);
  const extent = d3.extent(data, d => d.anomaly);
  const y = d3.scaleLinear().domain(data.length ? [Math.min(-.3, extent[0] - .2), Math.max(.5, extent[1] + .3)] : [-.5, 1]).nice().range([height - m.bottom, m.top]);
  const svg = d3.select('#chart').selectAll('svg').data([null]).join('svg').attr('viewBox', `0 0 ${width} ${height}`).attr('tabindex', 0).attr('role', 'img').attr('aria-label', `${state.region}, ${state.measure === 'gap' ? 'winter minus summer anomaly' : 'seasonal temperature anomaly'} in degrees Celsius, ${state.start} to ${state.end}. Left and right arrows inspect season-years.`);
  svg.selectAll('title').data([null]).join('title').text(`${state.region}: seasonal warming relative to separate 1995–2014 baselines`);
  svg.selectAll('.grid').data([null]).join('g').attr('class', 'grid').attr('transform', `translate(${m.left},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(width-m.left-m.right)).tickFormat(''));
  svg.selectAll('.x-axis').data([null]).join('g').attr('class', 'axis x-axis').attr('transform', `translate(0,${height-m.bottom})`).call(d3.axisBottom(x).ticks(width < 500 ? 4 : 8).tickFormat(d3.format('d')));
  svg.selectAll('.y-axis').data([null]).join('g').attr('class', 'axis y-axis').attr('transform', `translate(${m.left},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d > 0 ? '+' : ''}${d}`));
  svg.selectAll('.zero').data([null]).join('line').attr('class', 'zero').attr('x1', m.left).attr('x2', width-m.right).attr('y1', y(0)).attr('y2', y(0)).attr('stroke', '#b4c6bf').attr('stroke-dasharray', '3 4');
  // The experiments meet between the last historical and first projected season-year.
  const boundary = svg.selectAll('.experiment-boundary').data(state.start <= 2014 && state.end >= 2015 ? [2014.5] : []).join('g').attr('class', 'experiment-boundary').attr('pointer-events', 'none');
  boundary.selectAll('line').data(d => [d]).join('line').attr('x1', x).attr('x2', x).attr('y1', m.top).attr('y2', height-m.bottom).attr('stroke', '#526c72').attr('stroke-width', 1.5).attr('stroke-dasharray', '5 4');
  boundary.selectAll('text').data(d => [d]).join('text').attr('x', d => Math.max(m.left, Math.min(x(d), width-m.right-260))).attr('y', 16).attr('fill', '#203c42').attr('font-size', width < 500 ? 9 : 11).text(width < 500 ? 'Historical ≤2014 | Projections ≥2015' : 'Historical ends 2014 | Projections start 2015');
  const line = d3.line().x(d => x(d.year)).y(d => y(d.anomaly));
  svg.selectAll('.series').data(groups, d => d.key).join('path').attr('class', 'series').attr('data-scenario', d => d.scenario).attr('data-season', d => d.season).attr('stroke', d => COLORS[d.scenario]).attr('stroke-dasharray', d => d.season === 'JJA' ? '7 5' : null).attr('d', d => line(d.values)).interrupt().attr('opacity', .7).transition().duration(matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 180).attr('opacity', 1);
  svg.selectAll('.year-label').data([null]).join('text').attr('class', 'year-label').attr('x', width-m.right).attr('y', height-2).attr('text-anchor', 'end').attr('fill', '#687b7d').attr('font-size', 10).text('Season-year');
  const cursor = svg.selectAll('.cursor').data([null]).join('g').attr('class', 'cursor').attr('pointer-events', 'none').style('display', 'none');
  const overlay = svg.selectAll('.overlay').data([null]).join('rect').attr('class', 'overlay').attr('x', m.left).attr('y', m.top).attr('width', width-m.left-m.right).attr('height', height-m.top-m.bottom).attr('fill', 'transparent');
  overlay.raise();
  cursor.raise();
  const inspect = (year, pointer = null) => {
    state.year = Math.max(state.start, Math.min(state.end, Math.round(year)));
    const points = data.filter(d => d.year === state.year);
    const nearest = pointer && points.length ? d3.least(points, d => Math.abs(y(d.anomaly)-pointer[1])) : null;
    const highlighted = nearest && Math.abs(y(nearest.anomaly)-pointer[1]) <= 24 ? nearest : null;
    svg.selectAll('.series').attr('stroke-width', d => highlighted && d.scenario === highlighted.scenario && d.season === highlighted.season ? 4 : 2.4);

    cursor.style('display', null);
    cursor.selectAll('line').data([state.year]).join('line').attr('x1', d => x(d)).attr('x2', d => x(d)).attr('y1', m.top).attr('y2', height-m.bottom).attr('stroke', '#8ca39c').attr('stroke-dasharray', '3 3');
    cursor.selectAll('circle').data(points, d => `${d.scenario}:${d.season}`).join('circle').attr('cx', d => x(d.year)).attr('cy', d => y(d.anomaly)).attr('r', 4).attr('fill', d => COLORS[d.scenario]).attr('stroke', 'white').attr('stroke-width', 1.5);
    const tip = d3.select('#tooltip').property('hidden', false);
    tip.selectAll('*').remove();
    tip.append('b').text(`${state.region} · ${state.year}`);
    points.forEach(d => tip.append('span').text(`${LABELS[d.scenario]} · ${SEASONS[d.season]}: ${fmt(d.anomaly)} °C`));
    if (highlighted) {
      tip.append('b').text(`Highlighted: ${LABELS[highlighted.scenario]} · ${SEASONS[highlighted.season]}`);
      tip.append('span').text(`${highlighted.scenario === 'historical' ? 'Historical simulation' : 'Future projection'} · ${meta.model}`);
      tip.append('span').text('Relative to each season’s 1995–2014 average; not absolute temperature.');
      if (highlighted.season === 'gap') {
        original.filter(d => d.year === state.year && d.scenario === highlighted.scenario).forEach(d => tip.append('span').text(`${SEASONS[d.season]} anomaly: ${fmt(d.anomaly)} °C`));
      } else {
        const previous = rows.find(d => d.region === state.region && d.scenario === highlighted.scenario && d.season === highlighted.season && d.year === state.year-1);
        if (previous) tip.append('span').text(`Change from previous season-year: ${fmt(highlighted.anomaly-previous.anomaly)} °C (not a long-term trend)`);
      }
    }
    if (!points.length) tip.append('span').text('No selected projection in this season-year.');
    const box = document.querySelector('.explorer').getBoundingClientRect();
    const chartBox = document.querySelector('#chart').getBoundingClientRect();
    const left = pointer ? pointer[0]+chartBox.left-box.left+12 : m.left+chartBox.left-box.left;
    tip.style('left', `${Math.max(8, Math.min(left, box.width-tip.node().offsetWidth-12))}px`).style('top', `${chartBox.top-box.top+20}px`);
  };
  overlay.on('pointermove', event => {const p = d3.pointer(event, svg.node()); inspect(x.invert(p[0]), p);}).on('pointerleave', () => {cursor.style('display', 'none'); svg.selectAll('.series').attr('stroke-width', 2.4); d3.select('#tooltip').property('hidden', true);});
  svg.on('keydown', event => {
    if (['ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault(); inspect(state.year+(event.key === 'ArrowRight' ? 1 : -1));
      d3.select('#tooltip').attr('aria-live', 'polite');
    }
  }).on('blur', () => {cursor.style('display', 'none'); svg.selectAll('.series').attr('stroke-width', 2.4); d3.select('#tooltip').property('hidden', true).attr('aria-live', 'off');});
  d3.select('#empty').property('hidden', state.scenarios.length > 0);
  updateSummary(original);
}

function updateSummary(data) {
  const future = data.filter(d => d.scenario !== 'historical');
  const cards = d3.select('#rate-cards');
  cards.selectAll('*').remove();
  let text;
  if (!state.scenarios.length) text = 'No future scenarios selected. Choose a pathway to compare winter and summer.';
  else if (!future.length) text = 'This window contains historical simulations only. Extend the end year to 2015 or later to compare future seasons.';
  else {
    const years = d3.sort([...new Set(future.map(d => d.year))]);
    const first = years[0], last = years.at(-1), periodStart = Math.max(first, last-19);
    const details = [];
    for (const scenario of state.scenarios) {
      const winter = future.filter(d => d.scenario === scenario && d.season === 'DJF');
      const summer = future.filter(d => d.scenario === scenario && d.season === 'JJA');
      const matching = winter.length === summer.length && winter.every((d, i) => d.year === summer[i].year);
      if (!matching) throw new Error('Season-year mismatch prevents comparison.');
      const winterMean = d3.mean(winter.filter(d => d.year >= periodStart), d => d.anomaly);
      const summerMean = d3.mean(summer.filter(d => d.year >= periodStart), d => d.anomaly);
      details.push(`${LABELS[scenario]}: winter ${fmt(winterMean)} °C, summer ${fmt(summerMean)} °C, difference ${fmt(winterMean-summerMean)} °C`);
      const card = cards.append('article').attr('class', 'rate-card').attr('data-scenario', scenario).style('--scenario', COLORS[scenario]);
      card.append('h4').text(LABELS[scenario]);
      if (years.length < 20) {
        card.append('p').text(`Only ${years.length} complete future years selected. Select at least 20 for a trend comparison.`);
      } else {
        const winterRate = slope(winter), summerRate = slope(summer), difference = winterRate-summerRate;
        card.append('p').attr('class', 'rate-period').text(`${first}–${last} · ${years.length} seasons per trend`);
        const values = card.append('div').attr('class', 'rate-values');
        values.append('p').text(`Winter ${rateFmt(winterRate)}`);
        values.append('p').text(`Summer ${rateFmt(summerRate)}`);
        card.append('strong').attr('class', 'rate-difference').text(`Winter − summer rate: ${rateFmt(difference)} °C/decade`);
        card.append('p').attr('class', 'rate-answer').text(Math.abs(difference) < .0005 ? 'The two linear rates are nearly equal at this precision.' : `${difference > 0 ? 'Winter' : 'Summer'} has the larger linear warming rate in this interval.`);
      }
    }
    text = `${state.region}, ${periodStart}–${last} means (${last-periodStart+1} seasons each). ${details.join('; ')}. Separate 1995–2014 baselines; anomaly differences are distinct from the trend rates above.`;
  }
  d3.select('#summary').text(text);
}
