const SEASON_COLORS = {DJF: '#2f6fae', JJA: '#d9822b'};
const FILL = {winter: '#9cc4e4', summer: '#f3bd8a'};
const SEASONS = {DJF: 'Winter', JJA: 'Summer'};
const SCENARIOS = {ssp245: 'moderate emissions', ssp585: 'high emissions'};
const PRESETS = {
  arctic: {region: 'Arctic', scenario: 'ssp585', start: 2015, end: 2100},
  europe: {region: 'Europe sector', scenario: 'ssp585', start: 2015, end: 2100},
  namerica: {region: 'North America sector', scenario: 'ssp585', start: 2050, end: 2100}
};
const defaults = {region: 'North America sector', scenario: 'ssp585', start: 2015, end: 2100, year: 2100};
const state = {...defaults};
const fmt = d3.format('+.1f');
const rateFmt = d3.format('.2f');
let rows, meta;

Promise.all([d3.json('data/temperature.json'), d3.json('data/metadata.json')]).then(([data, metadata]) => {
  rows = data;
  meta = metadata;
  d3.select('#model-tag').text(`CMIP6 (${meta.model})`);
  d3.select('#model-details').text(`${meta.model} · member ${meta.member} · grid ${meta.grid}`);
  d3.select('#region').selectAll('option').data(meta.regions).join('option').attr('value', d => d.name).text(d => d.name);
  d3.select('#region').on('change', function() {state.region = this.value; setPreset(null); render();});
  d3.selectAll('input[name=scenario]').on('change', function() {state.scenario = this.value; setPreset(null); render();});
  d3.select('#start-year').on('input', function() {state.start = Math.min(+this.value, state.end - 1); setPreset(null); render();});
  d3.select('#end-year').on('input', function() {state.end = Math.max(+this.value, state.start + 1); setPreset(null); render();});
  d3.select('#reset').on('click', () => {
    Object.assign(state, defaults);
    syncControls();
    setPreset(null);
    render();
  });
  d3.selectAll('.preset').on('click', function() {
    Object.assign(state, PRESETS[this.dataset.preset]);
    syncControls();
    setPreset(this.dataset.preset);
    render();
  });
  syncControls();
  new ResizeObserver(render).observe(document.querySelector('#chart'));
  render();
}).catch(error => {
  d3.select('#answer').text('The data could not be loaded.');
  d3.select('#error').property('hidden', false).text(`Run this project through an HTTP server. ${error.message}`);
});

function syncControls() {
  d3.select('#region').property('value', state.region);
  d3.selectAll('input[name=scenario]').property('checked', function() {return this.value === state.scenario;});
}

function setPreset(name) {
  d3.selectAll('.preset').attr('aria-pressed', function() {return String(this.dataset.preset === name);});
}

