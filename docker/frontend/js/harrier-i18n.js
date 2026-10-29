/**
 * Harrier frontend runtime translation overlay (English-only).
 *
 * The web UI in this repository is shipped as a compiled Vue bundle
 * (no frontend source available), so a build-time i18n solution is not
 * possible. This script translates the rendered DOM from the bundle's
 * built-in Chinese strings to English at runtime, and keeps translating
 * via a MutationObserver as Vue re-renders the page.
 *
 * The Chinese strings in DICT/RULES below are the bundle's source text
 * being matched, not user-facing content.
 */
(function () {
  "use strict";

  var TITLE_EN = "Harrier";

  var DICT = {
    // ---- document / login ----
    "Harrier": "Harrier",
    "用户名": "Username",
    "密码": "Password",
    "登 录": "Login",
    "登录成功": "Login successful",
    "用户名或密码错误": "Incorrect username or password",
    "请输入用户名": "Please enter username",
    "请输入密码": "Please enter password",
    "本系统为开源项目": "This system is an open source project",
    "退出": "Log Out",
    "资产灯塔系统": "Asset Recon System",
    "登录": "Login",
    "左侧导航": "Left navigation",
    "退出成功": "Logged out",
    "修改密码": "Change Password",
    "旧密码": "Old Password",
    "新密码": "New Password",
    "确认密码": "Confirm Password",
    "请输入旧密码": "Please enter old password",
    "请输入新密码": "Please enter new password",
    "请输入确认密码": "Please confirm password",
    "两次密码不一致": "Passwords do not match",
    "修改成功，请重新登录": "Changed successfully, please log in again",

    // ---- navigation / pages ----
    "任务管理": "Task Management",
    "任务详情": "Task Detail",
    "资产搜索": "Asset Search",
    "资产分组": "Asset Group",
    "资产分组详情": "Asset Group Detail",
    "资产监控": "Asset Monitoring",
    "策略配置": "Policy Config",
    "计划任务": "Scheduled Tasks",
    "指纹管理": "Fingerprint Management",
    "GitHub 任务管理": "GitHub Task Management",
    "GitHub 任务详情": "GitHub Task Detail",
    "GitHub管理": "GitHub Management",
    "GitHub监控": "GitHub Monitor",
    "GitHub 监控管理": "GitHub Monitor Management",
    "GitHub 监控详情": "GitHub Monitor Detail",
    "GitHub 结果监控管理": "GitHub Result Monitor Management",
    "全局查看": "Global View",

    // ---- common UI ----
    "序号": "No.",
    "名称": "Name",
    "标题": "Title",
    "状态": "Status",
    "操作": "Action",
    "时间": "Time",
    "开始时间": "Start Time",
    "结束时间": "End Time",
    "开始日期": "Start Date",
    "结束日期": "End Date",
    "更新时间": "Update Time",
    "保存时间": "Save Time",
    "提交时间": "Submit Time",
    "发现时间": "Found Time",
    "内容": "Content",
    "类型": "Type",
    "类别": "Category",
    "描述": "Description",
    "备注": "Remark",
    "数量": "Count",
    "统计": "Statistics",
    "配置项": "Configuration Items",
    "配置信息": "Configuration",
    "基本信息": "Basic Info",
    "确定": "OK",
    "确 定": "OK",
    "取消": "Cancel",
    "取 消": "Cancel",
    "确认": "Confirm",
    "删除": "Delete",
    "批量删除": "Batch Delete",
    "编辑": "Edit",
    "修改": "Modify",
    "复制": "Copy",
    "复制成功": "Copied",
    "内容已复制到剪切板！": "Copied to clipboard!",
    "抱歉，复制失败！": "Sorry, copy failed!",
    "停止": "Stop",
    "批量停止": "Batch Stop",
    "批量停止成功": "Batch stop succeeded",
    "暂停": "Pause",
    "暂停成功": "Paused",
    "恢复": "Resume",
    "恢复成功": "Resumed",
    "批量恢复": "Batch Resume",
    "重启": "Restart",
    "同步": "Sync",
    "同步任务": "Sync Task",
    "同步中...": "Syncing...",
    "等待中": "Waiting",
    "成功": "Success",
    "导出": "Export",
    "批量导出": "Batch Export",
    "下载文件": "Download File",
    "删除文件": "Delete File",
    "预览文件": "Preview File",
    "文件上传中": "Uploading file",
    "上传错误": "Upload Error",
    "上传成功：": "Uploaded: ",
    ", 重复数：": ", duplicates: ",
    "添加成功": "Added successfully",
    "添加失败": "Add failed",
    "删除成功": "Deleted successfully",
    "提交成功": "Submitted successfully",
    "提交失败": "Submission failed",
    "修改成功": "Modified successfully",
    "更新": "Update",
    "更新列表成功": "List updated",
    "清空": "Clear",
    "清空列表成功": "List cleared",
    "清除": "Clear",
    "重置": "Reset",
    "应用": "Apply",
    "展开": "Expand",
    "收起": "Collapse",
    "展开行": "Expand Row",
    "关闭行": "Close Row",
    "全选": "Select All",
    "全选当页": "Select Current Page",
    "反选当页": "Invert Current Page",
    "排序": "Sort",
    "筛选": "Filter",
    "知道了": "Got it",
    "暂无数据": "No Data",
    "返回": "Back",
    "请输入": "Please enter",
    "请选择": "Please select",
    "进行搜索": "Search",
    "请输入搜索内容": "Please enter search content",
    "请输入关键字进行查询": "Please enter keywords to search",
    "关键字": "Keyword",
    "查询语句": "Query",
    "请输入查询语句": "Please enter query",
    "请输入查询语句!": "Please enter query!",
    "测试": "Test",
    "测试成功": "Test successful",
    "不能为空": "Cannot be empty",
    "只能输入数字": "Numbers only",
    "确认删除吗？": "Confirm deletion?",
    "确认删除所选数据吗？": "Are you sure you want to delete the selected data?",
    "确认删除所选数据吗": "Are you sure you want to delete the selected data?",
    "确认停止所选数据吗？": "Are you sure you want to stop the selected items?",
    "确认停止所选数据吗": "Are you sure you want to stop the selected items?",
    "删除后不可恢复，确认删除吗？": "This cannot be undone. Confirm deletion?",
    "删除后无法恢复，确认删除吗？": "This cannot be undone. Confirm deletion?",
    "等于": "equals",
    "大于": "greater than",
    "小于": "less than",
    "包含": "contains",
    "不包含": "not contains",
    "不等于": "not equal",
    "至": "to",
    "项": "items",

    // ---- pagination / calendar ----
    "共": "Total",
    "条数据": "records",
    "条/页": "/ page",
    "跳至": "Go to",
    "页": "",
    "页/": "/",
    "上一页": "Previous Page",
    "下一页": "Next Page",
    "向前 3 页": "Back 3 Pages",
    "向前 5 页": "Back 5 Pages",
    "向后 3 页": "Forward 3 Pages",
    "向后 5 页": "Forward 5 Pages",
    "今天": "Today",
    "此刻": "Now",
    "返回今天": "Back to Today",
    "选择时间": "Select Time",
    "选择日期": "Select Date",
    "选择周": "Select Week",
    "选择月份": "Select Month",
    "选择年份": "Select Year",
    "选择年代": "Select Decade",
    "上个月 (翻页上键)": "Previous Month (Page Up)",
    "下个月 (翻页下键)": "Next Month (Page Down)",
    "上一年 (Control键加左方向键)": "Previous Year (Ctrl+Left)",
    "下一年 (Control键加右方向键)": "Next Year (Ctrl+Right)",
    "上一年代": "Previous Decade",
    "下一年代": "Next Decade",
    "上一世纪": "Previous Century",
    "下一世纪": "Next Century",
    "YYYY年": "YYYY",
    "D日": "D",
    "YYYY年M月D日": "YYYY-MM-DD",
    "YYYY年M月D日 HH时mm分ss秒": "YYYY-MM-DD HH:mm:ss",

    // ---- tasks ----
    "任务名称": "Task Name",
    "任务名": "Task Name",
    "任务id": "Task ID",
    "任务类型": "Task Type",
    "任务类别": "Task Category",
    "任务下发": "Policy Scan",
    "添加任务": "Quick Scan",
    "修改任务": "Modify Task",
    "添加监控任务": "Add Monitor Task",
    "资产侦查任务": "Full Scan (ports first)",
    "资产发现任务": "Asset Discovery Task",
    "资产信息": "Asset Info",
    "task,资产侦查任务": "task, Full Scan (ports first)",
    "risk_cruising,风险巡航任务": "risk_cruising, Site-Only Scan (no ports)",
    "风险巡航任务": "Site-Only Scan (no ports)",
    "风险巡航任务-": "Site-Only Scan-",
    "风险任务下发": "Site Scan Dispatch",
    "添加风险巡航任务": "Add Site-Only Scan",
    "风险": "Risk",
    "FOFA 任务下发": "FOFA Scan",
    "监控-": "Monitor-",
    "停止任务成功": "Task stopped",
    "重启任务成功": "Task restarted",
    "删除任务成功": "Task deleted",
    "删除任务数据": "Delete task data",
    "下发成功": "Dispatched successfully",
    "运行间隔": "Run Interval",
    "运行次数": "Run Count",
    "运行间隔时间不小于6小时": "Run interval must be at least 6 hours",
    "请输入运行间隔": "Please enter run interval",
    "请输入运行间隔时间": "Please enter run interval",
    "小时": "hours",
    "请输入任务名称": "Please enter task name",
    "请输入任务名称!": "Please enter task name!",
    "请输入名称": "Please enter name",
    "请输入名称!": "Please enter name!",
    "请输入目标，支持IP、IP段、域名": "Please enter target(s): IP, IP range or domain",
    "请输入目标，支持IP、IP段、域名!": "Please enter target(s): IP, IP range or domain!",
    "目标": "Target",
    "选择目标数": "Targets Selected",
    "请至少勾选一个参数项!": "Please check at least one option!",
    "任务下发成功": "Task dispatched",
    "结果数目": "Result Count",
    "结果数：": "Results: ",
    "相关资产": "Related Assets",
    "Harrier资产导出报告_": "Harrier_Asset_Export_Report_",

    // ---- scan options ----
    "域名爆破": "Domain Brute",
    "域名爆破类型": "Domain Brute Type",
    "域名查询插件": "Domain Query Plugin",
    "DNS字典智能生成": "Smart DNS Dict Generation",
    "RiskIQ 调用": "RiskIQ",
    "Harrier 历史查询": "Harrier History Query",
    "端口扫描": "Port Scan",
    "端口扫描类型": "Port Scan Type",
    "自定义端口": "Custom Ports",
    "服务识别": "Service Detection",
    "服务弱口令爆破": "Service Weak Password Brute",
    "操作系统识别": "OS Detection",
    "操作系统": "OS",
    "SSL 证书获取": "SSL Cert Fetch",
    "SSL证书": "SSL Cert",
    "跳过CDN": "Skip CDN",
    "服务(python)识别": "Service (Python) Detection",
    "站点识别": "Site Identification",
    "搜索引擎调用": "Search Engine",
    "站点爬虫": "Site Spider",
    "站点截图": "Site Screenshot",
    "文件泄露": "File Leak",
    "文件泄露扫描": "File Leak Scan",
    "nuclei 调用": "Nuclei Scan",
    "WIH 调用": "WIH",
    "Host 碰撞": "Host Collision",
    "GitHub搜索": "GitHub Search",
    "JS PATH收集": "JS PATH Collection",
    "Fofa IP 查询": "Fofa IP Query",
    "Fofa IP查询": "Fofa IP Query",
    "子域名劫持扫描": "Subdomain Takeover Scan",
    "crt.sh 调用": "crt.sh",
    "PoC扫描": "PoC Scan",
    "PoC配置": "PoC Config",
    "PoC信息": "PoC Info",
    "弱口令爆破": "Weak Password Brute",
    "大字典": "Big Dictionary",
    "全端口": "All Ports",
    "自定义": "Custom",
    "请选择域名爆破类型": "Please select domain brute type",
    "请选择域名爆破类型!": "Please select domain brute type!",
    "请选择端口扫描类型": "Please select port scan type",
    "请选择端口扫描类型!": "Please select port scan type!",
    "请输如自定义端口，如:80,443": "Please enter custom ports, e.g.: 80,443",
    "请输如自定义端口，如:80,443!": "Please enter custom ports, e.g.: 80,443!",
    "IP高级配置": "IP Advanced Config",
    "主机超时时间": "Host Timeout",
    "主机超时时间(s)": "Host Timeout (s)",
    "默认(900s)": "Default (900s)",
    "请选择主机超时时间": "Please select host timeout",
    "请选择主机超时时间!": "Please select host timeout!",
    "请输入主机超时时间": "Please enter host timeout",
    "请输入主机超时时间!": "Please enter host timeout!",
    "探测报文并行度": "Probe Parallelism",
    "请输入报文并行度": "Please enter probe parallelism",
    "最少发包速率": "Min Packet Rate",
    "请输入最少发包速率": "Please enter min packet rate",
    "排除端口": "Excluded Ports",
    "排除指定端⼝，不对其进⾏扫描，如：9100,9102,1-100": "Exclude specified ports from scanning, e.g.: 9100,9102,1-100",

    // ---- policy ----
    "策略": "Policy",
    "策略名称": "Policy Name",
    "策略描述": "Policy Description",
    "新建策略": "New Policy",
    "编辑策略": "Edit Policy",
    "新建配置": "New Config",
    "请输入策略名称": "Please enter policy name",
    "请输入策略名称!": "Please enter policy name!",
    "请输入策略描述": "Please enter policy description",
    "请选择策略": "Please select policy",
    "请选择策略名称": "Please select policy name",
    "请选择策略名称!": "Please select policy name!",
    "域名和IP配置": "Domain & IP Config",
    "站点和风险配置": "Site & Risk Config",
    "弱口令爆破配置": "Weak Password Brute Config",
    "资产组配置": "Asset Group Config",
    "关联资产组": "Related Asset Group",
    "关联策略": "Related Policy",
    "请选择关联策略": "Please select related policy",
    "请选择关联策略!": "Please select related policy!",

    // ---- assets ----
    "资产范围": "Asset Scope",
    "资产范围ID": "Asset Scope ID",
    "资产组名称": "Asset Group Name",
    "资产组范围ID": "Asset Group Scope ID",
    "新建资产分组": "New Asset Group",
    "新建资产分组范围": "New Asset Group Scope",
    "添加资产分组范围": "Add Asset Group Scope",
    "范围": "Scope",
    "请选择资产": "Please select assets",
    "请选择资产!": "Please select assets!",
    "请选择资产组名称!": "Please select asset group name!",
    "请输入资产组名称": "Please enter asset group name",
    "请选择域名": "Please select domain",
    "域名": "Domain",
    "域名：": "Domain:",
    "子域名": "Subdomain",
    "添加子域名": "Add Subdomain",
    "站点": "Site",
    "站点：": "Site:",
    "添加站点": "Add Site",
    "请输入站点!": "Please enter site!",
    "请输入域名!": "Please enter domain!",
    "请输入域名，多个域名请用空格或者换行隔开。": "Please enter domains, separated by spaces or newlines.",
    "记录值": "Record Value",
    "记录类型": "Record Type",
    "解析类型": "Resolution Type",
    "来源": "Source",
    "来源 JS": "Source JS",
    "来源站点": "Source Site",
    "端口": "Port",
    "开放端口": "Open Ports",
    "服务": "Service",
    "服务信息（python）": "Service Info (Python)",
    "服务（python）": "Service (Python)",
    "产品": "Product",
    "主机": "Host",
    "主机名": "Hostname",
    "协议": "Protocol",
    "标头": "Header",
    "状态码": "Status Code",
    "body 长度": "Body Length",
    "应用名": "App Name",
    "应用": "Apply",
    "指 纹": "Fingerprint",
    "指纹统计": "Fingerprint Stats",
    "添加指纹": "Add Fingerprint",
    "上传指纹": "Upload Fingerprint",
    "指纹导出": "Fingerprint Export",
    "指纹数据.json": "fingerprint.json",
    "规则": "Rule",
    "图标": "Icon",
    "截图": "Screenshot",
    "截图详情": "Screenshot Detail",
    "序列号": "Serial Number",
    "主题名称": "Subject Name",
    "签发者名称": "Issuer Name",
    "使用者备用名称": "Subject Alt Name",
    "IP类别": "IP Type",
    "IP类别：": "IP Type:",
    "请选择IP类别": "Please select IP type",
    "请选择IP类别!": "Please select IP type!",
    "请选择IP类型进行搜索": "Please select IP type to search",
    "内网": "Internal",
    "公网": "Public",
    "IP字段": "IP Field",
    "IP端口": "IP Port",
    "IP 端口": "IP Port",
    "IP数": "IP Count",
    "域名数": "Domain Count",
    "站点数量": "Site Count",
    "域名数量": "Domain Count",
    "WIH数量": "WIH Count",
    "关联IP": "Related IP",
    "关联域名": "Related Domain",
    "C段": "C Segment",
    "漏洞名称": "Vulnerability Name",
    "漏洞等级": "Severity",
    "漏洞URL": "Vulnerability URL",
    "验证命令": "Verify Command",
    "模板ID": "Template ID",
    "模版ID": "Template ID",
    "路径": "Path",
    "路径名": "Path Name",
    "仓库": "Repository",
    "仓库名": "Repository",
    "凭证": "Credential",
    "标签": "Tag",
    "添加标签": "Add Tag",
    "请输入标签名称": "Please enter tag name",
    "URL信息": "URL Info",
    "域名批量导出": "Batch Export Domains",
    "IP 批量导出": "Batch Export IPs",
    "站点批量导出": "Batch Export Sites",
    "WIH批量导出": "Batch Export WIH",
    "URL批量导出": "Batch Export URLs",
    "C段 批量导出": "Batch Export C Segments",
    "IP 端口批量导出": "Batch Export IP Ports",
    "导出域名": "Export Domains",
    "导出IP": "Export IPs",

    // ---- asset monitor / scheduler ----
    "资产监控任务": "Asset Monitor Task",
    "资产站点更新": "Asset Site Update",
    "添加站点监控任务": "Add Site Monitor Task",
    "WIH 监控任务": "WIH Monitor Task",
    "添加WIH监控任务": "Add WIH Monitor Task",
    "计划类型": "Schedule Type",
    "定时任务": "Scheduled Task",
    "周期任务": "Periodic Task",
    "定时下发": "Scheduled Dispatch",
    "周期下发": "Periodic Dispatch",
    "添加计划任务": "Add Scheduled Task",
    "cron表达式": "Cron Expression",
    "上次运行时间": "Last Run Time",
    "下次运行时间": "Next Run Time",
    "上一次运行日期": "Last Run Date",
    "下一次运行日期": "Next Run Date",
    "请选择任务类型": "Please select task type",
    "请选择任务类型!": "Please select task type!",
    "请选择日期": "Please select date",
    "请选择时间": "Please select time",

    // ---- backend messages (app/modules error_map) ----
    "Cron 表达式错误": "Invalid cron expression",
    "Fofa 查询结果为空": "Fofa query returned no results",
    "Fofa 认证信息错误": "Fofa authentication error",
    "IP 无效": "Invalid IP",
    "nmap 排除端口错误": "Invalid nmap excluded ports",
    "PoC 任务目标为空": "PoC task target is empty",
    "URL无效": "Invalid URL",
    "不在给定的资产范围中": "Not in the given asset scope",
    "不支持对IP资产组添加站点": "Adding sites to an IP asset group is not supported",
    "不是域名发现任务": "Not a domain discovery task",
    "任务已经完成": "Task already finished",
    "任务目标不在资产组中": "Task target not in asset group",
    "任务目标为空": "Task target is empty",
    "任务目标无效": "Invalid task target",
    "任务类型错误": "Invalid task type",
    "任务资产同步处理中": "Task asset sync in progress",
    "任务运行中": "Task is running",
    "关键字为空": "Keyword is empty",
    "包含在禁止域名内": "Domain is blacklisted",
    "域名不在给定的资产范围中": "Domain not in the given asset scope",
    "域名已经存在指定资产组中": "Domain already exists in the specified asset group",
    "域名无效": "Invalid domain",
    "已存在对应的资产范围": "Corresponding asset scope already exists",
    "弱口令任务选择的策略爆破配置字段不能为空": "Brute config of the selected policy cannot be empty",
    "时间已经过去了": "Time has already passed",
    "时间错误": "Invalid time",
    "未登录": "Not logged in",
    "查询结果为空": "Query returned no results",
    "没有发现可以添加的域名": "No domains found to add",
    "没有找到Celery id": "Celery id not found",
    "没有找到任务": "Task not found",
    "没有找到对应的资产范围": "Asset scope not found",
    "没有找到资产范围ID": "Asset scope ID not found",
    "监控任务时间间隔不能小于6小时（21600s）": "Monitor task interval cannot be less than 6 hours (21600s)",
    "监控任务未找到": "Monitor task not found",
    "监控任务非停止状态": "Monitor task is not stopped",
    "监控任务非运行状态": "Monitor task is not running",
    "目标IP不允许下发": "Target IP is not allowed",
    "站点已在指定资产中": "Site already in the specified asset",
    "站点标签已经存在": "Site tag already exists",
    "站点标签没有找到": "Site tag not found",
    "站点没有找到": "Site not found",
    "策略不存在": "Policy does not exist",
    "策略数据为空": "Policy data is empty",
    "系统异常": "System error",
    "结果集 ID 没有找到": "Result set ID not found",
    "结果集中目标为空": "Result set target is empty",
    "给定资产范围中的域名不存在监控任务": "No monitor task for domains in the given asset scope",
    "给定资产范围中的域名已经存在监控任务": "Monitor task already exists for domains in the given asset scope",
    "自定义端口信息错误": "Invalid custom ports",
    "规则已存在": "Rule already exists",
    "规则无效": "Invalid rule",
    "计划任务没有找到": "Scheduled task not found",
    "计划任务类型错误": "Invalid scheduled task type",
    "资产站点更新任务已存在": "Asset site update task already exists",
    "资产组IP范围无效": "Invalid asset group IP range",
    "连接Fofa API异常": "Failed to connect to Fofa API",
    "非域名类型URL": "URL is not a domain type",
    "风险巡航任务选择的策略PoC配置字段不能为空": "PoC config of the selected policy cannot be empty",
    "时间配置": "Time Config",
    "会对子域名自动下发侦察任务, 获取子域名关联的ip、站点等信息。示例: live.freebuf.com": "Subdomains will automatically be dispatched for recon tasks to gather related IPs, sites, etc. Example: live.freebuf.com",
    "只支持body, title, header, icon_hash 四个字段，仅仅可以使用逻辑或， 如 body=\"Powered by WordPress\"": "Only body, title, header, icon_hash fields are supported, logical OR only, e.g. body=\"Powered by WordPress\"",
    "只支持body, title, header, icon_hash 四个字段，仅仅可以使用逻辑或， 如 body=Powered by WordPress!": "Only body, title, header, icon_hash fields are supported, logical OR only, e.g. body=Powered by WordPress!",
    "只支持body, title, header, icon_hash 四个字段，仅仅可以使用逻辑或， 如 body=": "Only body, title, header, icon_hash fields are supported, logical OR only, e.g. body=",
    "会对站点进行探测, 获取标题、headers, finger等信息。示例: https://www.freebuf.com/": "Sites will be probed to fetch title, headers, fingerprints, etc. Example: https://www.freebuf.com/",
    "请输入域名, 如freebuf.com, live.freebuf.com, 输入多个目标用换行或逗号分隔!": "Please enter domains, e.g. freebuf.com, live.freebuf.com; separate multiple targets with newlines or commas!",
    "请输入域名,如freebuf.com, live.freebuf.com, 输入多个目标用换行或逗号分隔": "Please enter domains, e.g. freebuf.com, live.freebuf.com; separate multiple targets with newlines or commas",
    "请输入确定的目标，不会进行端口扫描,如: http://10.0.1.1:8081/ 10.0.1.1:2222": "Please enter confirmed targets; port scanning will not be performed, e.g.: http://10.0.1.1:8081/ 10.0.1.1:2222",
    "PоC配置": "PoC Config",

    // ---- misc runtime / SVG tooltips ----
    "指纹": "Fingerprint",
    "漏洞PoC": "PoC Vulnerabilities",
    "协议识别": "Protocol Detection",
    "应用弱口令": "App Weak Password",
    "服务弱口令": "Service Weak Password",
    "APISIX 弱口令": "APISIX Weak Password",
    "ActiveMQ 弱口令": "ActiveMQ Weak Password",
    "Actuator API 未授权访问": "Actuator API Unauthorized Access",
    "Actuator API 未授权访问 (绕过WAF)": "Actuator API Unauthorized Access (WAF Bypass)",
    "Actuator httptrace API 未授权访问": "Actuator httptrace API Unauthorized Access",
    "Alibaba Druid 弱口令": "Alibaba Druid Weak Password",
    "Apache solr 未授权访问": "Apache solr Unauthorized Access",
    "Clickhouse 弱口令": "Clickhouse Weak Password",
    "CobaltStrike 弱口令": "CobaltStrike Weak Password",
    "Django 开启调试模式": "Django Debug Mode Enabled",
    "Docker Remote API 未授权访问": "Docker Remote API Unauthorized Access",
    "Druid 未授权访问": "Druid Unauthorized Access",
    "Elasticsearch 未授权访问": "Elasticsearch Unauthorized Access",
    "Exchange 邮件服务器弱口令": "Exchange Mail Server Weak Password",
    "FTP 弱口令": "FTP Weak Password",
    "Gitlab 弱口令": "Gitlab Weak Password",
    "Gitlab 用户名泄漏": "GitLab Username Disclosure",
    "Grafana 弱口令": "Grafana Weak Password",
    "Hadoop YARN RCP 未授权访问漏洞": "Hadoop YARN RPC Unauthorized Access",
    "Harbor 弱口令": "Harbor Weak Password",
    "Headless Remote API 未授权访问": "Headless Remote API Unauthorized Access",
    "IMAP 弱口令": "IMAP Weak Password",
    "Jenkins 弱口令": "Jenkins Weak Password",
    "Kibana 未授权访问": "Kibana Unauthorized Access",
    "ManageIQ 弱口令": "ManageIQ Weak Password",
    "Memcached 未授权访问": "Memcached Unauthorized Access",
    "MongoDB 弱口令": "MongoDB Weak Password",
    "Mongodb 未授权访问": "Mongodb Unauthorized Access",
    "MySQL 弱口令": "MySQL Weak Password",
    "Nacos 弱口令": "Nacos Weak Password",
    "Nacos 未授权访问": "Nacos Unauthorized Access",
    "Nexus Repository 弱口令": "Nexus Repository Weak Password",
    "Onlyoffice 未授权漏洞": "OnlyOffice Unauthorized Access",
    "Openfire 弱口令": "Openfire Weak Password",
    "POP3 弱口令": "POP3 Weak Password",
    "PostgreSQL 弱口令": "PostgreSQL Weak Password",
    "RDP 弱口令": "RDP Weak Password",
    "Redis 弱口令": "Redis Weak Password",
    "Redis 未授权访问": "Redis Unauthorized Access",
    "SMTP 弱口令": "SMTP Weak Password",
    "SQLServer 弱口令": "SQLServer Weak Password",
    "SSH 弱口令": "SSH Weak Password",
    "Shiro CBC 弱密钥": "Shiro CBC Weak Key",
    "Shiro GCM 弱密钥": "Shiro GCM Weak Key",
    "Tomcat 弱口令": "Tomcat Weak Password",
    "Ueditor SSRF 漏洞": "Ueditor SSRF Vulnerability",
    "Ueditor 存储 XSS 漏洞": "Ueditor Stored XSS Vulnerability",
    "WEB-INF/web.xml 文件泄漏": "WEB-INF web.xml File Disclosure",
    "ZooKeeper 未授权访问": "ZooKeeper Unauthorized Access",
    "apollo-adminservice 未授权访问": "apollo-adminservice Unauthorized Access",
    "发现 Adminer.php": "Adminer.php Detected",
    "发现 Any800全渠道智能客服云平台": "Any800 Omnichannel Service Platform Detected",
    "发现 Apache Apereo Cas": "Apache Apereo CAS Detected",
    "发现 Apache Ofbiz": "Apache Ofbiz Detected",
    "发现 Apache Shiro": "Apache Shiro Detected",
    "发现 Clickhouse REST API": "ClickHouse REST API Detected",
    "发现 Grafana": "Grafana Detected",
    "发现 Graphql 接口": "GraphQL Endpoint Detected",
    "发现 Harbor API": "Harbor API Detected",
    "发现 Hystrix Dashboard": "Hystrix Dashboard Detected",
    "发现 Nacos": "Nacos Detected",
    "发现 Oracle Weblogic 控制台": "Oracle WebLogic Console Detected",
    "发现 Swagger 文档接口": "Swagger API Documentation Detected",
    "发现 xxl-job-admin": "xxl-job-admin Detected",
    "发现VMware vCenter": "VMware vCenter Detected",
    "发现帆软 FineReport": "FanRuan FineReport Detected",
    "发现帆软 FineReport V10": "FanRuan FineReport V10 Detected",
    "发现泛微 Ecology": "Weaver Ecology Detected",
    "导出站点": "Export Sites",
    "无效": "Invalid",
    "入口": "Entry",
    "logo收起": "Collapse sidebar",
    "logo 登录": "Login logo",
    "资产侦察": "Asset Recon",

    // ---- PoC vulnerability names (DB-driven; pattern rules below cover the rest) ----
    "Django 开启调试模式": "Django Debug Mode Enabled",
    "Gitlab 用户名泄漏": "Gitlab Username Leak",
    "WEB-INF/web.xml 文件泄漏": "WEB-INF/web.xml File Leak",
    "Ueditor SSRF 漏洞": "Ueditor SSRF Vulnerability",
    "Ueditor 存储 XSS 漏洞": "Ueditor Stored XSS Vulnerability",
    "Exchange 邮件服务器弱口令": "Exchange Mail Server Weak Password",
    "Actuator API 未授权访问 (绕过WAF)": "Actuator API Unauthorized Access (WAF Bypass)",
    "发现 Any800全渠道智能客服云平台": "Detected: Any800 Omnichannel Customer Service Cloud",
    "发现 Graphql 接口": "Detected: Graphql Interface",
    "发现 Swagger 文档接口": "Detected: Swagger Doc Interface",
    "发现 Oracle Weblogic 控制台": "Detected: Oracle Weblogic Console",
    "发现帆软 FineReport": "Detected: Fanruan FineReport",
    "发现帆软 FineReport V10": "Detected: Fanruan FineReport V10",
    "发现泛微 Ecology": "Detected: Weaver Ecology"
  };

  // Pattern rules for dynamically composed strings (numbers, joined labels,
  // DB-driven PoC names). $1..$n refer to capture groups; each group is
  // translated recursively, falling back to the raw text.
  var RULES = [
    [/^图标[:：]\s*(.+)$/, "Icon: $1"],
    [/^目标：(\d+)，\s*PoC：(\d+)$/, "Targets: $1, PoC: $2"],
    [/^共\s*(\d+)\s*页\s*\/\s*(\d+)\s*条数据$/, "Total $2 records, $1 page(s)"],
    [/^(\d+)\s*条\/页$/, "$1 / page"],
    [/^请输入(.+?)进行搜索$/, "Enter $1 to search"],
    [/^请选择(.+?)进行搜索$/, "Select $1 to search"],
    [/^(.+?)\s*弱口令$/, "$1 Weak Password"],
    [/^(.+?)\s*未授权访问(漏洞)?$/, "$1 Unauthorized Access"],
    [/^(.+?)\s*未授权漏洞$/, "$1 Unauthorized Access"],
    [/^(.+?)\s*弱密钥$/, "$1 Weak Key"],
    [/^系统异常[:：]?\s*([\s\S]*)$/, "System error: $1"],
    [/^(.*?\S)\s*无效的目标$/, "$1 invalid target"],
    [/^发现\s*(.+)$/, "Detected: $1"],
    [/^(?=.*?[一-鿿])(.+?) - (\d+)$/, "$1 - $2"],
    [/^(.*\S)\s*相关资产$/, "$1 - Related Assets"],
    [/^(?=.*?[一-鿿])(.+?)[:：]\s*(\d+)$/, "$1: $2"],
    [/^(?=.*?[一-鿿])(.+?)[:：]$/, "$1:"]
  ];

  function lookup(s) {
    return Object.prototype.hasOwnProperty.call(DICT, s) ? DICT[s] : null;
  }

  function translateCore(text) {
    var direct = lookup(text);
    if (direct !== null) {
      return direct;
    }
    // antd inserts a space between the two characters of a button label
    var collapsed = text.replace(/([一-鿿])\s+([一-鿿])/g, "$1$2");
    if (collapsed !== text) {
      var c = lookup(collapsed);
      if (c !== null) {
        return c;
      }
    }
    // comma-joined lists of known items (config item summaries etc.)
    if (text.indexOf(",") !== -1 || text.indexOf("，") !== -1) {
      var parts = text.split(/[,，]/);
      if (parts.length > 1) {
        var out = [];
        for (var i = 0; i < parts.length; i++) {
          var p = lookup(parts[i].trim());
          if (p === null) {
            out = null;
            break;
          }
          out.push(p);
        }
        if (out) {
          return out.join(", ");
        }
      }
    }
    for (var r = 0; r < RULES.length; r++) {
      var m = text.match(RULES[r][0]);
      if (!m) {
        continue;
      }
      var res = RULES[r][1];
      for (var g = 1; g < m.length; g++) {
        if (m[g] === undefined) {
          continue;
        }
        var tv = translateCore(m[g]);
        res = res.split("$" + g).join(tv === null ? m[g] : tv);
      }
      return res;
    }
    return null;
  }

  function translateText(text) {
    if (!text || !/[一-鿿]/.test(text)) {
      return text;
    }
    var direct = lookup(text);
    if (direct !== null) {
      return direct;
    }
    var m = text.match(/^(\s*)([\s\S]*?)(\s*)$/);
    if (!m[2]) {
      return text;
    }
    var t = translateCore(m[2]);
    return t === null ? text : m[1] + t + m[3];
  }

  function getLang() {
    return "en";
  }

  var ATTRS = ["placeholder", "title", "aria-label", "alt"];

  function inLangSwitch(node) {
    var n = node.nodeType === 1 ? node : node.parentNode;
    while (n) {
      if (n.id === "harrier-lang-switch") {
        return true;
      }
      n = n.parentNode;
    }
    return false;
  }

  function translateElementAttrs(el) {
    for (var i = 0; i < ATTRS.length; i++) {
      var attr = ATTRS[i];
      if (el.hasAttribute && el.hasAttribute(attr)) {
        var v = el.getAttribute(attr);
        var t = translateText(v);
        if (t !== v) {
          el.setAttribute(attr, t);
        }
      }
    }
  }

  function translateTree(root) {
    if (!root || inLangSwitch(root)) {
      return;
    }
    if (root.nodeType === 3) {
      var t = translateText(root.nodeValue);
      if (t !== root.nodeValue) {
        root.nodeValue = t;
      }
      return;
    }
    if (root.nodeType !== 1) {
      return;
    }
    if (/^(SCRIPT|STYLE|NOSCRIPT|TEXTAREA)$/.test(root.tagName)) {
      return;
    }
    translateElementAttrs(root);
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.nodeValue || !/[一-鿿]/.test(node.nodeValue)) {
          return NodeFilter.FILTER_REJECT;
        }
        var parent = node.parentNode;
        if (parent && /^(SCRIPT|STYLE|NOSCRIPT|TEXTAREA)$/.test(parent.tagName)) {
          return NodeFilter.FILTER_REJECT;
        }
        if (inLangSwitch(node)) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var node;
    var nodes = [];
    while ((node = walker.nextNode())) {
      nodes.push(node);
    }
    for (var i = 0; i < nodes.length; i++) {
      var v = nodes[i].nodeValue;
      var translated = translateText(v);
      if (translated !== v) {
        nodes[i].nodeValue = translated;
      }
    }
    var els = root.querySelectorAll ? root.querySelectorAll("[placeholder],[title],[aria-label],[alt]") : [];
    for (var j = 0; j < els.length; j++) {
      if (!inLangSwitch(els[j])) {
        translateElementAttrs(els[j]);
      }
    }
  }

  function translateTitle() {
    if (!document.title) {
      return;
    }
    var next = translateText(document.title);
    if (next !== document.title) {
      document.title = next;
    }
  }

  var started = false;

  var revealed = false;

  function reveal() {
    if (revealed) {
      return;
    }
    revealed = true;
    if (document.body) {
      document.body.style.opacity = "1";
    }
  }

  function start() {
    if (started) {
      return;
    }
    started = true;
    translateTitle();
    translateTree(document.documentElement);
    // initial pass done; reveal shortly after Vue's first render settles
    setTimeout(reveal, 700);
    setTimeout(reveal, 2500);  // failsafe

    // Batch mutations and process them on a short timer: Vue re-renders
    // produce large mutation bursts (polling tables, dropdowns), and
    // translating per-mutation would walk the same subtrees many times.
    var pending = [];
    var scheduled = false;

    function flush() {
      scheduled = false;
      var batch = pending;
      pending = [];
      for (var i = 0; i < batch.length; i++) {
        translateTree(batch[i]);
      }
      translateTitle();
      buildHint();
    }

    var observer = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var m = mutations[i];
        if (m.type === "characterData") {
          pending.push(m.target);
        } else {
          for (var j = 0; j < m.addedNodes.length; j++) {
            pending.push(m.addedNodes[j]);
          }
          if (m.type === "attributes" && m.target) {
            pending.push(m.target);
          }
        }
      }
      if (pending.length && !scheduled) {
        scheduled = true;
        setTimeout(flush, 50);
      }
    });
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ATTRS
    });
  }

  // ---- per-page explanation hints (dismissible, per session) ----
  var HINTS = [
    {
      match: "/taskList",
      en: "Quick Scan (the button on this page) is recon only: ports, sites, fingerprints, nuclei templates. For vulnerability verification (PoC) and weak-password testing, go to Policy Config and click \"Policy Scan\" on a policy (e.g. Full)."
    },
    {
      match: "/policy",
      en: "Policy Scan runs the full pipeline: port scan → site discovery → nuclei → PoC vulnerability checks → weak-password brute force. Task type \"task\" scans ports first (recommended); \"risk_cruising\" only checks the sites you enter — no port scan, so services on other ports are never tested. Your all-in-one policy is named Full."
    }
  ];

  function currentHint() {
    var h = location.hash || "";
    for (var i = 0; i < HINTS.length; i++) {
      if (h.indexOf(HINTS[i].match) !== -1) {
        return HINTS[i];
      }
    }
    return null;
  }

  function buildHint() {
    var hint = currentHint();
    var existing = document.getElementById("harrier-page-hint");
    if (!hint) {
      if (existing) {
        existing.parentNode.removeChild(existing);
      }
      return;
    }
    if (existing && existing.getAttribute("data-key") === hint.match) {
      return;
    }
    if (existing) {
      existing.parentNode.removeChild(existing);
    }
    try {
      if (sessionStorage.getItem("harrier-hint-closed-" + hint.match)) {
        return;
      }
    } catch (e) {}
    var box = document.createElement("div");
    box.id = "harrier-page-hint";
    box.setAttribute("data-key", hint.match);
    box.style.cssText = "position:fixed;top:64px;right:16px;z-index:99999;max-width:420px;" +
      "background:#e6f7ff;border:1px solid #91d5ff;border-radius:4px;padding:8px 28px 8px 12px;" +
      "font-size:12px;line-height:1.5;font-family:sans-serif;color:#0050b3;" +
      "box-shadow:0 2px 8px rgba(0,0,0,.12);";
    box.textContent = hint.en;
    var close = document.createElement("span");
    close.textContent = "×";
    close.style.cssText = "position:absolute;top:4px;right:8px;cursor:pointer;font-size:14px;color:#1890ff;";
    close.onclick = function () {
      try {
        sessionStorage.setItem("harrier-hint-closed-" + hint.match, "1");
      } catch (e) {}
      box.parentNode.removeChild(box);
    };
    box.appendChild(close);
    document.body.appendChild(box);
  }

  function boot() {
    buildHint();
    window.addEventListener("hashchange", buildHint);
    start();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
