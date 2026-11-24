import {el} from '../dom.js';

const percent = share => new Intl.NumberFormat('zh-CN', {style:'percent',maximumFractionDigits:1}).format(share);

export function plotBoard(plans) {
  if (!plans.length) return el('p',{class:'empty'},'试投格录齐后测算。展陈复核员归档图谱后会显示灯影方格。');
  const chosen = el('div',{class:'plot-sheet'});
  const lookup = new Map(plans.map(plan => [plan.code,plan]));
  const selector = el('select',{'aria-label':'遮挡图谱',onchange:event => draw(lookup.get(event.target.value))},
    plans.map(plan => el('option',{value:plan.code},plan.code)));
  function draw(plan) {
    const note = el('p',{class:'plot-detail','aria-live':'polite'},'选择方格查看试投覆盖。带虚线边框的格子需要二签。');
    const cols = plan.evidence.grid[0];
    const grid = el('div',{class:'plot-grid','aria-label':'灯影网格',style:'--cols:'+cols},
      plan.layout.map(point => el('button',{
        type:'button',class:'plot-point cluster-'+point.cluster+(point.protected?' protected':''),
        'aria-label':point.code+'，第 '+point.cluster+' 组'+(point.protected?'，保护位':''),
        'data-code':point.code, 'aria-pressed':'false',
        onclick:event => {
          const old = grid.querySelector('[aria-pressed=true]');
          if (old) old.setAttribute('aria-pressed','false');
          event.currentTarget.setAttribute('aria-pressed','true');
          note.textContent = point.code+' · 第 '+point.cluster+' 组 · 遮挡 '+percent(point.shade)+
            ' · 串光 '+percent(point.spill)+(point.protected?' · 保护观察位需二签':'');
        }
      },String(point.cluster))));
    chosen.replaceChildren(
      el('p',{class:'plot-caption'},plan.band+' · 观测版本 '+plan.revision+' · '+
        plan.evidence.plots+' 格 · '+plan.evidence.cut_edges+'/'+plan.evidence.edges+' 条边跨区'),
      grid,note);
  }
  draw(plans[0]);
  return el('section',{class:'plan-picker'},el('label',{},'归档平面',selector),chosen);
}