// Slope of an ordinary least-squares line, in °C per decade.
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

  const data = rows.filter(d => d.region === state.region && d.year >= state.start && d.year <= state.end && (d.scenario === 'historical' || d.scenario === state.scenario));
  const groups = d3.groups(data, d => `${d.scenario}:${d.season}`).map(([key, values]) => ({key, scenario: values[0].scenario, season: values[0].season, values: d3.sort(values, d => d.year)}));

  const width = Math.max(280, document.querySelector('#chart').clientWidth);
  const height = width < 500 ? 310 : 390;
  const m = {top: 30, right: 20, bottom: 35, left: 45};
  const x = d3.scaleLinear().domain([state.start, state.end]).range([m.left, width - m.right]);
  const extent = d3.extent(data, d => d.anomaly);
  const y = d3.scaleLinear().domain(data.length ? [Math.min(-.3, extent[0] - .2), Math.max(.5, extent[1] + .3)] : [-.5, 1]).nice().range([height - m.bottom, m.top]);

  const svg = d3.select('#chart').selectAll('svg').data([null]).join('svg').attr('viewBox', `0 0 ${width} ${height}`).attr('tabindex', 0).attr('role', 'img')
    .attr('aria-label', `${state.region}, ${SCENARIOS[state.scenario]}: winter and summer warming since 1995–2014 in degrees Celsius, ${state.start} to ${state.end}. Left and right arrows inspect years.`);
  svg.selectAll('.grid').data([null]).join('g').attr('class', 'grid').attr('transform', `translate(${m.left},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(''));
  drawUnderlay(svg, data, x, y, height, m);
  svg.selectAll('.x-axis').data([null]).join('g').attr('class', 'axis x-axis').attr('transform', `translate(0,${height - m.bottom})`).call(d3.axisBottom(x).ticks(width < 500 ? 4 : 8).tickFormat(d3.format('d')));
  svg.selectAll('.y-axis').data([null]).join('g').attr('class', 'axis y-axis').attr('transform', `translate(${m.left},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d > 0 ? '+' : ''}${d}`));
  svg.selectAll('.zero').data([null]).join('line').attr('class', 'zero').attr('x1', m.left).attr('x2', width - m.right).attr('y1', y(0)).attr('y2', y(0)).attr('stroke', '#c9c0b1').attr('stroke-dasharray', '3 4');

  // The historical run ends in 2014 and the projections start in 2015.
  const boundary = svg.selectAll('.experiment-boundary').data(state.start <= 2014 && state.end >= 2015 ? [2014.5] : []).join('g').attr('class', 'experiment-boundary').attr('pointer-events', 'none');
  boundary.selectAll('line').data(d => [d]).join('line').attr('x1', x).attr('x2', x).attr('y1', m.top).attr('y2', height - m.bottom).attr('stroke', '#a59d8f').attr('stroke-dasharray', '4 4');
  boundary.selectAll('text').data(d => [d]).join('text').attr('x', d => x(d) + 6).attr('y', m.top + 12).attr('fill', '#7a746a').attr('font-size', 10).text('Projections →');

  const line = d3.line().x(d => x(d.year)).y(d => y(d.anomaly));
  svg.selectAll('.series').data(groups, d => d.key).join('path').attr('class', 'series')
    .attr('stroke', d => SEASON_COLORS[d.season]).attr('stroke-dasharray', d => d.season === 'JJA' ? '6 4' : null)
    .attr('stroke-opacity', d => d.scenario === 'historical' ? .45 : 1).attr('d', d => line(d.values));
  svg.selectAll('.year-label').data([null]).join('text').attr('class', 'year-label').attr('x', width - m.right).attr('y', height - 2).attr('text-anchor', 'end').attr('fill', '#7a746a').attr('font-size', 10).text('Year');

  const cursor = svg.selectAll('.cursor').data([null]).join('g').attr('class', 'cursor').attr('pointer-events', 'none').style('display', 'none');
  const overlay = svg.selectAll('.overlay').data([null]).join('rect').attr('class', 'overlay').attr('x', m.left).attr('y', m.top).attr('width', width - m.left - m.right).attr('height', height - m.top - m.bottom).attr('fill', 'transparent');
  overlay.raise();
  cursor.raise();

  const inspect = (year, pointer = null) => {
    state.year = Math.max(state.start, Math.min(state.end, Math.round(year)));
    const points = d3.sort(data.filter(d => d.year === state.year), d => d.season);
    cursor.style('display', null);
    cursor.selectAll('line').data([state.year]).join('line').attr('x1', d => x(d)).attr('x2', d => x(d)).attr('y1', m.top).attr('y2', height - m.bottom).attr('stroke', '#a59d8f').attr('stroke-dasharray', '3 3');
    cursor.selectAll('circle').data(points, d => d.season).join('circle').attr('cx', d => x(d.year)).attr('cy', d => y(d.anomaly)).attr('r', 4).attr('fill', d => SEASON_COLORS[d.season]).attr('stroke', 'white').attr('stroke-width', 1.5);
    const tip = d3.select('#tooltip').property('hidden', false);
    tip.selectAll('*').remove();
    tip.append('b').text(`${state.year}${points[0]?.scenario === 'historical' ? ' (historical run)' : ''}`);
    points.forEach(d => tip.append('span').text(`${SEASONS[d.season]}: ${fmt(d.anomaly)} °C`));
    const winter = points.find(d => d.season === 'DJF'), summer = points.find(d => d.season === 'JJA');
    if (winter && summer) {
      const gap = winter.anomaly - summer.anomaly;
      tip.append('span').attr('class', 'tip-note').text(Math.abs(gap) < .05 ? 'Both seasons have warmed about the same.' : `${gap > 0 ? 'Winter' : 'Summer'} has warmed ${Math.abs(gap).toFixed(1)} °C more.`);
    }
    const box = document.querySelector('.explorer').getBoundingClientRect();
    const chartBox = document.querySelector('#chart').getBoundingClientRect();
    const left = pointer ? pointer[0] + chartBox.left - box.left + 14 : m.left + chartBox.left - box.left;
    tip.style('left', `${Math.max(8, Math.min(left, box.width - tip.node().offsetWidth - 12))}px`).style('top', `${chartBox.top - box.top + 20}px`);
  };
  const hide = () => {cursor.style('display', 'none'); d3.select('#tooltip').property('hidden', true).attr('aria-live', 'off');};
  overlay.on('pointermove', event => {const p = d3.pointer(event, svg.node()); inspect(x.invert(p[0]), p);}).on('pointerleave', hide);
  svg.on('keydown', event => {
    if (['ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault();
      inspect(state.year + (event.key === 'ArrowRight' ? 1 : -1));
      d3.select('#tooltip').attr('aria-live', 'polite');
    }
  }).on('blur', hide);

  updateAnswer(data);
}

// One plain sentence answering "which season is warming faster?" for the current view.
function updateAnswer(data) {
  const answer = d3.select('#answer').html('');
  const detail = d3.select('#answer-detail');
  const future = data.filter(d => d.scenario !== 'historical');
  const winter = future.filter(d => d.season === 'DJF');
  const summer = future.filter(d => d.season === 'JJA');
  if (winter.length < 20) {
    answer.text(future.length ? 'Select at least 20 future years to compare warming rates.' : 'This range only covers the historical run. Move “To” past 2015 to see the projections.');
    detail.text('');
    return;
  }
  const first = d3.min(winter, d => d.year), last = d3.max(winter, d => d.year);
  const rates = {DJF: slope(winter), JJA: slope(summer)};
  const fast = rates.DJF >= rates.JJA ? 'DJF' : 'JJA', slow = fast === 'DJF' ? 'JJA' : 'DJF';
  const season = key => answer.append('span').attr('class', key === 'DJF' ? 'winter' : 'summer').text(SEASONS[key].toLowerCase());
  answer.append('span').text(`In the ${state.region}, under ${SCENARIOS[state.scenario]}, `);
  if (rates[slow] > 0 && (rates[fast] - rates[slow]) / rates[fast] < .1) {
    season('DJF'); answer.append('span').text(' and '); season('JJA');
    answer.append('span').text(' are warming at about the same rate.');
  } else {
    season(fast);
    answer.append('span').text(rates[slow] > .05 ? ` is warming about ${(rates[fast] / rates[slow]).toFixed(1)}× as fast as ` : ' is warming much faster than ');
    season(slow);
    answer.append('span').text('.');
  }
  detail.text(`Winter ${rateFmt(rates.DJF)} °C per decade · Summer ${rateFmt(rates.JJA)} °C per decade · straight-line trend, ${first}–${last}`);
}

// Shades the space between winter and summer so the reader sees at a glance which season has warmed more.
function drawUnderlay(svg, data, x, y, height, m) {
  const top = m.top, bottom = height - m.bottom;
  const defs = svg.selectAll('defs').data([null]).join('defs');
  const layer = svg.selectAll('.underlay').data([null]).join('g').attr('class', 'underlay').attr('pointer-events', 'none');
  const ribbons = d3.groups(data, d => d.scenario).map(([scenario, values]) => {
    const pts = d3.groups(values, d => d.year).map(([year, v]) => ({
      year,
      w: v.find(d => d.season === 'DJF')?.anomaly,
      s: v.find(d => d.season === 'JJA')?.anomaly
    })).filter(d => d.w != null && d.s != null);
    return {scenario, pts: d3.sort(pts, d => d.year)};
  }).filter(d => d.pts.length > 1);
  const px = d => x(d.year);
  const clip = (cls, shape) => defs.selectAll(`clipPath.${cls}`).data(ribbons, d => d.scenario)
    .join(enter => enter.append('clipPath').attr('class', cls).call(e => e.append('path')))
    .attr('id', d => `${cls}-${d.scenario}`)
    .select('path').attr('d', d => shape(d.pts));
  clip('above-winter', d3.area().x(px).y0(top).y1(d => y(d.w)));
  clip('below-winter', d3.area().x(px).y0(bottom).y1(d => y(d.w)));
  const opacity = d => d.scenario === 'historical' ? .25 : .5;
  // Above summer and below winter = winter warmed more; below summer and above winter = summer warmed more.
  layer.selectAll('path.winter-more').data(ribbons, d => d.scenario).join('path').attr('class', 'winter-more')
    .attr('d', d => d3.area().x(px).y0(p => y(p.s)).y1(top)(d.pts)).attr('clip-path', d => `url(#below-winter-${d.scenario})`)
    .attr('fill', FILL.winter).attr('fill-opacity', opacity);
  layer.selectAll('path.summer-more').data(ribbons, d => d.scenario).join('path').attr('class', 'summer-more')
    .attr('d', d => d3.area().x(px).y0(p => y(p.s)).y1(bottom)(d.pts)).attr('clip-path', d => `url(#above-winter-${d.scenario})`)
    .attr('fill', FILL.summer).attr('fill-opacity', opacity);
}
