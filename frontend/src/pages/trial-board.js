import {el} from '../dom.js';

const percent = share => new Intl.NumberFormat('zh-CN', {style:'percent', maximumFractionDigits:1}).format(share);

// 把差异格对汇总成“涉及格 -> 与本队同簇但异队不同簇的格”映射。
function diffIndex(map) {
  const index = new Map();
  for (const pair of map.diff_pairs || []) {
    for (const [here, there] of [[pair.cell_a, pair.cell_b], [pair.cell_b, pair.cell_a]]) {
      if (!index.has(here)) index.set(here, []);
      index.get(here).push(there);
    }
  }
  return index;
}

function teamGrid(map, total, fillCount, partnerLabel) {
  if (!map) {
    const ready = fillCount === total && total > 0;
    return el('article', {class:'team-sheet'},
      el('h3', {}, '尚未封存分簇图谱'),
      el('p', {class:'empty'},
        `当前已记 ${fillCount}/${total} 格` + (ready ? '，可提交分簇测算。' : '，记满整网格后才能分簇。')));
  }
  const cols = map.evidence.grid[0];
  const diffs = diffIndex(map);
  const note = el('p', {class:'plot-detail', 'aria-live':'polite'},
    `只在本队同簇的格对 ${map.diff_pairs.length} 组；点格查看与${partnerLabel}的差异。`);
  const grid = el('div', {class:'plot-grid', 'aria-label':`${map.team} 试投网格`, style:'--cols:'+cols},
    map.layout.map(point => {
      const flagged = diffs.has(point.code);
      return el('button', {
        type:'button',
        class:'plot-point cluster-'+point.cluster+(flagged ? ' diff' : ''),
        'aria-label':`${point.code}，第 ${point.cluster} 组${flagged ? '，差异格' : ''}`,
        'data-code':point.code, 'aria-pressed':'false',
        onclick:event => {
          const old = grid.querySelector('[aria-pressed=true]');
          if (old) old.setAttribute('aria-pressed', 'false');
          event.currentTarget.setAttribute('aria-pressed', 'true');
          const others = diffs.get(point.code);
          note.textContent = `${point.code} · 第 ${point.cluster} 组 · 遮挡 ${percent(point.shade)} · 串光 ${percent(point.spill)}` +
            (others ? ` · 仅本队同簇：${others.join('、')}` : ' · 两队该格簇属一致');
        }
      }, String(point.cluster));
    }));
  return el('article', {class:'team-sheet'},
    el('h3', {}, `${map.team} 队 · 底图版本 ${map.revision} · ${map.clusters} 簇`),
    el('p', {class:'plot-caption'}, `${map.evidence.cut_edges}/${map.evidence.edges} 条边跨区`),
    grid, note);
}

export function trialBoard(rows) {
  // rows: {runs, cells, maps, bands}
  const {runs, cells, maps, bands} = rows;
  if (!runs.length) return el('p', {class:'empty'}, '先开启一次双队试投对照，两队各自记满同一网格。');
  const bandById = new Map(bands.map(band => [band.code, band]));
  const runCards = runs.map(run => {
    const teamMaps = maps.filter(map => map.run === run.code);
    const north = teamMaps.find(map => map.team === 'NORTH');
    const south = teamMaps.find(map => map.team === 'SOUTH');
    const total = (() => {
      const band = bandById.get(run.band);
      return band ? band.cols * band.rows : 0;
    })();
    const fillOf = team => cells.filter(cell => cell.run === run.code && cell.team === team).length;
    const diffCount = north ? north.diff_pairs.length : 0;
    return el('article', {class:'run-card'},
      el('h3', {}, `${run.code} · ${bandById.get(run.band)?.title || run.band}`),
      el('p', {class:'plot-caption'},
        `封存底图版本 ${run.baseline_revision} · 状态 ${run.status}` +
        (run.adopted_team ? ` · 已采纳 ${run.adopted_team}（${run.adopted_plan}）` : '') +
        ` · 仅单队同簇格对 ${diffCount} 组`),
      el('div', {class:'team-grids'},
        teamGrid(north, total, fillOf('NORTH'), 'SOUTH 队'),
        teamGrid(south, total, fillOf('SOUTH'), 'NORTH 队')));
  });
  return el('section', {class:'trial-board'}, runCards);
}
