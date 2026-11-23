/**
 * 图标注册表 —— 分类/板块自定义图标的唯一入口。
 *
 * 静态命名导入 + 冻结映射表：lucide-vue-next 为 ESM + sideEffects:false，
 * 只有此处列出的图标会进入 bundle（每个约 0.4KB）。
 * 严禁 `import * as icons` 动态取值 —— 会把全量 ~1500 个图标打进产物。
 *
 * 存库字符串 = lucide 官方 PascalCase 组件名（如 "Server"），
 * 查无此名一律回退 fallback，脏数据安全。
 */
import type { Component } from 'vue'
import {
  // 数据与基础设施
  Database, Server, HardDrive, Cloud, Globe, Network, Wifi, Cpu, Terminal,
  Code, Box, Boxes, Layers, Container,
  // 安全与账号
  Key, KeyRound, Lock, Shield, ShieldCheck, Fingerprint, UserRound, Users, BadgeCheck,
  // 财务
  CreditCard, Wallet, Banknote, Coins, Receipt, PiggyBank, TrendingUp,
  ChartColumn, ChartPie, CircleDollarSign,
  // 文件与资料
  FileText, Folder, FolderOpen, Archive, BookOpen, Notebook, StickyNote,
  ClipboardList, Image, Film, Music,
  // 通讯
  Mail, MessageSquare, Phone, Send, AtSign,
  // 生活
  House, Car, Plane, ShoppingCart, ShoppingBag, Package, Gift, Utensils,
  Coffee, Gamepad2, HeartPulse,
  // 通用
  Star, Heart, Bookmark, Tag, Bell, Calendar, Clock, MapPin, Link, Zap,
  Sparkles, Flag, Briefcase, Building2, GraduationCap, Lightbulb, Rocket,
  Wrench, Camera, Smartphone, Laptop, Headphones, Bot,
} from 'lucide-vue-next'

export interface IconDef {
  name: string
  icon: Component
  /** 中文搜索关键词 */
  kw: string
  group: string
}

