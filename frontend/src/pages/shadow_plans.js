        import {workspace} from '../workspace.js';
        import {plotBoard} from './plot-board.js';

        const page = {
  "title": "灯影分区平面",
  "module": "遮挡图谱",
  "caption": "遮挡图谱",
  "detail": "沿网格邻接关系建图。相邻格的遮挡与串光越接近，谱聚类越倾向于放入同一组。",
  "path": "/shadow_plans",
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
      "name": "revision",
      "label": "底图版本"
    },
    {
      "name": "clusters",
      "label": "簇数"
    },
    {
      "name": "layout",
      "label": "簇及网格坐标"
    },
    {
      "name": "evidence",
      "label": "谱聚类统计"
    },
    {
      "name": "token",
      "label": "任务凭证"
    }
  ],
  "layout": "split",
  "view": "table",
  "actions": [
    {
      "name": "segment_bank",
      "label": "测算灯影分区",
      "path": "/shadow_plans/segment-bank",
      "fields": [
        {
          "name": "band",
          "label": "投影带",
          "kind": "text",
          "initial": "BANK-01"
        },
        {
          "name": "clusters",
          "label": "划分灯组数",
          "kind": "int",
          "initial": 3
        }
      ],
      "help": "运行当前底图，记录版本、组号与邻边切分。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "pin_map",
      "label": "归档分区平面",
      "path": "/shadow_plans/pin-map",
      "fields": [
        {
          "name": "code",
          "label": "图谱号",
          "kind": "text",
          "initial": "MAP-BANK-01"
        },
        {
          "name": "token",
          "label": "计算任务凭证",
          "kind": "token",
          "initial": ""
        }
      ],
      "help": "保存灯组分区，供观测调岗时定位。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "shadow_plans";
        export async function render(root, role) {
          await workspace(root, role, {...page, renderData:plotBoard});

        }
