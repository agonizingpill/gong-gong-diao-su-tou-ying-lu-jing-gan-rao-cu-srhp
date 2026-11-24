import {request} from '../api.js';
import {actionForm} from '../controls.js';
import {el} from '../dom.js';
import {titleBlock, status} from '../widgets.js';
import {trialBoard} from './trial-board.js';

const page = {
  title: '双队试投对照',
  module: '双队试投读数',
  caption: '双队试投对照',
  detail: '两队各自记满同一网格、分别分簇，标出只在其中一张图同簇的格对。读数随对照封存，底图换版后旧对照失效；复核员采纳其中一队的整套读数。',
  actions: [
    {
      name: 'open_trial',
      label: '开启双队试投对照',
      path: '/trial_runs/open-trial',
      fields: [{name: 'band', label: '投影带', kind: 'text', initial: 'BANK-01'}],
      help: '按当前底图版本封存一批对照，两队随后在同一网格独立读数。',
      roles: ['operator', 'reviewer'],
      success: '已开启'
    },
    {
      name: 'record_trial',
      label: '记录某队试投方格',
      path: '/trial_runs/record-trial',
      fields: [
        {name: 'band', label: '投影带', kind: 'text', initial: 'BANK-01'},
        {name: 'team', label: '试投灯组 NORTH/SOUTH', kind: 'text', initial: 'NORTH'},
        {name: 'x', label: '列坐标', kind: 'int', initial: 0},
        {name: 'y', label: '行坐标', kind: 'int', initial: 0},
        {name: 'shade', label: '遮挡面积比', kind: 'float', initial: 0.18},
        {name: 'spill', label: '串光面积比', kind: 'float', initial: 0.72}
      ],
      help: '两队同格各存一行、互不覆盖。底图换版后先记下的补测会令旧对照失效。',
      roles: ['operator', 'reviewer'],
      success: '已写入'
    },
    {
      name: 'segment_trial',
      label: '某队分簇测算',
      path: '/trial_runs/segment-trial',
      fields: [
        {name: 'band', label: '投影带', kind: 'text', initial: 'BANK-01'},
        {name: 'team', label: '试投灯组 NORTH/SOUTH', kind: 'text', initial: 'NORTH'},
        {name: 'clusters', label: '划分灯组数', kind: 'int', initial: 3}
      ],
      help: '该队网格记满后才可测算，返回计算任务凭证。',
      roles: ['operator', 'reviewer'],
      success: '已排队'
    },
    {
      name: 'pin_trial',
      label: '封存某队分簇图谱',
      path: '/trial_runs/pin-trial',
      fields: [
        {name: 'band', label: '投影带', kind: 'text', initial: 'BANK-01'},
        {name: 'team', label: '试投灯组 NORTH/SOUTH', kind: 'text', initial: 'NORTH'},
        {name: 'token', label: '计算任务凭证', kind: 'token', initial: ''}
      ],
      help: '两队都封存后自动标出仅单队同簇的格对；底图换版须重新对照。',
      roles: ['operator', 'reviewer'],
      success: '已封存'
    },
    {
      name: 'adopt_trial',
      label: '复核员采纳整套读数',
      path: '/trial_runs/adopt-trial',
      fields: [
        {name: 'band', label: '投影带', kind: 'text', initial: 'BANK-01'},
        {name: 'team', label: '采纳灯组 NORTH/SOUTH', kind: 'text', initial: 'NORTH'},
        {name: 'plan_code', label: '归档图谱号', kind: 'text', initial: 'MAP-BANK-01-TRIAL'}
      ],
      help: '归档图与现用底图一次性切换；重复采纳同一队不重复升版。',
      roles: ['reviewer'],
      success: '已采纳'
    }
  ]
};

export const {title} = page;
export const key = 'trial_runs';

export async function render(root, role) {
  const panel = el('section', {class:'ledger', 'aria-label':page.caption});
  const refresh = async () => {
    try {
      const [runs, cells, maps, bands] = await Promise.all([
        request('/trial_runs'), request('/trial_cells'),
        request('/trial_maps'), request('/sculpture_bands')]);
      panel.replaceChildren(el('h2', {}, page.caption), trialBoard({runs, cells, maps, bands}));
    } catch (error) {
      panel.replaceChildren(status(error.message, 'error'));
    }
  };
  const actions = page.actions.filter(x => x.roles.includes(role));
  root.replaceChildren(titleBlock(page.module, page.title, page.detail),
    el('div', {class:'work split'}, panel,
      actions.length ? el('section', {class:'actions'}, actions.map(x => actionForm(x, refresh))) : null));
  return refresh();
}
