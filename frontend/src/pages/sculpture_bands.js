        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "展品与投影带",
  "module": "雕塑投影带",
  "caption": "雕塑投影带",
  "detail": "每个投影带有独立网格和观测版本。细部观察位绑定虚构人物雕塑的展品底图。",
  "path": "/sculpture_bands",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "title",
      "label": "虚构展品"
    },
    {
      "name": "cols",
      "label": "网格列数"
    },
    {
      "name": "rows",
      "label": "网格行数"
    },
    {
      "name": "revision",
      "label": "观测版本"
    },
    {
      "name": "scope",
      "label": "造型种类"
    }
  ],
  "layout": "split",
  "view": "grid",
  "actions": [
    {
      "name": "book_band",
      "label": "登记展品投影带",
      "path": "/sculpture_bands/book-band",
      "fields": [
        {
          "name": "code",
          "label": "投影带编号",
          "kind": "text",
          "initial": "BANK-03"
        },
        {
          "name": "title",
          "label": "虚构展品名",
          "kind": "text",
          "initial": "石门 · 起伏棱面"
        },
        {
          "name": "cols",
          "label": "网格列数",
          "kind": "int",
          "initial": 4
        },
        {
          "name": "rows",
          "label": "网格行数",
          "kind": "int",
          "initial": 4
        },
        {
          "name": "scope",
          "label": "造型种类",
          "kind": "text",
          "initial": "抽象几何雕塑"
        }
      ],
      "help": "坐标从 0 开始。投影带只接受虚构展品记录。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "sculpture_bands";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
