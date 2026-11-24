        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "遮挡与串光观察格",
  "module": "遮挡观测格",
  "caption": "遮挡观测格",
  "detail": "以方格记录试投覆盖。只更新测量读数，保留该格的保护标记与灯组责任。",
  "path": "/sight_cells",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "band",
      "label": "投影带"
    },
    {
      "name": "x",
      "label": "列坐标"
    },
    {
      "name": "y",
      "label": "行坐标"
    },
    {
      "name": "shade",
      "label": "遮挡面积比"
    },
    {
      "name": "spill",
      "label": "串光面积比"
    },
    {
      "name": "owner",
      "label": "当前责任灯组"
    },
    {
      "name": "protected",
      "label": "雕塑保护观察位"
    }
  ],
  "layout": "flip",
  "view": "table",
  "actions": [
    {
      "name": "record_beam",
      "label": "记录试投方格",
      "path": "/sight_cells/record-beam",
      "fields": [
        {
          "name": "band",
          "label": "投影带",
          "kind": "text",
          "initial": "BANK-01"
        },
        {
          "name": "x",
          "label": "列坐标",
          "kind": "int",
          "initial": 2
        },
        {
          "name": "y",
          "label": "行坐标",
          "kind": "int",
          "initial": 1
        },
        {
          "name": "shade",
          "label": "遮挡面积比",
          "kind": "float",
          "initial": 0.46
        },
        {
          "name": "spill",
          "label": "串光面积比",
          "kind": "float",
          "initial": 0.5
        }
      ],
      "help": "两项面积比均为 0 至 1。录入后旧待签移交单会失效。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "protect_station",
      "label": "登记雕塑保护位",
      "path": "/sight_cells/protect-station",
      "fields": [
        {
          "name": "code",
          "label": "要保护的观察位",
          "kind": "text",
          "initial": "BANK-01-1-1"
        }
      ],
      "help": "细部保护标记只用于虚构人物雕塑。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "sight_cells";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