export const ICON_LIST: IconDef[] = [
  // 数据与基础设施
  { name: 'Database', icon: Database, kw: '数据库 数据', group: '数据与设施' },
  { name: 'Server', icon: Server, kw: '服务器 vps 主机', group: '数据与设施' },
  { name: 'HardDrive', icon: HardDrive, kw: '硬盘 存储 磁盘', group: '数据与设施' },
  { name: 'Cloud', icon: Cloud, kw: '云 云服务', group: '数据与设施' },
  { name: 'Globe', icon: Globe, kw: '地球 网站 域名 网络', group: '数据与设施' },
  { name: 'Network', icon: Network, kw: '网络 拓扑', group: '数据与设施' },
  { name: 'Wifi', icon: Wifi, kw: '无线 网络', group: '数据与设施' },
  { name: 'Cpu', icon: Cpu, kw: '处理器 芯片 硬件', group: '数据与设施' },
  { name: 'Terminal', icon: Terminal, kw: '终端 命令行', group: '数据与设施' },
  { name: 'Code', icon: Code, kw: '代码 开发', group: '数据与设施' },
  { name: 'Box', icon: Box, kw: '盒子 容器', group: '数据与设施' },
  { name: 'Boxes', icon: Boxes, kw: '盒子 集合', group: '数据与设施' },
  { name: 'Layers', icon: Layers, kw: '图层 层级', group: '数据与设施' },
  { name: 'Container', icon: Container, kw: '容器 docker', group: '数据与设施' },
  // 安全与账号
  { name: 'Key', icon: Key, kw: '钥匙 密钥 密码', group: '安全与账号' },
  { name: 'KeyRound', icon: KeyRound, kw: '钥匙 密钥 密码', group: '安全与账号' },
  { name: 'Lock', icon: Lock, kw: '锁 加密 密码', group: '安全与账号' },
  { name: 'Shield', icon: Shield, kw: '盾牌 防护 安全', group: '安全与账号' },
  { name: 'ShieldCheck', icon: ShieldCheck, kw: '盾牌 已验证 安全', group: '安全与账号' },
  { name: 'Fingerprint', icon: Fingerprint, kw: '指纹 身份', group: '安全与账号' },
  { name: 'UserRound', icon: UserRound, kw: '用户 账号 个人', group: '安全与账号' },
  { name: 'Users', icon: Users, kw: '用户组 团队 成员', group: '安全与账号' },
  { name: 'BadgeCheck', icon: BadgeCheck, kw: '认证 徽章 通过', group: '安全与账号' },
  // 财务
  { name: 'CreditCard', icon: CreditCard, kw: '信用卡 银行卡 支付', group: '财务' },
  { name: 'Wallet', icon: Wallet, kw: '钱包 资产', group: '财务' },
  { name: 'Banknote', icon: Banknote, kw: '钞票 现金 钱', group: '财务' },
  { name: 'Coins', icon: Coins, kw: '硬币 金币 货币', group: '财务' },
  { name: 'Receipt', icon: Receipt, kw: '收据 账单 发票', group: '财务' },
  { name: 'PiggyBank', icon: PiggyBank, kw: '存钱罐 储蓄', group: '财务' },
  { name: 'TrendingUp', icon: TrendingUp, kw: '上涨 趋势 投资', group: '财务' },
  { name: 'ChartColumn', icon: ChartColumn, kw: '柱状图 统计 图表', group: '财务' },
  { name: 'ChartPie', icon: ChartPie, kw: '饼图 占比 图表', group: '财务' },
  { name: 'CircleDollarSign', icon: CircleDollarSign, kw: '美元 金额 订阅', group: '财务' },
  // 文件与资料
  { name: 'FileText', icon: FileText, kw: '文件 文档 笔记', group: '文件与资料' },
  { name: 'Folder', icon: Folder, kw: '文件夹 目录 分类', group: '文件与资料' },
  { name: 'FolderOpen', icon: FolderOpen, kw: '文件夹 打开', group: '文件与资料' },
  { name: 'Archive', icon: Archive, kw: '归档 存档 备份', group: '文件与资料' },
  { name: 'BookOpen', icon: BookOpen, kw: '书 阅读 学习', group: '文件与资料' },
  { name: 'Notebook', icon: Notebook, kw: '笔记本 记录', group: '文件与资料' },
  { name: 'StickyNote', icon: StickyNote, kw: '便签 备忘', group: '文件与资料' },
  { name: 'ClipboardList', icon: ClipboardList, kw: '清单 任务 列表', group: '文件与资料' },
  { name: 'Image', icon: Image, kw: '图片 照片 相册', group: '文件与资料' },
  { name: 'Film', icon: Film, kw: '电影 视频 影视', group: '文件与资料' },
  { name: 'Music', icon: Music, kw: '音乐 歌曲', group: '文件与资料' },
  // 通讯
  { name: 'Mail', icon: Mail, kw: '邮件 邮箱', group: '通讯' },
  { name: 'MessageSquare', icon: MessageSquare, kw: '消息 聊天 评论', group: '通讯' },
  { name: 'Phone', icon: Phone, kw: '电话 手机号 联系', group: '通讯' },
  { name: 'Send', icon: Send, kw: '发送 telegram', group: '通讯' },
  { name: 'AtSign', icon: AtSign, kw: '艾特 邮箱 社交', group: '通讯' },
  // 生活
  { name: 'House', icon: House, kw: '房子 家 住址', group: '生活' },
  { name: 'Car', icon: Car, kw: '汽车 车辆 交通', group: '生活' },
  { name: 'Plane', icon: Plane, kw: '飞机 旅行 出行', group: '生活' },
  { name: 'ShoppingCart', icon: ShoppingCart, kw: '购物车 购物', group: '生活' },
  { name: 'ShoppingBag', icon: ShoppingBag, kw: '购物袋 商品', group: '生活' },
  { name: 'Package', icon: Package, kw: '包裹 快递 物品', group: '生活' },
  { name: 'Gift', icon: Gift, kw: '礼物 礼品', group: '生活' },
  { name: 'Utensils', icon: Utensils, kw: '餐具 美食 餐厅', group: '生活' },
  { name: 'Coffee', icon: Coffee, kw: '咖啡 饮品', group: '生活' },
  { name: 'Gamepad2', icon: Gamepad2, kw: '游戏 手柄 娱乐', group: '生活' },
  { name: 'HeartPulse', icon: HeartPulse, kw: '健康 心率 医疗', group: '生活' },
  // 通用
  { name: 'Star', icon: Star, kw: '星标 收藏 重要', group: '通用' },
  { name: 'Heart', icon: Heart, kw: '喜欢 收藏 心', group: '通用' },
  { name: 'Bookmark', icon: Bookmark, kw: '书签 收藏', group: '通用' },
  { name: 'Tag', icon: Tag, kw: '标签 分类', group: '通用' },
  { name: 'Bell', icon: Bell, kw: '铃铛 提醒 通知', group: '通用' },
  { name: 'Calendar', icon: Calendar, kw: '日历 日期 计划', group: '通用' },
  { name: 'Clock', icon: Clock, kw: '时钟 时间 定时', group: '通用' },
  { name: 'MapPin', icon: MapPin, kw: '定位 地址 位置', group: '通用' },
  { name: 'Link', icon: Link, kw: '链接 网址 url', group: '通用' },
  { name: 'Zap', icon: Zap, kw: '闪电 快捷 能量', group: '通用' },
  { name: 'Sparkles', icon: Sparkles, kw: '星光 亮点 ai', group: '通用' },
  { name: 'Flag', icon: Flag, kw: '旗帜 标记 里程碑', group: '通用' },
  { name: 'Briefcase', icon: Briefcase, kw: '公文包 工作 商务', group: '通用' },
  { name: 'Building2', icon: Building2, kw: '大楼 公司 机构', group: '通用' },
  { name: 'GraduationCap', icon: GraduationCap, kw: '学位帽 教育 学习', group: '通用' },
  { name: 'Lightbulb', icon: Lightbulb, kw: '灯泡 想法 灵感', group: '通用' },
  { name: 'Rocket', icon: Rocket, kw: '火箭 发布 项目', group: '通用' },
  { name: 'Wrench', icon: Wrench, kw: '扳手 工具 维护', group: '通用' },
  { name: 'Camera', icon: Camera, kw: '相机 摄影 拍照', group: '通用' },
  { name: 'Smartphone', icon: Smartphone, kw: '手机 移动设备', group: '通用' },
  { name: 'Laptop', icon: Laptop, kw: '笔记本电脑 电脑', group: '通用' },
  { name: 'Headphones', icon: Headphones, kw: '耳机 音频', group: '通用' },
  { name: 'Bot', icon: Bot, kw: '机器人 自动化 ai', group: '通用' },
]

export const ICON_REGISTRY: Readonly<Record<string, Component>> = Object.freeze(
  Object.fromEntries(ICON_LIST.map((d) => [d.name, d.icon]))
)

/** 按存库名解析图标组件；查无此名回退 fallback */
export function resolveIcon(name?: string | null, fallback = 'Database'): Component {
  return (name && ICON_REGISTRY[name]) || ICON_REGISTRY[fallback] || Database
}
