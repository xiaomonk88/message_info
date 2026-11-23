# 淡色实色界面与 MiSans 字体

全站使用淡色实色表面、细边框和轻阴影。卡片、侧栏、顶栏、弹窗和命令面板均不使用背景模糊；不渲染全屏光晕或固定渐变画布。

- 颜色与组件样式：`frontend/src/styles/main.css`。保留五套强调色与亮暗主题。
- 字体定义：`frontend/src/styles/fonts.css`。正文、标题、控件、表格、代码和数字统一使用 MiSans；数字保留 `tabular-nums` 设置。
- 字体资源：`frontend/public/fonts/misans/MiSans-VF.woff2`，随构建复制至 `dist/fonts/misans/`。采用完整可变字体（字重 150–700），通过 `font-display: swap` 保持加载期间文字可见。
- 本软件使用小米 MiSans 字体。来源、转换说明和官方许可见 `frontend/public/fonts/misans/README.md` 与 `LICENSE.pdf`。
- 为避免滚动卡顿，不添加 `backdrop-filter`、大面积 `filter: blur()` 或光晕装饰层；组件优先复用 `--bg-elev`、`--surface-border` 与轻量阴影令牌。
- 保留原有主题存储键，继续沿用用户的明暗和配色偏好。

验证：在 `frontend` 执行 `npm.cmd run build`，再检查桌面与手机宽度下的登录页、仪表盘、表格和弹窗。
